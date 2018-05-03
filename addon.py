#  earthTV Addon
#
#      Copyright (C) 2016
#      http://
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import os
import sys
import urllib
import urllib2
import urlparse
import re
import requests
import HTMLParser

import buggalo

import json

import datetime
import calendar

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

from xml.dom.minidom import parse, parseString

CommonRootView = 50
FullWidthList = 51
ThumbnailView = 500
MediaListView2 = 503
MediaListView3 = 504
PictureWrapView = 510
PictureThumbView = 514

#place holder for error message
ERROR_MESSAGE1 = 'line 1'
ERROR_MESSAGE2 = 'line 2'
ERROR_MESSAGE3 = 'line 3'

class EarthTV(object):

    def showSelector(self):

        xbmc.log('- main selector -')
        xbmcplugin.setContent(HANDLE, 'movies')

        url="http://www.earthtv.com/en/"
        if(SITE== '1'):
            url="http://www.earthtv.com/de/"
        elif (SITE == '2'):
            url="http://www.earthtv.com/fr/"
        elif (SITE == '3'):
            url="http://www.earthtv.com/ru/"
        elif (SITE == '4'):
            url="http://www.earthtv.com/ar/"

        # add live channel
        self.addPictureItem('The World LIVE', PATH + '?categories=%s' % url, ICON)

        # add next page
        self.addFolderItem('Next page', PATH + '?page=2')

        # get channels from page 1
        url = 'http://www.earthtv.com/de/webcams/1'

        u = urllib2.urlopen(url)
        html = u.read()
        u.close()

        for m in re.finditer('<div.class="place.video-thumb">.*?href="(?P<href>[^\"]*)".*?src="(?P<src>[^\"]*)".*?alt="(?P<alt>[^\"]*)".*?<\/div>', html, re.DOTALL):

            url = "http://www.earthtv.com" + m.group('href')
            thumb = "http:" + m.group('src')
            title = m.group('alt')

            self.addPictureItem(title, PATH + '?categories=%s' % url, thumb)

        #xbmc.executebuiltin('Container.SetViewMode(%d)' % ThumbnailView)
        xbmc.executebuiltin('Container.SetViewMode(%d)' % PictureWrapView)
        xbmcplugin.endOfDirectory(HANDLE)

    def showCategory(self, url):

        url = url[5:]
        url = "http:" + urllib2.quote(url)

        xbmc.log("earthTV: show URL %s" % url, level=xbmc.LOGNOTICE)

        #stop buffering
        xbmcgui.Window(10000).setProperty('earthURL','')
        while(xbmcgui.Window(10000).getProperty('earthSeq')<>''):
            xbmc.sleep(1000)
            xbmc.log("earthTV: wait stop stream", level=xbmc.LOGNOTICE)
            xbmcgui.Dialog().notification(ADDON_NAME, 'Stop stream', time=1100)

        xbmcgui.Dialog().notification(ADDON_NAME, 'Query link', time=1000)

        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            result = r.text
            xbmc.log("earthTV: %s" % 'get page', level=xbmc.LOGNOTICE)

            # find referer
            s1 = '<meta.itemprop="embedURL".content="(.*?)"'
            match = re.search(s1,result)
            if match is not None:
                ref = match.group(1)
                xbmcgui.Window(10000).setProperty('earthRef', ref)

                xbmc.log("earthTV: %s" % 'find referer', level=xbmc.LOGNOTICE)

                #find playlist
                playlist = '<iframe.*?src="(.*?)"'
                match = re.search(playlist, result)
                if match is not None:
                    xbmc.log("earthTV: %s" % 'find playlist', level=xbmc.LOGNOTICE)

                    # find data
                    data = 'token=(?P<token>.*?)&.*?livesd=(?P<url>.*?)"'
                    match = re.search(data, match.group(0))
                    if(match != None):
                        xbmc.log("earthTV: %s" % 'find data', level=xbmc.LOGNOTICE)

                        url = match.group('url')
                        baseurl = url[:url.rfind('/')+1]

                        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
                                  'Referer': ref,
                                  'Origin': 'http://playercdn.earthtv.com'}

                        r = requests.get(url, headers=header)
                        if r.status_code == requests.codes.ok:
                            playlist = r.text
                            xbmc.log("earthTV: %s" % 'load playlist', level=xbmc.LOGNOTICE)

                            chunk = None
                            cnt = 0

                            # now we try to grab chunk list, sites are nested
                            while chunk is None and cnt < 3:
                                chunkline = None
                                cnt = cnt + 1

                                lines = playlist.split('\n')
                                for line in lines:
                                     if(not line.startswith('#')):
                                        chunkline = line
                                        break

                                if(chunkline != None):
                                    xbmc.log("earthTV: %s" % 'get chunklist', level=xbmc.LOGNOTICE)

                                    #chunklist = 'http://cdn.liveonearth.com/cdnedge/smil:TWL-en.smil/' + chunkline
                                    chunklist = baseurl + chunkline

                                    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
                                              'Referer': ref,
                                              'Origin': 'http://playercdn.earthtv.com',
                                              'Host': 'cdn.liveonearth.com',
                                              'Accept': '*/*',
                                              'Accept-Encoding': 'gzip, deflate',
                                              'Accept-Language': 'de,en-US;q=0.7,en;q=0.3'
                                             }

                                    r=requests.get(chunklist, headers=header)
                                    if r.status_code == requests.codes.ok:
                                        playlist = r.text

                                        if('EXT-X-MEDIA-SEQUENCE' in playlist):
                                            # list contains sequence
                                            chunk = playlist
                                            seqstart = ''

                                            lines = playlist.split('\n')
                                            for line in lines:
                                                if(line.startswith('#EXT-X-MEDIA-SEQUENCE:')):
                                                    seqstart = line[22:]
                                                    xbmcgui.Window(10000).setProperty('earthSeq', seqstart)
                                                    xbmc.log("earthTV: %s" % 'sequence found ' +str(seqstart), level=xbmc.LOGNOTICE)
                                                    break

                                            if(seqstart <> ''):
                                                for line in lines:
                                                    if(not line.startswith('#') and (len(line)>10)):
                                                        xbmcgui.Window(10000).setProperty('earthURL', baseurl + line)
                                                        xbmc.log("earthTV: %s" % 'start buffering', level=xbmc.LOGNOTICE)

                                                        xbmcgui.Dialog().notification(ADDON_NAME, 'Buffering', time=3000)
                                                        xbmc.sleep(3000)
                                                        xbmc.Player().play(VID)

                                                        break
                                    else:
                                        cnt = 3

    def showPage(self, page):

        xbmc.log('- page - ' + page)

        i = int(page)
        i = i + 1

        # add next page
        self.addFolderItem('Next page', PATH + '?page=' +str(i))

        # get channels from page x
        url="http://www.earthtv.com/en/"
        if(SITE== '1'):
            url="http://www.earthtv.com/de/"
        elif (SITE == '2'):
            url="http://www.earthtv.com/fr/"
        elif (SITE == '3'):
            url="http://www.earthtv.com/ru/"
        elif (SITE == '4'):
            url="http://www.earthtv.com/ar/"

        url = url + "webcams/" + page

        u = urllib2.urlopen(url)
        html = u.read()
        u.close()

        for m in re.finditer('<div.class="place.video-thumb">.*?href="(?P<href>[^\"]*)".*?src="(?P<src>[^\"]*)".*?alt="(?P<alt>[^\"]*)".*?<\/div>', html, re.DOTALL):

            url = "http://www.earthtv.com" + m.group('href')
            thumb = "http:" + m.group('src')
            title = m.group('alt')

            self.addPictureItem(title, PATH + '?categories=%s' % url, thumb)

        xbmc.executebuiltin('Container.SetViewMode(%d)' % ThumbnailView)
        xbmcplugin.endOfDirectory(HANDLE)


