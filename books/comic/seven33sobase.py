#!/usr/bin/env python3
# encoding: utf-8
# http://www.733mh.com或者http://m.733mh.com网站的免费漫画的基类，简单提供几个信息实现一个子类即可推送特定的漫画
# Author: insert0003 <https://github.com/insert0003>
import re
from lib.urlopener import URLOpener
from lib.autodecoder import AutoDecoder
from books.base import BaseComicBook
from bs4 import BeautifulSoup

class Seven33SoBaseBook(BaseComicBook):
    accept_domains = ("http://www.733mh.com", "http://m.733mh.com")
    host = "http://www.733mh.com"

    # 获取漫画章节列表
    def getChapterList(self, url):
        decoder = AutoDecoder(isfeed=False)
        opener = URLOpener(self.host, timeout=60)
        chapterList = []

        if url.startswith( "http://www.733mh.com" ):
            url = url.replace('http://www.733mh.com', 'http://m.733mh.com')

        result = opener.open(url)
        if result.status_code != 200 or not result.content:
            self.log.warn('fetch comic page failed: %s' % url)
            return chapterList

        content = self.AutoDecodeContent(result.content, decoder, self.feed_encoding, opener.realurl, result.headers)

        soup = BeautifulSoup(content, 'html.parser')
        # <div class="chapter-list" id="chapterList">
        soup = soup.find('div', {"class":"chapter-list", "id":"chapterList"})
        if (soup is None):
            self.log.warn('chapter-list is not exist.')
            return chapterList

        lias = soup.findAll('a')
        if (lias is None):
            self.log.warn('chapter-list is not exist.')
            return chapterList

        for aindex in range(len(lias)):
            rindex = len(lias)-1-aindex
            href = "http://m.733mh.com" + lias[rindex].get('href', '')
            chapterList.append((lias[rindex].get_text(), href))

        return chapterList

    # 获取漫画图片列表
    def getImgList(self, url):
        decoder = AutoDecoder(isfeed=False)
        opener = URLOpener(self.host, timeout=60)
        imgList = []

        result = opener.open(url)
        if result.status_code != 200 or not result.content:
            self.log.warn('fetch comic page failed: %s' % url)
            return imgList

        content = self.AutoDecodeContent(result.content, decoder, self.feed_encoding, opener.realurl, result.headers)

        res = re.search(r'photosr(.*)";', content).group()
        if (res is None):
            self.log.warn(content)
            self.log.warn('var qTcms_S_m_murl_e is not exist.')
            return imgList

        images = res.split(";")
        for ori in images:
            if ori != "":
                img = re.search(r'\"(.*)\"', ori).group(1)
                img_url = "http://tutu.gugumanhuawang.com/{}".format(img)
                imgList.append(img_url)
        return imgList
