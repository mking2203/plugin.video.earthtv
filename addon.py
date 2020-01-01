#!/usr/bin/python
# -*- coding: utf-8 -*-

#  earthTV Addon
#
#      Copyright (C) 2018 Mark Koenig
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
import iso8601
import urllib
import urllib2
import urlparse
import re
import requests
from HTMLParser import HTMLParser

import buggalo

import json

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

CommonRootView = 50
FullWidthList = 51
InfoWall = 54
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

        # add live channel
        self.addPictureItem('The World LIVE', PATH + '?playLive=%s' % (BASEURL + COUNTRY), ICON)
        # Main channels
        self.addFolderItem('Webcams', PATH + '?region=' + COUNTRY + 'webcams' '&page=1')

        r = requests.get((BASEURL + COUNTRY) + 'webcams')
        if r.status_code == requests.codes.ok:
            # page is loaded
            result = r.text

            data = '<ul.class="dropdown-menu".*?>(.*?)<.ul'
            match = re.search(data, result)
            if(match != None):
                data = '<a.href="(.*?)">(.*?)<'
                matches = re.finditer(data, match.group(0))
                if(matches != None):
                    for match in matches:
                        self.addFolderItem(match.group(2), PATH + '?region=' + match.group(1) + '&page=1')

        xbmc.executebuiltin('Container.SetViewMode(%d)' % InfoWall)
        xbmcplugin.endOfDirectory(HANDLE)

    def showRegion(self, region, page):

        xbmc.log('- show region -')
        xbmcplugin.setContent(HANDLE, 'movies')

        no = int(page)

        # add next page
        self.addFolderItem('Next page', PATH + '?region=' + region + '&page=' + str(no + 1))

        # get channels
        urlpage = BASEURL + region + '/' + page
        xbmc.log("earthTV: %s" % urlpage, level=xbmc.LOGNOTICE)

        u = urllib2.urlopen(urlpage)
        html = u.read()
        u.close()

        for m in re.finditer('<div.class="place.video-thumb">.*?href="(?P<href>[^\"]*)".*?src="(?P<src>[^\"]*)".*?alt="(?P<alt>[^\"]*)".*?<\/div>', html, re.DOTALL):
            url = "http://www.earthtv.com" + m.group('href')
            thumb = "http:" + m.group('src')
            title = m.group('alt')
            self.addFolderItem(title, PATH + '?camera=%s' % url, thumb)

        xbmc.executebuiltin('Container.SetViewMode(%d)' % InfoWall)
        xbmcplugin.endOfDirectory(HANDLE)

    def showCamera(self, url):

        xbmc.log('- show camera -')
        xbmcplugin.setContent(HANDLE, 'movies')

        # get channels
        xbmc.log("earthTV: %s" % url, level=xbmc.LOGNOTICE)

        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            # page is loaded
            result = r.text

            #actual channel
            s1 = '<meta.itemprop="embedURL".content="(.*?)"'
            match = re.search(s1,result)
            if match is not None:
                #ref found
                ref = match.group(1)
                refs = ref + '&'

                lang = ''
                loc = ''
                channel = ''
                token = ''

                s1 = 'channel=(.*?)&'
                match = re.search(s1,refs)
                if match is not None:
                    channel = match.group(1)

                    # search thumb
                    s1 = '<meta.itemprop="thumbnailURL".content="(.*?)"'
                    match = re.search(s1,result)
                    if match is not None:
                        thumb = match.group(1)
                        if('live' in channel):
                            self.addPictureItem('PLAY\n' + channel, PATH + '?playLive=%s' % url, thumb)
                        else:
                            self.addPictureItem('PLAY\n' + channel, PATH + '?play=%s' % url, thumb)

            # search channels
            s1 = '<div.class="content">.<a.href="(.*?)".*?<img.src="(.*?)".*?<div.class="title">(.*?)<'
            match = re.finditer(s1,result)
            for m in match:

                url = BASEURL + str(m.group(1))
                thumb = 'http:' + str(m.group(2))

                channel = str(m.group(3))
                htmlparser = HTMLParser()
                channel = htmlparser.unescape(channel)

                title = 'Channel\n' + channel.strip()

                self.addFolderItem(title, PATH + '?camera=%s' % url, thumb)

        xbmc.executebuiltin('Container.SetViewMode(%d)' % InfoWall)
        xbmcplugin.endOfDirectory(HANDLE)

    def play(self, url):

        url = url[6:]
        url = "http:" + urllib2.quote(url)

        xbmc.log("earthTV: play URL %s" % url, level=xbmc.LOGNOTICE)

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
                #ref found
                ref = match.group(1)
                refs = ref + '&'

                lang = ''
                loc = ''
                channel = ''
                token = ''

                s1 = 'token=(.*?)&'
                match = re.search(s1,ref + '&')
                if match is not None:
                    token = match.group(1)
                s1 = 'language=(.*?)&'
                match = re.search(s1,ref + '&')
                if match is not None:
                    lang = match.group(1)
                s1 = 'channel=(.*?)&'
                match = re.search(s1,ref + '&')
                if match is not None:
                    channel = match.group(1)
                s1 = 'location_id=(.*?)&'
                match = re.search(s1,ref + '&')
                if match is not None:
                    loc = match.group(1)


                header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
                          'Referer': ref,
                          'Origin': 'http://playercdn.earthtv.com'
                         }

                link = 'http://api.earthtv.com/v1/clips?token=' + token + '&language=' + lang + '&limit=30&channel=' + channel + '&location_id=' + loc

                r = requests.get(link, headers=header)
                if r.status_code == requests.codes.ok:
                    xbmc.log("earthTV: %s" % 'find playlist', level=xbmc.LOGNOTICE)
                    result = r.text

                    # init playlist
                    pl = xbmc.PlayList(1)
                    pl.clear()

                    jsonObj = json.loads(result)

                    for clip in jsonObj:
                        fi = clip['Files']

                        country = clip['Country']
                        city =  clip['City']
                        desc = clip['Description']
                        time = clip['LoT']
                        # 2018-02-05T19:46:22+02:00
                        dt = iso8601.parse_date(time)

                        url = ''
                        resolution = 0

                        for f in fi:
                            if 'Video' in f['Type']:
                                if(f['W']>resolution):
                                    resolution = f['W']
                                    url = 'http://cdn.earthtv.com/' + f['File'] + '?token=' + token

                        if(resolution <> 0):
                            listitem = xbmcgui.ListItem(country + '/' + city)

                            txt = country + ' / ' + city + ' '
                            txt = txt + '%02i:%02i' % (dt.hour, dt.minute)+ 'h / ' + '%02i.%02i.%04i' % (dt.day, dt.month, dt.year)
                            if desc is not None:
                                txt = txt + '\n' + desc

                            listitem.setInfo('video', { 'plot': txt })
                            listitem.setArt({'thumb': ICON})

                            #xbmc.log("earthTV: %s" % url, level=xbmc.LOGNOTICE)
                            pl.add(url, listitem)

                    if(pl.size() > 0):
                        xbmc.Player().play(pl)
                    else:
                        xbmcgui.Dialog().notification(ADDON_NAME, 'Sorry, no PLAYLIST', time=3000)


    def playLive(self, url):

        xbmc.log("earthTV: show URL %s" % url, level=xbmc.LOGNOTICE)
        xbmc.executebuiltin("ActivateWindow(busydialog)")

        url = url[6:]
        url = "https:" + urllib2.quote(url)

        #stop buffering
        xbmcgui.Window(10000).setProperty('earthURL','')
        while(xbmcgui.Window(10000).getProperty('earthSeq')<>''):
            xbmc.sleep(1000)
            xbmc.log("earthTV: wait stop stream", level=xbmc.LOGNOTICE)
            xbmcgui.Dialog().notification(ADDON_NAME, 'Stop stream', time=1100)

        xbmcgui.Dialog().notification(ADDON_NAME, 'Query link', time=1000)


        url = 'https://www.earthtv.com/de'

        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            result = r.text

            s1 = 'onEtvApiReady.*?token.*?\'(.*?)\''
            match = re.search(s1,result, re.DOTALL)
            if match is not None:
                token = match.group(1)

                xbmc.log("earthTV: token %s" % token, level=xbmc.LOGNOTICE)

                r = requests.get('https://dapi-de.earthtv.com/api/v1/media.getPlayerConfig?playerToken=' +  token)
                if r.status_code == requests.codes.ok:
                    result = r.text

                    jObj = json.loads(result)
                    playlist = jObj['streamUris']['hls']

                    xbmc.log("earthTV: playlist %s" % playlist, level=xbmc.LOGNOTICE)

                    # init playlist
                    pl = xbmc.PlayList(1)
                    pl.clear()

                    playitem = xbmcgui.ListItem(path=playlist)
                    playitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
                    playitem.setProperty('inputstream.adaptive.manifest_type', 'hls')

                    playitem.setContentLookup(False)

                    pl.add(playlist,playitem)

                    xbmc.Player().play(pl)


