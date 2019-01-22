#!/usr/bin/env python3
# encoding: utf-8
#http://www.gufengmh.com或者http://m.gufengmh.com网站的免费漫画的基类，简单提供几个信息实现一个子类即可推送特定的漫画
#Author: insert0003 <https://github.com/insert0003>
import re, json
from lib.urlopener import URLOpener
from lib.autodecoder import AutoDecoder
from books.base import BaseComicBook
from bs4 import BeautifulSoup
import urllib, urllib2, imghdr
from base64 import b64decode, b64encode

class GuFengBaseBook(BaseComicBook):
    title               = u''
    description         = u''
    language            = ''
    feed_encoding       = ''
    page_encoding       = ''
    mastheadfile        = ''
    coverfile           = ''
    host                = 'http://m.gufengmh.com'
    feeds               = [] #子类填充此列表[('name', mainurl),...]

    #获取漫画章节列表
    def getChapterList(self, url):
        decoder = AutoDecoder(isfeed=False)
        opener = URLOpener(self.host, timeout=60)
        chapterList = []

        if url.startswith( "http://www.gufengmh.com" ):
            url = url.replace('http://www.gufengmh.com', 'http://m.gufengmh.com')

        result = opener.open(url)
        if result.status_code != 200 or not result.content:
            self.log.warn('fetch comic page failed: %s' % url)
            return chapterList

        content = self.AutoDecodeContent(result.content, decoder, self.feed_encoding, opener.realurl, result.headers)

        soup = BeautifulSoup(content, 'html.parser')
        #<ul class="Drama autoHeight" data-sort="asc" id="chapter-list-1">
        soup = soup.find('ul', {"class":"Drama autoHeight", "id":"chapter-list-1"})
        if (soup is None):
            self.log.warn('chapter-list is not exist.')
            return chapterList

        lias = soup.findAll('a')
        if (lias is None):
            self.log.warn('chapterList href is not exist.')
            return chapterList

        for li in lias:
            href = "http://m.gufengmh.com" + li.get("href")
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

        content = self.AutoDecodeContent(result.content, decoder, self.feed_encoding, opener.realurl, result.headers)

        #var chapterPath = "images/comic/31/61188/";
        chapterPath = re.search(r'(var chapterPath = ")(.*)(";var chapterPrice)', content)
        if (chapterPath is None):
            self.log.warn('var chapterPath is not exist.')
            return imgList
        else:
            chapterPath = chapterPath.group(2)

        #var pageImage = "http://res.gufengmh.com/images/";
        imgPrefix = re.search(r'(var pageImage = ")(.*)(/images/)', content)
        if (imgPrefix is None):
            self.log.warn('var chapterImages is not exist.')
            return imgList
        else:
            imgPrefix = imgPrefix.group(2)+"/"

        #var chapterImages = ["",""];
        images = re.search(r'(var chapterImages = \[)(.*)(\];)', content)
        if (images is None):
            self.log.warn('var chapterImages is not exist.')
            return imgList
        else:
            images = images.group(2).split(',')

        for img in images:
            img_url = imgPrefix + chapterPath + img.replace("\"","")
            print img_url
            imgList.append(img_url)

        return imgList
