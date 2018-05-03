# -*- coding: UTF-8 -*-

import os,time

import xbmc
import xbmcgui
import xbmcplugin, xbmcaddon
import xbmcvfs

import re
import requests

if __name__ == '__main__':
    monitor = xbmc.Monitor()

    # get profile path
    __addon = xbmcaddon.Addon()
    __profilePath = xbmc.translatePath(__addon.getAddonInfo('profile')).decode("utf-8")
    if not xbmcvfs.exists(__profilePath): xbmcvfs.mkdirs(__profilePath)

    #set video path
    __videoPath = os.path.join(__profilePath, "video.ts")

    while not monitor.abortRequested():
        # Sleep/wait for abort for 1 second
        if monitor.waitForAbort(1):
            # Abort was requested while waiting. We should exit
            break

        # get parameter
        url = xbmcgui.Window(10000).getProperty('earthURL')
        ref = xbmcgui.Window(10000).getProperty('earthRef')
        start = xbmcgui.Window(10000).getProperty('earthSeq')

        actual = start

        # check if we need to start dl
        if(url <> '') and (start<>''):
            end = int(start) + 30
            xbmc.log("earthTV: %s" % 'start dl video', level=xbmc.LOGNOTICE)

            with open(__videoPath, 'wb') as out_file:

                header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
                          'Referer': ref,
                          'Origin': 'http://playercdn.earthtv.com'}

                stop = False

                while not stop:
                    actURL = url.replace(str(start),str(actual))
                    actNo = int(actual)

                    xbmc.log("earthTV: %s" % 'dl video chunk ' + str(actNo), level=xbmc.LOGNOTICE)
                    #dl = 'http://cdn.liveonearth.com/cdnedge/smil:TWL-en.smil/' + actURL

                    r = requests.get(actURL, headers=header)
                    if r.status_code == requests.codes.ok:
                        # OK, then get next chunk
                        out_file.write(r.content)
                        actNo = actNo + 1
                        actual = str(actNo)
                        if monitor.waitForAbort(1):
                            # Abort was requested while waiting. We should exit
                            break
                    else:
                        # NOK, we are too fast
                        if monitor.waitForAbort(6):
                            # Abort was requested while waiting. We should exit
                            break

                    # end reached
                    if(actNo >= end):
                        xbmc.log("earthTV: %s" % 'end buffering', level=xbmc.LOGNOTICE)
                        xbmcgui.Window(10000).setProperty('earthSeq', '')
                        stop = True

                    # stop stream
                    url = xbmcgui.Window(10000).getProperty('earthURL')
                    if(url == ''):
                        xbmc.log("earthTV: %s" % 'stop buffering', level=xbmc.LOGNOTICE)
                        xbmcgui.Window(10000).setProperty('earthSeq', '')
                        stop = True









