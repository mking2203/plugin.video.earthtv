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
        
        xbmc.executebuiltin('Container.SetViewMode(%d)' % ThumbnailView)
        xbmcplugin.endOfDirectory(HANDLE)

    def showCategory(self, url):
    
        url = url[5:]   
        url = "http:" + urllib2.quote(url)
        
        xbmc.log('- category - ' + url) 
        
        u = urllib2.urlopen(url)
        html = u.read()
        u.close()
        
        m = re.search('<iframe.id="player1"[^>]*src="[^\"]*token=(?P<token>[^&]*)[^\"]*channel=(?P<channel>[^&]*)[^\"]*livesd=(?P<url>[^&\"]*)', html) 
        if(m != None): 
            token = m.group('token')
            channel = m.group('channel')
            url = m.group('url')
                         
            listitem =xbmcgui.ListItem (channel)
            listitem.setInfo('video', {'Title': channel})
             
            xbmc.log('- file - ' + url) 
            
            xbmc.Player().play(url, listitem)
        else:
            xbmcgui.Dialog().ok(ADDON_NAME, 'Nothing to play', '', '') 
        
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