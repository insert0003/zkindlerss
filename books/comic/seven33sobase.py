#!/usr/bin/env python3
# encoding: utf-8
# http://www.733mh.com或者http://m.733mh.com网站的免费漫画的基类，简单提供几个信息实现一个子类即可推送特定的漫画
# Author: insert0003 <https://github.com/insert0003>
import re
from lib.urlopener import URLOpener
from lib.autodecoder import AutoDecoder
from books.base import BaseComicBook
from bs4 import BeautifulSoup
from base64 import b64decode, b64encode

class Seven33SoBaseBook(BaseComicBook):
    accept_domains = ("https://www.733.so", "https://m.733.so")
    host = "https://www.733.so"

    # 获取漫画章节列表
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
        # <ul class="Drama autoHeight" id="mh-chapter-list-ol-0">
        soup = soup.find('ul', {"class":"Drama autoHeight", "id":"mh-chapter-list-ol-0"})
        if (soup is None):
            self.log.warn('chapter-list is not exist.')
            return chapterList

        lias = soup.findAll('a')
        if (lias is None):
            self.log.warn('chapter-list is not exist.')
            return chapterList

        # https://m.733.so/mh/28038/1109102.html
        for aindex in range(len(lias)):
            rindex = len(lias)-1-aindex
            href = "https://m.733.so" + lias[rindex].get('href', '')
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

        res = re.search(r'qTcms_S_m_murl_e="(.*)";', content).group()
        if (res is None):
            self.log.warn(content)
            self.log.warn('var qTcms_S_m_murl_e is not exist.')
            return imgList

        list_encoded = res.split('\"')[1]
        lz_decoded = b64decode(list_encoded)
        images = lz_decoded.split("$qingtiandy$")

        if (images is None):
            self.log.warn('image list is not exist.')
            return imgList

        for img in images:
            imgList.append(img)

        return imgList
