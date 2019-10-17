#!/usr/bin/env python3
# encoding: utf-8
#https://www.733.so或者https://m.733.so网站的免费漫画的基类，简单提供几个信息实现一个子类即可推送特定的漫画
#Author: insert0003 <https://github.com/insert0003>
import re, json, urlparse, time
from lib.urlopener import URLOpener
from lib.autodecoder import AutoDecoder
from books.base import BaseComicBook
from bs4 import BeautifulSoup
import urllib, urllib2, imghdr
from base64 import b64decode, b64encode

class Seven33SoBaseBook(BaseComicBook):
    title               = u''
    description         = u''
    language            = ''
    feed_encoding       = ''
    page_encoding       = ''
    mastheadfile        = ''
    coverfile           = ''
    host                = 'https://m.733.so'
    feeds               = [] #子类填充此列表[('name', mainurl),...]

    #获取漫画章节列表
    def getChapterList(self, url):
        decoder = AutoDecoder(isfeed=False)
        opener = URLOpener(self.host, timeout=60)
        chapterList = []

        if url.startswith( "https://www.733.so" ):
            url = url.replace('https://www.733.so', 'https://m.733.so')

        result = opener.open(url)
        if result.status_code != 200 or not result.content:
            self.log.warn('fetch comic page failed: %s' % url)
            return chapterList

        content = self.AutoDecodeContent(result.content, decoder, self.feed_encoding, opener.realurl, result.headers)

        soup = BeautifulSoup(content, 'html.parser')
        lias = soup.select("html > body > div.Introduct > div#list > ul#mh-chapter-list-ol-0 > li > a")

        if (soup is None):
            self.log.warn('chapter-list is not exist.')
            return chapterList

        for aindex in range(len(lias)):
            rindex = len(lias)-1-aindex
            href = "https://m.733.so" + lias[rindex].get("href")
            chapterList.append(href)

        return chapterList

    #获取漫画图片列表
    def getImgList(self, url):
        decoder = AutoDecoder(isfeed=False)
        opener = URLOpener(self.host, timeout=60)
        imgList = []

        result = opener.open(url)
        if result.status_code != 200 or not result.content:
            self.log.warn('fetch comic page failed: %s' % url)
            return imgList

        urlpaths = urlparse.urlsplit(url.lower()).path.split("/")
        if ( (u"mh" in urlpaths) and (urlpaths.index(u"mh")+2 < len(urlpaths)) ):
            tid = str(time.time()).replace(".", "1")
            if len(tid) == 12:
                tid = tid + "1"
            cid = urlpaths[urlpaths.index(u"mh")+1]
            pid = urlpaths[urlpaths.index(u"mh")+2].replace(".html", "")
        else:
            self.log.warn('Can not get cid and pid from URL: {}.'.format(url))
            return imgList

        content = self.AutoDecodeContent(result.content, decoder, self.feed_encoding, opener.realurl, result.headers)

        res = re.search(r'var qTcms_S_m_murl_e=".*";', content).group()
        if (res is None):
            self.log.warn('var qTcms_S_m_murl_e is not exist.')
            return imgList

        list_encoded = res.split('\"')[1]
        lz_decoded = b64decode(list_encoded)
        images = lz_decoded.split("$qingtiandy$")

        if (images is None):
            self.log.warn('image list is not exist.')
            return imgList

        for img in images:
            if "https://res.gufengmh8.com/" in img:
                img_url = img
            elif "http://res.img.pufei.net" in img:
                img_url = img
            else:
                if "http://www.baidu1.com/" in img:
                    # http://www.baidu1.com/2016/06/28/21/042f051bea.jpg
                    # http://img_733.234us.com/newfile.php?data=MjAxNi8wNi8yOC8yMS8wNDJmMDUxYmVhLmpwZ3wxNTQ4OTgzNDA0ODkwfDI2Nzk4fDMwOTYzNnxt
                    b64str = img.replace("http://www.baidu1.com/", "") + '|{}|{}|{}|m'.format(tid, cid, pid)
                elif "http://ac.tc.qq.com/" in img:
                    b64str = img + '|{}|{}|{}|m'.format(tid, cid, pid)
                elif "http://res.gufengmh.com/" in img:
                    # http://res.gufengmh.com/images/comic/393/785728/1548900050B4iX-yPTclWGhKd1.jpg
                    # http://img_733.234us.com/newfile.php?data=aHR0cDovL3Jlcy5ndWZlbmdtaC5jb20vaW1hZ2VzL2NvbWljLzM5My83ODU3MjgvMTU0ODkwMDA1MEI0aVgteVBUY2xXR2hLZDEuanBnfDE1NDg5ODQwNTE0Nzh8MjY3OTh8NTgzMDI2fG0=
                    b64str = img + '|{}|{}|{}|m'.format(tid, cid, pid)
                else:
                    self.log.warn('Ths image herf is: %s' % img)
                    b64str = img + '|{}|{}|{}|m'.format(tid, cid, pid)

                imgb64 = b64encode(b64str)
                requestImg = 'http://img_733.234us.com/newfile.php?data={}'.format(imgb64)
                img_url = self.getImgUrl(requestImg)

            if not img_url:
                self.log.warn("can not get real url for : %s." % requestImg)
            else:
                imgList.append(img_url)

        return imgList

    #获取漫画图片格式
    def getImgUrl(self, url):
        opener = URLOpener(self.host, timeout=60)
        headers = {
            'Host': "img_733.234us.com",
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'}
        result = opener.open(url, headers=headers)
        if result.status_code != 200 or opener.realurl == url:
            self.log.warn('can not get real comic url for : %s' % url)
            return None

        return opener.realurl