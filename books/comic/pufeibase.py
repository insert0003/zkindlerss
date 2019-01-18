#!/usr/bin/env python3
# encoding: utf-8
#http://www.pufei.net或者http://m.pufei.net网站的免费漫画的基类，简单提供几个信息实现一个子类即可推送特定的漫画
#Author: insert0003 <https://github.com/insert0003>
import re, json
from lib.urlopener import URLOpener
from lib.autodecoder import AutoDecoder
from books.base import BaseComicBook
from bs4 import BeautifulSoup
import urllib, urllib2, imghdr
from base64 import b64decode, b64encode

class PuFeiBaseBook(BaseComicBook):
    title               = u''
    description         = u''
    language            = ''
    feed_encoding       = ''
    page_encoding       = ''
    mastheadfile        = ''
    coverfile           = ''
    host                = 'http://m.pufei.net'
    feeds               = [] #子类填充此列表[('name', mainurl),...]

    #获取漫画章节列表
    def getChapterList(self, url):
        decoder = AutoDecoder(isfeed=False)
        opener = URLOpener(self.host, timeout=60)
        chapterList = []

        if url.startswith( "http://www.pufei.net" ):
            url = url.replace('http://www.pufei.net', 'http://m.pufei.net')

        result = opener.open(url)
        if result.status_code != 200 or not result.content:
            self.log.warn('fetch comic page failed: %s' % url)
            return chapterList

        content = self.AutoDecodeContent(result.content, decoder, self.feed_encoding, opener.realurl, result.headers)

        soup = BeautifulSoup(content, 'html.parser')
        soup = soup.find('div', {"class":"chapter-list", "id":"chapterList2"})
        if (soup is None):
            self.log.warn('chapter-list is not exist.')
            return chapterList

        lias = soup.findAll('a')
        if (lias is None):
            self.log.warn('chapterList href is not exist.')
            return chapterList

        for aindex in range(len(lias)):
            rindex = len(lias)-1-aindex
            href = "http://m.pufei.net" + lias[rindex].get("href")
            chapterList.append(href)

        return chapterList

    #获取图片信息
    def get_node_online(self, input_str):
        opts_str = 'console.log(%s)' % input_str.encode("utf-8")
        try:
            self.log.warn("Try use runoob execution nodejs.")
            url = "https://m.runoob.com/api/compile.php"
            params = {"code":opts_str, "stdin":"", "language":"4", "fileext":"node.js"}
            params = urllib.urlencode(params)
            req = urllib2.Request(url)
            req.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
            req.add_data(params)

            res = urllib2.urlopen(req)
            result = json.loads(res.read())
            return result["output"]
        except:
            self.log.warn("Try use tutorialspoint execution nodejs.")
            url = "https://tpcg.tutorialspoint.com/tpcg.php"
            params = {"lang":"node", "device":"", "code":opts_str, "stdin":"", "ext":"js", "compile":0, "execute": "node main.js", "mainfile": "main.js", "uid": 4203253 }
            params = urllib.urlencode(params)
            req = urllib2.Request(url)
            req.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
            req.add_data(params)

            res = urllib2.urlopen(req)
            result = BeautifulSoup(res.read(), 'html.parser')
            return result.find("br").text

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

        res = re.search(r'cp=".*";', content).group()
        if (res is None):
            self.log.warn('var qTcms_S_m_murl_e is not exist.')
            return imgList

        list_encoded = res.split('\"')[1]
        lz_decoded = b64decode(list_encoded)
        lz_nodejs = self.get_node_online(lz_decoded)

        if (lz_nodejs is None):
            self.log.warn('image list is not exist.')
            return imgList

        images = re.sub("\[|\]| |'|\n", "", lz_nodejs).split(",")
        for img in images:
            img_url = "http://res.img.pufei.net/" + img
            imgList.append(img_url)

        return imgList