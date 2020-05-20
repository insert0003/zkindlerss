#!/usr/bin/env python3
# encoding: utf-8
#https://www.manhuagui.com或者https://m.manhuagui.com网站的免费漫画的基类，简单提供几个信息实现一个子类即可推送特定的漫画
#Author: insert0003 <https://github.com/insert0003>
import re, json
from lib.urlopener import URLOpener
from lib.autodecoder import AutoDecoder
from books.base import BaseComicBook
from bs4 import BeautifulSoup
import urllib, urllib2, imghdr
from google.appengine.api import images
from lib.userdecompress import decompressFromBase64

class ManHuaGuiBaseBook(BaseComicBook):
    accept_domains = (
        "https://www.manhuagui.com",
        "https://m.manhuagui.com",
        "https://tw.manhuagui.com",
    )
    host = "https://m.manhuagui.com"

    # 获取漫画图片内容
    def adjustImgContent(self, content):
        #强制转换成JPEG
        try:
            img = images.Image(content)
            img.resize(width=(img.width-1), height=(img.height-1))
            content = img.execute_transforms(output_encoding=images.JPEG)
            return content
        except:
            return None

    #获取图片信息
    def get_node_online(self, input_str):
        opts_str = 'console.log(%s)' % input_str.encode("utf-8")
        for njRetry in range(3):
            try:
                if njRetry == 0:
                    self.log.info("Try use runoob execution nodejs.")
                    url = "https://tool.runoob.com/compile2.php"
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
            except Exception, e:
                self.log.warn('str(Exception):{}'.format(str(e)))
                continue

    #获取漫画章节列表
    def getChapterList(self, url):
        decoder = AutoDecoder(isfeed=False)
        opener = URLOpener(self.host, timeout=60)
        chapterList = []

        url = url.replace("https://www.manhuagui.com", "https://m.manhuagui.com")
        url = url.replace("https://tw.manhuagui.com", "https://m.manhuagui.com")

        for njRetry in range(10):
            try:
                result = opener.open(url)
                if result.status_code == 200 and result.content:
                    break
            except Exception, e:
                if njRetry < 5:
                    self.log.warn('fetch comic page failed: %s, retry' % url)
                    continue
                else:
                    self.log.warn('fetch comic page failed: %s' % url)
                    return chapterList

        content = self.AutoDecodeContent(result.content, decoder, self.feed_encoding, opener.realurl, result.headers)

        soup = BeautifulSoup(content, 'html.parser')
        invisible_input = soup.find("input", {"id":'__VIEWSTATE'})
        if invisible_input:
            lz_encoded=invisible_input.get("value")
            lz_decoded = decompressFromBase64(lz_encoded)
            soup = BeautifulSoup(lz_decoded, 'html.parser')
        else:
            soup = soup.find("div", {"class": 'chapter-list', "id":'chapterList'})

        if (soup is None):
            self.log.warn('chapterList is not exist.')
            return chapterList

        lias = soup.findAll('a')
        if (lias is None):
            self.log.warn('chapterList href is not exist.')
            return chapterList

        for index, a in enumerate(lias):
            href = self.urljoin("https://m.manhuagui.com", a.get('href', ''))
            bstr = a.find("b")
            if bstr == None:
                chapterList.append((u'第%d话'%(index+1), href))
            else:
                chapterList.append((unicode(bstr.contents[0]), href))

        return list(reversed(chapterList))

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
        soup = BeautifulSoup(content, 'html.parser')
        scripts = soup.findAll("script", {"type": "text/javascript"})
        for script in scripts:
            if "window[\"\\x65\\x76\\x61\\x6c\"]" in script.text != "":
                raw_content = script.text
                break

        if (raw_content is None):
            self.log.warn('raw_content href is not exist.')
            return imgList

        res = re.search(r'window\["\\x65\\x76\\x61\\x6c"\](.*\))', raw_content).group(1)
        lz_encoded = re.search(r"'([A-Za-z0-9+/=]+)'\['\\x73\\x70\\x6c\\x69\\x63'\]\('\\x7c'\)", res).group(1)
        lz_decoded = decompressFromBase64(lz_encoded)
        res = re.sub(r"'([A-Za-z0-9+/=]+)'\['\\x73\\x70\\x6c\\x69\\x63'\]\('\\x7c'\)", "'%s'.split('|')"%(lz_decoded), res)
        codes = self.get_node_online(res)
        pages_opts = json.loads(re.search(r'^SMH.reader\((.*)\)\.preInit\(\);$', codes).group(1))

        # cid = self.getChapterId(url)
        m = pages_opts["sl"]["m"]
        e = pages_opts["sl"]["e"]
        images = pages_opts["images"]

        if (images is None):
            self.log.warn('image list is not exist.')
            return imgList

        for img in images:
            # https://i.hamreus.com/ps3/p/pingxingtt_gbl/%E7%AC%AC117%E8%AF%9D/1_7684.jpg.webp?e=1769209619&m=MOn_QAAi-qwQBaRjlmNYkA
            img_url = u'https://i.hamreus.com{}?e={}&m={}'.format(img, e, m)
            imgList.append(img_url)

        return imgList

    def getChapterId(self, url):
        section = url.split("/")
        fName = section[len(section)-1]
        return fName.split(".")[0]