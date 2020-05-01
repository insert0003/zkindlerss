#!/usr/bin/env python
# -*- coding:utf-8 -*-
# http://www.cartoonmad.com网站的漫画的基类，简单提供几个信息实现一个子类即可推送特定的漫画
# Author: insert0003 <https://github.com/insert0003>
from bs4 import BeautifulSoup
from lib.urlopener import URLOpener
from lib.autodecoder import AutoDecoder
from books.base import BaseComicBook

class CartoonMadBaseBook(BaseComicBook):
    accept_domains = ("http://www.cartoonmad.com", "https://www.cartoonmad.com")
    host = "https://www.cartoonmad.com"

    # 获取漫画章节列表
    def getChapterList(self, url):
        decoder = AutoDecoder(isfeed=False)
        opener = URLOpener(self.host, timeout=60)
        chapterList = []

        if url.startswith("http://"):
            url = url.replace('http://', 'https://')

        if "/m/" in url:
            url = url.replace('/m/', '/')

        result = opener.open(url)
        if result.status_code != 200 or not result.content:
            self.log.warn('fetch comic page failed: %s' % url)
            return chapterList

        content = self.AutoDecodeContent(result.content, decoder, self.feed_encoding, opener.realurl, result.headers)

        soup = BeautifulSoup(content, 'html.parser')
        allComicTable = soup.find_all('table', {'width': '800', 'align': 'center'})

        if (allComicTable is None):
            self.log.warn('allComicTable is not exist.')
            return chapterList

        for comicTable in allComicTable:
            comicVolumes = comicTable.find_all('a', {'target': '_blank'})
            if (comicVolumes is None):
                self.log.warn('comicVolumes is not exist.')
                return chapterList

            for volume in comicVolumes:
                href = self.urljoin(self.host, volume.get("href"))
                chapterList.append((unicode(volume.string), href))

        return chapterList

    # 获取漫画图片列表
    def getImgList(self, url):
        imgList = []

        ulist = self.getImgUrlList(url)
        if not ulist:
            self.log.warn('can not find img list for : %s' % url)
            return imgList

        firstPage = self.getImgUrl(url)
        if not firstPage:
            self.log.warn('can not get first image real url : %s' % url)
            return imgList


        imgTail = firstPage.split("/")[-1]
        imgLeng = len(imgTail.split(".")[0])
        imgBase = firstPage.replace(imgTail, "")

        if "comicpic" in firstPage:
            # https://www.cartoonmad.com/comic/comicpic.asp?file=/5531/143/001
            imgType = ""
        else:
            # https://www.cartoonmad.com/75550/4897/001/001.jpg
            imgType = "."+imgTail.split(".")[1]

        for index in range(len(ulist)):
            imgUrl = "{}{}{}".format(imgBase, str(index+1).zfill(imgLeng), imgType)
            imgList.append(imgUrl)

        if imgList[0] != firstPage or imgList[-1] != self.getImgUrl(ulist[-1]):
            imgList = []
            for ul in ulist:
                imgList.append(self.getImgUrl(ul))

        self.log.info(imgList)
        return imgList

    # 获取漫画图片网址
    def getImgUrlList(self, url):
        imgUrlList = []
        decoder = AutoDecoder(isfeed=False)
        opener = URLOpener(self.host, timeout=60)

        result = opener.open(url)
        if result.status_code != 200 or not result.content:
            self.log.warn('fetch comic page failed: %s' % url)
            return None

        content = self.AutoDecodeContent(result.content, decoder, self.page_encoding, opener.realurl, result.headers)
        soup = BeautifulSoup(content, 'html.parser')
        sel = soup.find('select')  # 页码行，要提取所有的页面
        if (sel is None):
            self.log.warn('soup select is not exist.')
            return None

        ulist = sel.find_all('option') if sel else None
        if not ulist:
            self.log.warn('select option is not exist.')
            return None

        imgUrlList.append(url)
        for ul in ulist:
            if ul.get('value') is None:
                ulist.remove(ul)
            else:
                href = self.host + '/comic/' + ul.get('value')
                imgUrlList.append(href)

        self.log.info(imgUrlList)
        return imgUrlList

    # 获取漫画图片格式
    def getImgUrl(self, url):
        # From: https://www.cartoonmad.com/comic/489700014051001.html
        # To: https://www.cartoonmad.com/75550/4897/001/001.jpg
        tail = url.split("/")[-1].split(".")[0]
        cid = tail[:4]
        tid = tail[5:8]
        pid = tail[-3:]

        # if cid == "1643" or cid == "1220":
        #   imgurl = "https://web.cartoonmad.com/75699/{}/{}/{}.jpg".format(cid, tid, pid)
        # elif cid == "5531" or cid == "5187":
        #   imgurl = "https://www.cartoonmad.com/comic/comicpic.asp?file=/{}/{}/{}".format(cid, tid, pid)
        # else:
        #   imgurl = "https://www.cartoonmad.com/75566/{}/{}/{}.jpg".format(cid, tid, pid)
        if cid == "2704":
            # https://www.cartoonmad.com/comic/comicpic.asp?file=/2704/003/001&rimg=1
            imgurl = "https://www.cartoonmad.com/comic/comicpic.asp?file=/{}/{}/{}&rimg=1".format(cid, tid, pid)
        else:
            imgurl = "https://www.cartoonmad.com/comic/comicpic.asp?file=/{}/{}/{}".format(cid, tid, pid)
        return imgurl

        decoder = AutoDecoder(isfeed=False)
        opener = URLOpener(self.host, timeout=60)
        result = opener.open(url)
        if result.status_code != 200 or not result.content:
           self.log.warn('fetch comic page failed: %s' % url)
           return None

        content = self.AutoDecodeContent(result.content, decoder, self.page_encoding, opener.realurl, result.headers)
        soup = BeautifulSoup(content, 'html.parser')

        comicImgTag = soup.find('img', {'oncontextmenu': 'return false'})
        if (comicImgTag is None):
            self.log.warn('can not find image href.')
            return None
        imgUrl = self.host + "/comic/" + comicImgTag.get('src')

        headers = {'Referer': url}
        result = opener.open(imgUrl, headers=headers)
        if result.status_code != 200 or opener.realurl == url:
            self.log.warn('can not get real comic url for : %s' % url)
            return None

        return opener.realurl