#### some functions ####

    def addFolderItem(self, title, url, thumb=''):
        list_item = xbmcgui.ListItem(label=title)

        list_item.setArt({'thumb': thumb,
                          'icon': thumb })

        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, True)

    def addPictureItem(self, title, url, thumb):

        list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumb)

        list_item.setArt({'thumb': thumb,
                          'icon': thumb })

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

    BASEURL='https://www.earthtv.com'

    COUNTRY = '/en/'
    if(SITE== '1'):
        COUNTRY='/de/'
    elif (SITE == '2'):
        COUNTRY='/fr/'
    elif (SITE == '3'):
        COUNTRY='/ru/'
    elif (SITE == '4'):
        COUNTRY='/ar/'

    try:
        iArchive = EarthTV()

        if PARAMS.has_key('playLive'):
            iArchive.playLive(PARAMS['playLive'][0])
        if PARAMS.has_key('play'):
            iArchive.play(PARAMS['play'][0])
        if PARAMS.has_key('camera'):
            iArchive.showCamera(PARAMS['camera'][0])
        if PARAMS.has_key('categories'):
            iArchive.showCategory(PARAMS['categories'][0])
        elif PARAMS.has_key('region'):
            iArchive.showRegion(PARAMS['region'][0],PARAMS['page'][0] )
        else:
            iArchive.showSelector()
    except Exception:
        buggalo.onExceptionRaised()
