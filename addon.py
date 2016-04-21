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
PictureWrapView = 510
PictureThumbView = 514

#place holder for error message
ERROR_MESSAGE1 = 'line 1'
ERROR_MESSAGE2 = 'line 2'
ERROR_MESSAGE3 = 'line 3'

class EarthTV(object):

    def showSelector(self):
    
        xbmc.log('- main selector -')
                                      
        url="http://www.earthtv.com/en/"
        if(SITE== '1'):
            url="http://www.earthtv.com/de/"
        elif (SITE == '2'):
            url="http://www.earthtv.com/fr/"
        elif (SITE == '3'):
            url="http://www.earthtv.com/ru/"
        elif (SITE == '4'):
            url="http://www.earthtv.com/ar/"
        
        self.addPictureItem('The World LIVE', PATH + '?categories=%s' % url  + '&quality=%s' % BITR, ICON)
        
        #pDialog = xbmcgui.DialogProgressBG()
        #pDialog.create(ADDON_NAME, 'Get featured channels')
        #pDialog.update(50, ADDON_NAME)
        
        u = urllib2.urlopen(url)
        html = u.read()
        u.close()
        
        p = 0
        
        for m in re.finditer('<a.href="(?P<url>[^"]*)"><img.class="lazy".data-original="(?P<img>[^"]*)" alt="(?P<title>[^"]*)"', html, re.DOTALL):
                        
            url = 'http://www.earthtv.com' + m.group('url')
            thumb = m.group('img')
            title = m.group('title')
            
            xbmc.log (title)

            thumb = thumb.replace('//','http://')
        
            self.addPictureItem(title, PATH + '?categories=%s' % url + '&quality=%s' % BITR, thumb)
        
        xbmc.executebuiltin('Container.SetViewMode(%d)' % ThumbnailView)
        xbmcplugin.endOfDirectory(HANDLE)
        
        #pDialog.close()

    def showCategory(self, url, quality):
    
        xbmc.log('- category - ' + url + ' - ' + quality)       
        
        # ------------------ get page --------------------------
        
        u = urllib2.urlopen(url)
        html = u.read()
        u.close()

        token = ''  
        channel =''
        location =''
        
        m = None
        v = 0
        
        # ------------------ get token --------------------------

        res = re.search('webcdn.earthtv.com/player/1.4',html)
        if(res <> None):
            xbmc.log('Player V1.4 detected')
            v = 1
            m = re.search('home_url:.\'.*?\'.*?token:.\'(?P<token>[^\']*)\'.*?language:.\'(?P<language>[^\']*)\'(.*?location:.\'(?P<location>[^\']*)\')?.*?channel:.\'(?P<channel>[^\']*)\'', html, re.DOTALL)
    
        res = re.search('playerv2.earthtv.com',html)
        if(res <> None):
            xbmc.log('Player V2 detected')
            v = 2
            m = re.search('<iframe.id="player1".*?src="[^\']*token=(?P<token>[^\&]*)[^\>]*location_id=(?P<location>[^\&]*)[^\>]*channel=(?P<channel>[^\"]*)', html, re.DOTALL)

        if(m != None):
            token = m.group('token')
            channel = m.group('channel')
            location = m.group('location')
    
            xbmc.log ('Token = ' + token)
        
            if(token == ''):
                xbmcgui.Dialog().ok(ADDON_NAME, 'No token', '', '') 
                return
        
            # ------------------ get season parameter --------------------------
        
            req = urllib2.Request('http://api.earthtv.com/v1/me?token=%s' % token)
            if(v==1):
                req.add_header('Referer', 'http://webcdn.earthtv.com/player/1.40/player.html?v=1.41')
                req.add_header('Origin', 'http://webcdn.earthtv.com')
            if(v==2):    
                req.add_header('Referer', 'http://playerv2.earthtv.com/?token=%s&autoplay=true&limit=20&location_id=AMS&channel=Latest' % token) 
                req.add_header('Origin', 'http://playerv2.earthtv.com')

            req.add_header('Accept', 'application/json, text/javascript, */*; q=0.01')
            req.add_header('Accept-Encoding', 'gzip, deflate')
            req.add_header('Host', 'api.earthtv.com')

            r = urllib2.urlopen(req)
            html = r.read()
            r.close()

            xbmc.log('Received session parameter')
        
            # ------------------ get clips --------------------------
        
            getUrl = 'http://api.earthtv.com/v1/clips?token=%s' % token
            
            if(location != None):
                getUrl = getUrl + '&location_id=%s' % location
            
            getUrl = getUrl + '&channel=%s' % channel
            getUrl = getUrl + '&limit=20'
            #getUrl = getUrl + '&language=de_DE'

            req = urllib2.Request(getUrl)

            if(v==1):
                req.add_header('Referer', 'http://webcdn.earthtv.com/player/1.40/player.html?v=1.41')
                req.add_header('Origin', 'http://webcdn.earthtv.com')
            if(v==2):
                req.add_header('Referer', 'http://playerv2.earthtv.com/?token=%s' % token)
                req.add_header('Origin', 'http://playerv2.earthtv.com')

            req.add_header('Accept', 'application/json, text/javascript, */*; q=0.01')
            req.add_header('Accept-Encoding', 'gzip, deflate')
            req.add_header('Host', 'api.earthtv.com')

            r = urllib2.urlopen(req)
                        
            # load jason  
            jsonData = json.load(r, encoding='utf-8')
            r.close()
        
            # init playlist
            pl=xbmc.PlayList(1)
            pl.clear()
        
            cnt = 0
        
            for i in range (0, len(jsonData)):
                
                country = jsonData[i]['Country']
                city =  jsonData[i]['City']
                desc = jsonData[i]['Description']
            
                if(country == None):
                    country = ''
                if(city == None):
                    city=''
    
                # 2016-04-20T11:44:59+00:00
                atime = str(jsonData[i]['LoT'])
            
                month = atime[5:-18]
                day = atime[8:-15]
                hour = atime[11:-12]
                minute = atime[14:-9]
            
                monthInt = int(month)
                monthStr = calendar.month_name[monthInt] 
            
                strTime = day + '. ' + monthStr + ' / ' + hour + ':' + minute
            
                aList = jsonData[i]['Files']
                for j in range (0, len(aList)):
                    t = aList[j]['Type']
        
                    if(t == 'Video'):
                        data = str(aList[j]['File'])
                        width = str(aList[j]['W'])
                        height = str(aList[j]['H'])
                        bitrate = int(aList[j]['Bit'])
       
                        # 1920 x 1080    4   mbit
                        # 1280 x  720    1,8 mbit
                        # 640 x  480     500 - 1,8 mbit (0,55 - 0,8 - 1,8)
                    
                        if(((quality == '2') & (width == '1920')) | ((quality == '1') & (width == '1280')) | ((quality == '0') & (width == '640') & (bitrate < 700000))):  
                            cnt = cnt + 1
                            ch = channel.replace('+', ' ')
                            
                            listitem = xbmcgui.ListItem(ch + ' %s' % strTime)
                            url = 'http://cdn.earthtv.com/' + data + '?token=%s' % token
                            
                            listitem.setInfo('video', {'title': desc, 'genre': 'Webcam'})
                            
                            pl.add(url, listitem)
                    
                            #xbmc.log('Add video : %s' % bitrate)
                    
                        #xbmc.log (str(aList[j]['W']) + ' / ' + str(aList[j]['H']) + " Bitrate " + str(aList[j]['Bit']))
                    
    
        
            if(cnt != 0):
                xbmc.Player().play(pl)
            else:
                xbmcgui.Dialog().ok(ADDON_NAME, 'Nothing to play', '', '') 
        
        else:        
            xbmcgui.Dialog().ok(ADDON_NAME, 'No player found', '', '') 


#### some functions ####

    def addFolderItem(self, title, url):
        list_item = xbmcgui.ListItem(label=title)
        list_item.addContextMenuItems([ (ADDON.getLocalizedString(30160), 'Action(ParentDir)') ])
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, False)
        
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
    BITR = xbmcplugin.getSetting(HANDLE, 'maxBitrate')

try:
        iArchive = EarthTV()
            
        if PARAMS.has_key('categories'):
            iArchive.showCategory(PARAMS['categories'][0], PARAMS['quality'][0])
        else:
            iArchive.showSelector()
except Exception:
    buggalo.onExceptionRaised() 