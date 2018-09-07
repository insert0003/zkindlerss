#!/usr/bin/env python3
# encoding: utf-8
#https://www.manhuagui.com或者https://m.manhuagui.com网站的免费漫画的基类，简单提供几个信息实现一个子类即可推送特定的漫画
#Author: insert0003 <https://github.com/insert0003>
import re, urlparse, json, datetime, base64
from time import sleep
from config import TIMEZONE
from lib.urlopener import URLOpener
from lib.autodecoder import AutoDecoder
from books.base import BaseComicBook
from apps.dbModels import LastDelivered
from bs4 import BeautifulSoup
import urllib, urllib2, imghdr
from google.appengine.api import images

from __builtin__ import unichr as chr
import math
import re

keyStrBase64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
baseReverseDic = {};

class Object(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def getBaseValue(alphabet, character):
    if alphabet not in baseReverseDic:
        baseReverseDic[alphabet] = {}
    for i in range(len(alphabet)):
        baseReverseDic[alphabet][alphabet[i]] = i
    return baseReverseDic[alphabet][character]

def _decompress(length, resetValue, getNextValue):
    dictionary = {}
    enlargeIn = 4
    dictSize = 4
    numBits = 3
    entry = ""
    result = []

    data = Object(
        val=getNextValue(0),
        position=resetValue,
        index=1
    )

    for i in range(3):
        dictionary[i] = i

    bits = 0
    maxpower = math.pow(2, 2)
    power = 1

    while power != maxpower:
        resb = data.val & data.position
        data.position >>= 1
        if data.position == 0:
            data.position = resetValue
            data.val = getNextValue(data.index)
            data.index += 1

        bits |= power if resb > 0 else 0
        power <<= 1;

    next = bits
    if next == 0:
        bits = 0
        maxpower = math.pow(2, 8)
        power = 1
        while power != maxpower:
            resb = data.val & data.position
            data.position >>= 1
            if data.position == 0:
                data.position = resetValue
                data.val = getNextValue(data.index)
                data.index += 1
            bits |= power if resb > 0 else 0
            power <<= 1
        c = chr(bits)
    elif next == 1:
        bits = 0
        maxpower = math.pow(2, 16)
        power = 1
        while power != maxpower:
            resb = data.val & data.position
            data.position >>= 1
            if data.position == 0:
                data.position = resetValue;
                data.val = getNextValue(data.index)
                data.index += 1
            bits |= power if resb > 0 else 0
            power <<= 1
        c = chr(bits)
    elif next == 2:
        return ""

    dictionary[3] = c
    w = c
    result.append(c)
    counter = 0
    while True:
        counter += 1
        if data.index > length:
            return ""

        bits = 0
        maxpower = math.pow(2, numBits)
        power = 1
        while power != maxpower:
            resb = data.val & data.position
            data.position >>= 1
            if data.position == 0:
                data.position = resetValue;
                data.val = getNextValue(data.index)
                data.index += 1
            bits |= power if resb > 0 else 0
            power <<= 1

        c = bits
        if c == 0:
            bits = 0
            maxpower = math.pow(2, 8)
            power = 1
            while power != maxpower:
                resb = data.val & data.position
                data.position >>= 1
                if data.position == 0:
                    data.position = resetValue
                    data.val = getNextValue(data.index)
                    data.index += 1
                bits |= power if resb > 0 else 0
                power <<= 1

            dictionary[dictSize] = chr(bits)
            dictSize += 1
            c = dictSize - 1
            enlargeIn -= 1
        elif c == 1:
            bits = 0
            maxpower = math.pow(2, 16)
            power = 1
            while power != maxpower:
                resb = data.val & data.position
                data.position >>= 1
                if data.position == 0:
                    data.position = resetValue;
                    data.val = getNextValue(data.index)
                    data.index += 1
                bits |= power if resb > 0 else 0
                power <<= 1
            dictionary[dictSize] = chr(bits)
            dictSize += 1
            c = dictSize - 1
            enlargeIn -= 1
        elif c == 2:
            return "".join(result)

        if enlargeIn == 0:
            enlargeIn = math.pow(2, numBits)
            numBits += 1

        if c in dictionary:
            entry = dictionary[c]
        else:
            if c == dictSize:
                entry = w + w[0]
            else:
                return None
        result.append(entry)

        # Add w+entry[0] to the dictionary.
        dictionary[dictSize] = w + entry[0]
        dictSize += 1
        enlargeIn -= 1

        w = entry
        if enlargeIn == 0:
            enlargeIn = math.pow(2, numBits)
            numBits += 1

class ManHuaGuiBaseBook(BaseComicBook):
    title               = u''
    description         = u''
    language            = ''
    feed_encoding       = ''
    page_encoding       = ''
    mastheadfile        = ''
    coverfile           = ''
    host                = 'https://www.manhuagui.com'
    feeds               = [] #子类填充此列表[('name', mainurl),...]

    #使用此函数返回漫画图片列表[(section, title, url, desc),...]
    def ParseFeedUrls(self):
        urls = [] #用于返回
        
        userName = self.UserName()
        for item in self.feeds:
            title, url = item[0], item[1]
            comic_id = ""
            
            lastCount = LastDelivered.all().filter('username = ', userName).filter("bookname = ", title).get()
            if not lastCount:
                self.log.info('These is no log in db LastDelivered for name: %s, set to 0' % title)
                oldNum = 0
            else:
                oldNum = lastCount.num

            if url.startswith( "https://m.manhuagui.com" ):
                url = url.replace('https://m.manhuagui.com', 'https://www.manhuagui.com')

            chapterList = self.getChapterList(url)
            if oldNum < len(chapterList):
                imgList = self.getImgList(chapterList[oldNum])
                if len(imgList) == 0:
                    self.log.warn('can not found image list: %s' % chapterList[oldNum])
                    break

                pageCount=0
                for img in imgList:
                    pageCount=pageCount+1
                    fTitle='{}/{}'.format(pageCount, len(imgList))
                    urls.append((title, fTitle, img, None))
                    self.log.warn('comicSrc: %s' % img)

                self.UpdateLastDelivered(title, oldNum+1)

        return urls

    #生成器，返回一个图片元组，mime,url,filename,content,brief,thumbnail
    def Items(self):
        urls = self.ParseFeedUrls()
        opener = URLOpener(self.host, timeout=self.timeout, headers=self.extra_header)
        decoder = AutoDecoder(isfeed=False)
        prevSection = ''
        htmlTemplate = '<html><head><meta http-equiv="Content-Type" content="text/html;charset=utf-8"><title>%s</title></head><body><img src="%s"/></body></html>'

        for section, fTitle, url, desc in urls:
            if section != prevSection or prevSection == '':
                    decoder.encoding = '' #每个小节都重新检测编码[当然是在抓取的是网页的情况下才需要]
                    prevSection = section
                    opener = URLOpener(self.host, timeout=self.timeout, headers=self.extra_header)
                    if self.needs_subscription:
                        result = self.login(opener, decoder)

            result = opener.open(url)
            content = result.content
            if not content:
                self.log.warn('can not get image content %s' % url)
                continue

            imgFilenameList = []

            #强制转换成JPEG
            self.log.warn('convert to JPEG %s' % url)
            # content = convert_image(content)
            img = images.Image(content)
            img.resize(width=(img.width-1), height=(img.height-1))
            content = img.execute_transforms(output_encoding=images.JPEG)
            #先判断是否是图片
            imgType = imghdr.what(None, content)
            self.log.warn('This image is %s' % imgType)

            if imgType:
                content = self.process_image_comic(content)
                if content:
                    if isinstance(content, (list, tuple)): #一个图片分隔为多个图片
                        imgIndex = self.imgindex
                        for idx, imgPartContent in enumerate(content):
                            imgType = imghdr.what(None, imgPartContent)
                            imgMime = r"image/" + imgType
                            fnImg = "img%d_%d.jpg" % (imgIndex, idx)
                            imgPartUrl = url[:-4]+"_%d.jpg"%idx
                            imgFilenameList.append(fnImg)
                            yield (imgMime, imgPartUrl, fnImg, imgPartContent, None, True)
                    else: #单个图片
                        imgType = imghdr.what(None, content)
                        imgMime = r"image/" + imgType
                        fnImg = "img%d.%s" % (self.imgindex, 'jpg' if imgType=='jpeg' else imgType)
                        imgFilenameList.append(fnImg)
                        yield (imgMime, url, fnImg, content, None, None)

            #每个图片当做一篇文章，否则全屏模式下图片会挤到同一页
            for imgFilename in imgFilenameList:
                tmpHtml = htmlTemplate % (fTitle, imgFilename)
                yield (imgFilename.split('.')[0], url, fTitle, tmpHtml, '', None)

    #获取图片信息
    def get_node_online(self, input_str):
        opts_str = 'console.log(%s)' % input_str.encode("utf-8")
        url = "https://m.runoob.com/api/compile.php"
        params = {"code":opts_str, "stdin":"", "language":"4", "fileext":"node.js"}
        params = urllib.urlencode(params)

        req = urllib2.Request(url)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
        req.add_data(params)

        res = urllib2.urlopen(req)
        result = json.loads(res.read())
        return result["output"]

    #获取漫画章节列表
    def getChapterList(self, url):
        decoder = AutoDecoder(isfeed=False)
        opener = URLOpener(self.host, timeout=60)
        chapterList = []

        result = opener.open(url)
        if result.status_code != 200 or not result.content:
            self.log.warn('fetch comic page failed: %s' % url)
            return chapterList

        content = self.AutoDecodeContent(result.content, decoder, self.feed_encoding, opener.realurl, result.headers)

        soup = BeautifulSoup(content, 'lxml')
        invisible_input = soup.find("input", {"id":'__VIEWSTATE'})
        if invisible_input:
            lz_encoded=invisible_input.get("value")
            lz_decoded = self.decompressFromBase64(lz_encoded)
            soup = BeautifulSoup(lz_decoded, 'lxml')

        divs = soup.findAll("div", {"class": 'chapter-list cf mt10'})

        for divCount in range(len(divs)):
            prefix = len(divs)-1-divCount
            div = divs[prefix]
            for ul in div.findAll('ul'):
                lias = ul.findAll('a')
                for aindex in range(len(lias)):
                    rindex = len(lias)-1-aindex
                    title = lias[rindex].get("title")
                    href = "https://www.manhuagui.com" + lias[rindex].get("href")
                    chapterList.append({'title':title, 'href':href})

        return chapterList

    #获取漫画图片列表
    def getImgList(self, url):
        decoder = AutoDecoder(isfeed=False)
        opener = URLOpener(self.host, timeout=60)
        imgList = []

        result = opener.open(url['href'])
        if result.status_code != 200 or not result.content:
            self.log.warn('fetch comic page failed: %s' % url)
            return imgList

        content = self.AutoDecodeContent(result.content, decoder, self.feed_encoding, opener.realurl, result.headers)
        soup = BeautifulSoup(content, 'lxml')
        scripts = soup.findAll("script", {"type": "text/javascript"})
        for script in scripts:
            if script.text != "":
                raw_content = script.text
                break

        res = re.search(r'window\["\\x65\\x76\\x61\\x6c"\](.*\))', raw_content).group(1)
        lz_encoded = re.search(r"'([A-Za-z0-9+/=]+)'\['\\x73\\x70\\x6c\\x69\\x63'\]\('\\x7c'\)", res).group(1)
        lz_decoded = self.decompressFromBase64(lz_encoded)
        res = re.sub(r"'([A-Za-z0-9+/=]+)'\['\\x73\\x70\\x6c\\x69\\x63'\]\('\\x7c'\)", "'%s'.split('|')"%(lz_decoded), res)
        codes = self.get_node_online(res)
        pages_opts = json.loads(re.search(r'^SMH.imgData\((.*)\)\.preInit\(\);$', codes).group(1))

        cid = pages_opts["cid"]
        md5 = pages_opts["sl"]["md5"]
        path = pages_opts["path"]
        files = pages_opts["files"]
        for img in files:
            img_url = 'https://i.hamreus.com{}{}?cid={}&md5={}'.format(path.encode("utf8"), img, cid, md5)
            imgList.append(img_url)

        return imgList

    def decompressFromBase64(self, compressed):
        if compressed is None:
            return ""
        if compressed == "":
            return None
        return _decompress(len(compressed), 32, lambda index: getBaseValue(keyStrBase64, compressed[index]))
