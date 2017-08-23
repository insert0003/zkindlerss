#!/usr/bin/env python
# -*- coding:utf-8 -*-
from base import BaseComicBook

def getBook():
    return KissXDeath

class KissXDeath(BaseComicBook):
    title               = u'KissXDeath'
    description         = u'叶恭弘创作，2014年09月22日新连载在电子漫画周刊《少年Jump+》上的作品'
    language            = 'zh-tw'
    feed_encoding       = 'big5'
    page_encoding       = 'big5'
    mastheadfile        = 'mh_comic.gif'
    coverfile           = 'cv_kissxdeath.jpg'
    mainurl             = 'http://www.cartoonmad.com/comic/4329.html'
