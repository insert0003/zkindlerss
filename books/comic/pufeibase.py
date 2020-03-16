#!/usr/bin/env python3
# encoding: utf-8
#http://www.pufei8.com或者http://m.pufei8.com网站的免费漫画的基类，简单提供几个信息实现一个子类即可推送特定的漫画
#Author: insert0003 <https://github.com/insert0003>
import re, json
from lib.urlopener import URLOpener
from lib.autodecoder import AutoDecoder
from books.base import BaseComicBook
from bs4 import BeautifulSoup
import urllib, urllib2, imghdr

class PuFeiBaseBook(BaseComicBook):
    accept_domains = ("http://www.pufei8.com", "http://m.pufei.com")
    host = "http://www.pufei8.com"

    #获取漫画章节列表
    def getChapterList(self, url):
        decoder = AutoDecoder(isfeed=False)
        opener = URLOpener(self.host, timeout=60)
        chapterList = []

        if url.startswith( "http://m.pufei8.com" ):
            url = url.replace('http://m.pufei8.com', 'http://www.pufei8.com')

        result = opener.open(url)
        if result.status_code != 200 or not result.content:
            self.log.warn('fetch comic page failed: %s' % url)
            return chapterList

        content = self.AutoDecodeContent(result.content, decoder, self.feed_encoding, opener.realurl, result.headers)

        soup = BeautifulSoup(content, 'html.parser')
		# <div class="plist pmedium max-h200" id="play_0">
        soup = soup.find('div', {"class":"plist pmedium max-h200", "id":"play_0"})
        if (soup is None):
            self.log.warn('chapter-list is not exist.')
            return chapterList

        lias = soup.findAll('a')
        if (lias is None):
            self.log.warn('chapterList href is not exist.')
            return chapterList

        for index, a in enumerate(lias):
            href = self.urljoin("http://www.pufei8.com", a.get('href', ''))
            chapterList.append((unicode(lias[index].string), href))

        return list(reversed(chapterList))

    #获取图片信息
    def get_node_online(self, input_str):
        opts_str = 'console.log(%s)' % input_str.encode("utf-8")

        for njRetry in range(3):
            try:
                if njRetry == 0:
                    self.log.info("Try use rextester execution nodejs.")
                    url = "https://rextester.com/rundotnet/Run"

                    params = {"LanguageChoiceWrapper":"23", "EditorChoiceWrapper":1, "LayoutChoiceWrapper":1, "Program":opts_str, "Input":"", "Privacy":"", "PrivacyUsers":"", "Title": "", "SavedOutput": "", "WholeError": "", "WholeWarning": "", "StatsToSave": "", "CodeGuid": "", "IsInEditMode": False, "IsLive": False }
                    params = urllib.urlencode(params)
                    req = urllib2.Request(url)
                    req.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
                    req.add_data(params)

                    res = urllib2.urlopen(req)
                    result = json.loads(res.read())
                    return result["Result"]
                elif njRetry == 1:
                    self.log.info("Try use tutorialspoint execution nodejs.")
                    url = "https://tpcg.tutorialspoint.com/tpcg.php"
                    params = {"lang":"node", "device":"", "code":opts_str, "stdinput":"", "ext":"js", "compile":0, "execute": "node main.js", "mainfile": "main.js", "uid": 9920007 }
                    params = urllib.urlencode(params)
                    req = urllib2.Request(url)
                    req.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
                    req.add_data(params)

                    res = urllib2.urlopen(req)
                    result = BeautifulSoup(res.read(), 'html.parser')
                    return result.find("br").text
                else:
                    self.log.info("Try use runoob execution nodejs.")
                    url = "https://tool.runoob.com/compile.php"
                    params = {"code":opts_str, "token":"4381fe197827ec87cbac9552f14ec62a", "language":"4", "fileext":"node.js"}
                    params = urllib.urlencode(params)
                    req = urllib2.Request(url)
                    req.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
                    req.add_data(params)

                    res = urllib2.urlopen(req)
                    result = res.read()
                    result = result.replace("\/", "/")
                    result = json.loads(result)
                    return result["output"]
            except Exception, e:
                self.log.warn('str(Exception):{}'.format(str(e)))
                continue

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

        try:
            # function base64decode(str){*};
            func = re.search(r'function\ base64decode\(str\){.*};', content).group()
            func = func.split('base64decode')[1].replace('};', '}')

            # packed="*";
            packed = re.search(r'packed=".*";', content).group()
            packed = packed.split('\"')[1]
        except:
            self.log.warn('var photosr is not exist.')
            return imgList

        # eval(function(str){*}("*").slice(4))
        lz_input = "eval(function{}(\"{}\").slice(4))".format(func, packed)
        lz_nodejs = self.get_node_online(lz_input)

        if (lz_nodejs is None):
            self.log.warn('image list is not exist.')
            return imgList

        # photosr[1]="images/2019/11/08/09/19904f5d64.jpg/0";...photosr[98]="images/2019/11/08/09/22abc96bd2.jpg/0";
        images = lz_nodejs.split("\"")
        self.log.info(images)
		# http://res.img.220012.net/2017/08/22/13/343135d67f.jpg
        for img in images:
            if ".jpg" in img:
                img_url = self.urljoin("http://res.img.220012.net", img)
                imgList.append(img_url)

        return imgList