#### some functions ####

    def addFolderItem(self, title, url):
        list_item = xbmcgui.ListItem(label=title)
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, True)

    def addPictureItem(self, title, url, thumb):

        list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumb)

        list_item.setArt({'thumb': thumb,
                          'icon': thumb,
                          'fanart': BACKG})

        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, False)

#### main entry point ####

if __name__ == '__main__':

    ADDON = xbmcaddon.Addon()
    ADDON_NAME = ADDON.getAddonInfo('name')

    PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
    VID = os.path.join(PROFILE, "video.ts")

    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    BACKG = os.path.join(ADDON.getAddonInfo('path'), 'nasa.jpg')

    DEBUG_PLUGIN = True
    DEBUG_HTML = False
    USE_THUMBS = True

    ERROR_MESSAGE1 = ADDON.getLocalizedString(30150)
    ERROR_MESSAGE2 = ADDON.getLocalizedString(30151)
    ERROR_MESSAGE3 = ADDON.getLocalizedString(30152)

    if(str(xbmcplugin.getSetting(HANDLE, 'debug')) == 'true'):
        DEBUG_PLUGIN = True
    if(str(xbmcplugin.getSetting(HANDLE, 'debugHTML')) == 'true'):
        DEBUG_HTML = True

    SITE = xbmcplugin.getSetting(HANDLE, 'siteVersion')

try:
        iArchive = EarthTV()

        if PARAMS.has_key('categories'):
            iArchive.showCategory(PARAMS['categories'][0])
        elif PARAMS.has_key('page'):
            iArchive.showPage(PARAMS['page'][0])
        else:
            iArchive.showSelector()
except Exception:
    buggalo.onExceptionRaised()
