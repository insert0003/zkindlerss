#!/usr/bin/env python
# -*- coding:utf-8 -*-
import imghdr

from bs4 import BeautifulSoup
from base import BaseFeedBook, URLOpener

def getBook():
    return Onepiece

class Onepiece(BaseFeedBook):
    title               = u'東京食屍鬼RE'
    description         = u'石田スイ'
    language            = 'zh-tw'
    feed_encoding       = "big5"
    page_encoding       = "big5"
    mastheadfile        = "mh_comic.gif"
    coverfile           = 'cv_tokyo.jpg'

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
        mainurl = "http://www.cartoonmad.com"
        urls = []
        opener = URLOpener(self.host, timeout=60)
        result = opener.open(mainurl)
        if result.status_code != 200:
            self.log.warn('fetch rss failed:%s' % mainurl)
            return []
        content = result.content.decode(self.feed_encoding)

        comic_name = '東京食屍鬼'.decode("utf8")
        title = '東京食屍鬼'.decode("utf8")
        soup = BeautifulSoup(content, "lxml")
        mhnew = soup.findAll("div", {"style": 'overflow:hidden;'})
        
        for obj in mhnew:
            name = obj.find("a").text
            if ( name[0:len(comic_name)] == comic_name ):
                href = "http://www.cartoonmad.com" + obj.find("a").get("href")
                print href
                comic_opener = URLOpener(self.host, timeout=60)
                comic_page = comic_opener.open(href)
                if comic_page.status_code != 200:
                    self.log.warn('fetch rss failed:%s' % mainurl)
                    return []

                comic_content = comic_page.content.decode(self.feed_encoding)
                comic_body = BeautifulSoup(comic_content, "lxml")
                ul = comic_body.find("select").findAll("option")
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
        return urls
