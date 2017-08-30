#!/usr/bin/env python
# -*- coding:utf-8 -*-
from base import BaseComicBook

def getBook():
    return AJin

class AJin(BaseComicBook):
    title               = u'亚人'
    description         = u'日本漫画家樱井画门创作的漫画'
    language            = 'zh-tw'
    feed_encoding       = 'big5'
    page_encoding       = 'big5'
    mastheadfile        = 'mh_comic.gif'
    coverfile           = 'cv_ajin.jpg'
    mainurl             = 'http://www.cartoonmad.com/comic/3572.html'
