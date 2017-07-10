#!/usr/bin/env python
# -*- coding:utf-8 -*-
import imghdr

from bs4 import BeautifulSoup
from base import BaseFeedBook, URLOpener

def getBook():
    return MyHero

class MyHero(BaseFeedBook):
    title               = u'我的英雄学院'
    description         = u'日本漫画家堀越耕平创作的少年漫画'
    language            = 'zh-tw'
    feed_encoding       = "big5"
    page_encoding       = "big5"
    mastheadfile        = "mh_comic.gif"
    coverfile           = 'cv_myhero.jpg'

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
        mainurl = "http://www.cartoonmad.com/comic/4085.html"
        title = '我的英雄学院'.decode("utf8")
        
        href = self.GetNewComic(title, mainurl)
        if href == "":
            return []

        return self.GetComicUrls(title, href)
