#!/usr/bin/env python
# -*- coding:utf-8 -*-
#http://www.cartoonmad.com网站的漫画的基类，简单提供几个信息实现一个子类即可推送特定的漫画
#Author: insert0003 <https://github.com/insert0003>
import datetime
from bs4 import BeautifulSoup
from config import TIMEZONE
from lib.urlopener import URLOpener
from lib.autodecoder import AutoDecoder
from books.base import BaseComicBook
from apps.dbModels import LastDelivered

import imghdr, urllib2

class CartoonMadBaseBook(BaseComicBook):
    title               = u''
    description         = u''
    language            = ''
    feed_encoding       = ''
    page_encoding       = ''
    mastheadfile        = ''
    coverfile           = ''
    host                = 'http://www.cartoonmad.com'
    feeds               = [] #子类填充此列表[('name', mainurl),...]
    
    #使用此函数返回漫画图片列表[(section, title, url, desc),...]
    def ParseFeedUrls(self):
        urls = [] #用于返回
        newComicUrls = self.GetNewComic() #返回[(title, num, url),...]
        if not newComicUrls:
            return []
        
        decoder = AutoDecoder(isfeed=False)
        for title, num, url in newComicUrls:
            if url.startswith( "http://" ):
                url = url.replace('http://', 'https://')

            opener = URLOpener(self.host, timeout=60)
            result = opener.open(url)
            if result.status_code != 200 or not result.content:
                self.log.warn('fetch comic page failed: %s' % url)
                continue
                
            content = result.content
            content = self.AutoDecodeContent(content, decoder, self.page_encoding, opener.realurl, result.headers)
            
            bodySoup = BeautifulSoup(content, 'lxml')
            sel = bodySoup.find('select') #页码行，要提取所有的页面
            ul = sel.find_all('option') if sel else None
            if not ul:
                continue

            for comicPage in ul:
                href = comicPage.get('value')
                if href:
                    pageHref = self.urljoin(url, href)
                    result = opener.open(pageHref)
                    if result.status_code != 200:
                        self.log.warn('fetch comic page failed: %s' % pageHref)
                        continue
                        
                    content = result.content
                    content = self.AutoDecodeContent(content, decoder, self.page_encoding, opener.realurl, result.headers)
                    soup = BeautifulSoup(content, 'lxml')
                    
                    comicImgTag = soup.find('img', {'oncontextmenu': 'return false'})
                    comicSrc = comicImgTag.get('src') if comicImgTag else None
                    if comicSrc:
                        urls.append((title, comicPage.text, comicSrc, None))
                        self.log.warn('comicSrc: %s' % comicSrc)

            self.UpdateLastDelivered(title, num)
            
        return urls

    #生成器，返回一个图片元组，mime,url,filename,content,brief,thumbnail
    def Items(self):
        urls = self.ParseFeedUrls()
        opener = URLOpener(self.host, timeout=self.timeout, headers=self.extra_header)
        decoder = AutoDecoder(isfeed=False)
        prevSection = ''
        min_width, min_height = self.min_image_size if self.min_image_size else (0, 0)
        htmlTemplate = '<html><head><meta http-equiv="Content-Type" content="text/html;charset=utf-8"><title>%s</title></head><body><img src="%s"/></body></html>'

        for section, fTitle, url, desc in urls:
            # if section != prevSection or prevSection == '':
            #         decoder.encoding = '' #每个小节都重新检测编码[当然是在抓取的是网页的情况下才需要]
            #         prevSection = section
            #         opener = URLOpener(self.host, timeout=self.timeout, headers=self.extra_header)
            #         if self.needs_subscription:
            #             result = self.login(opener, decoder)

            # result = opener.open(url)
            # content = result.content
            content = urllib2.urlopen(url).read()
            if not content:
                continue

            imgFilenameList = []

            #先判断是否是图片
            imgType = imghdr.what(None, content)
            if imgType:
                content = self.process_image_comic(content)
                if content:
                    if isinstance(content, (list, tuple)): #一个图片分隔为多个图片
                        imgIndex = self.imgindex
                        for idx, imgPartContent in enumerate(content):
                            imgType = imghdr.what(None, imgPartContent)
                            imgMime = r"image/" + imgType
                            fnImg = "img%d_%d.jpg" % (imgIndex, idx)
                            imgPartUrl = url[:-4]+"_%d.jpg"%idx
                            imgFilenameList.append(fnImg)
                            yield (imgMime, imgPartUrl, fnImg, imgPartContent, None, True)
                    else: #单个图片
                        imgType = imghdr.what(None, content)
                        imgMime = r"image/" + imgType
                        fnImg = "img%d.%s" % (self.imgindex, 'jpg' if imgType=='jpeg' else imgType)
                        imgFilenameList.append(fnImg)
                        yield (imgMime, url, fnImg, content, None, None)

            #每个图片当做一篇文章，否则全屏模式下图片会挤到同一页
            for imgFilename in imgFilenameList:
                tmpHtml = htmlTemplate % (fTitle, imgFilename)
                yield (imgFilename.split('.')[0], url, fTitle, tmpHtml, '', None)

    #根据已经保存的记录查看连载是否有新的章节，返回章节URL列表
    #返回：[(title, num, url),...]
    def GetNewComic(self):
        urls = []

        if not self.feeds:
            return []
        
        userName = self.UserName()
        decoder = AutoDecoder(isfeed=False)
        for item in self.feeds:
            title, url = item[0], item[1]
            if url.startswith( "http://" ):
                url = url.replace('http://', 'https://')
            
            lastCount = LastDelivered.all().filter('username = ', userName).filter("bookname = ", title).get()
            if not lastCount:
                default_log.info('These is no log in db LastDelivered for name: %s, set to 0' % title)
                oldNum = 0
            else:
                oldNum = lastCount.num
                
            opener = URLOpener(self.host, timeout=60)
            result = opener.open(url)
            if result.status_code != 200:
                self.log.warn('fetch index page for %s failed[%s] : %s' % (title, URLOpener.CodeMap(result.status_code), url))
                continue
            content = result.content
            content = self.AutoDecodeContent(content, decoder, self.feed_encoding, opener.realurl, result.headers)
            
            soup = BeautifulSoup(content, 'lxml')
            
            allComicTable = soup.find_all('table', {'width': '800', 'align': 'center'})
            addedForThisComic = False
            for comicTable in allComicTable:
                comicVolumes = comicTable.find_all('a', {'target': '_blank'})
                for volume in comicVolumes:
                    texts = volume.text.split(' ')
                    if len(texts) > 2 and texts[1].isdigit() and volume.get('href'):
                        num = int(texts[1])
                        if num > oldNum:
                            self.log.warn('volume: %s' % volume)
                            oldNum = num
                            href = self.urljoin(self.host, volume.get('href'))
                            urls.append((title, num, href))
                            addedForThisComic = True
                            break #一次只推送一卷（有时候一卷已经很多图片了）
                            
                if addedForThisComic:
                    break
                    
        return urls

