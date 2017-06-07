#!/usr/bin/env python
# -*- coding:utf-8 -*-
import imghdr

from bs4 import BeautifulSoup
from base import BaseFeedBook, URLOpener
from apps.dbModels import UpdateLog

def getBook():
    return Onepiece

class Onepiece(BaseFeedBook):
    title               = u'海贼王'
    description         = u'日本漫画家尾田荣一郎创作的少年漫画'
    language            = 'zh-tw'
    feed_encoding       = "big5"
    page_encoding       = "big5"
    mastheadfile        = "mh_comic.gif"
    coverfile           = 'cv_onepiece.jpg'

    def updatelog(self, name, count):
        try:
            mylogs = UpdateLog.all().filter("comicname = ", name)
            for log in mylogs:
                log.delete()
            dl = UpdateLog(comicname=name, updatecount=count)
            dl.put()
        except Exception as e:
            print('UpdateLog failed to save:%s',str(e))

    def Items(self, opts=None, user=None):
        """
        生成器，返回一个图片元组，mime,url,filename,content,brief,thumbnail
        """
        urls = self.ParseFeedUrls()
        opener = URLOpener(self.host, timeout=self.timeout, headers=self.extra_header)
        for section, ftitle, url, desc in urls:
            opener = URLOpener(self.host, timeout=self.timeout, headers=self.extra_header)
            result = opener.open(url)
            article = result.content 
            if not article:
                continue
           
            imgtype = imghdr.what(None, article)
            imgmime = r"image/" + imgtype
            fnimg = "img%d.%s" % (self.imgindex, 'jpg' if imgtype=='jpeg' else imgtype)
            yield (imgmime, url, fnimg, article, None, None)
           
            tmphtml = '<html><head><title>Picture</title></head><body><img src="%s" /></body></html>' % fnimg
            yield (section, url, ftitle, tmphtml, '', None)

    def ParseFeedUrls(self):
        mainurl = "http://www.cartoonmad.com/comic/1152.html"
        href = ""
        this_count = 0
        urls = []
        for retryCount in range(0,5):
            opener = URLOpener(self.host, timeout=60)
            result = opener.open(mainurl)
            if result.status_code != 200:
                continue
            else:
                retryCount = 6
                break
        if retryCount != 6:
            self.log.warn('fetch rss failed:%s' % mainurl)
            return []

        content = result.content.decode(self.feed_encoding, 'ignore')

        title = '海贼王'.decode("utf")
        soup = BeautifulSoup(content, "lxml")
        mhlog = UpdateLog.all().filter("comicname = ", title).get()
        updatecount = mhlog.updatecount
        
        mhs = soup.findAll("table", {"width": '688'})
        for mh in mhs:
            comics = mh.findAll("a", {"target": '_blank'})
            for comic in comics:
                num = int(comic.text.split(" ")[1])
                if num > updatecount :
                    this_count = num
                    href = "http://www.cartoonmad.com" + comic.get("href")
                    print this_count
                    print href

        if href != "":
            comic_opener = URLOpener(self.host, timeout=60)
            comic_page = comic_opener.open(href)
            if comic_page.status_code != 200:
                self.log.warn('fetch rss failed:%s' % mainurl)
                return []

            comic_content = comic_page.content.decode(self.feed_encoding)
            comic_body = BeautifulSoup(comic_content, "lxml")
            ul = comic_body.find("select").findAll("option")
            if ul is None :
                return[]
            else:
                for mh in ul:
                    mhhref = mh.get("value")
                    if mhhref:
                        pagehref = "http://www.cartoonmad.com/comic/" + mhhref
                        pageopener = URLOpener(self.host, timeout=60)
                        pageresult = pageopener.open(pagehref)
                        if pageresult.status_code != 200:
                            self.log.warn('fetch rss failed:%s' % mainurl)
                            return []
                        body = pageresult.content.decode(self.feed_encoding)
                        sp = BeautifulSoup(body, "lxml")
                        mhpic = sp.find("img", {"oncontextmenu": 'return false'}).get("src")
                        print mhpic
                        urls.append( (title, mh.text, mhpic, None))
            self.updatelog(title, this_count)
        return urls
