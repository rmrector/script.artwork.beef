import json
import xbmc
import sys
from datetime import datetime, timedelta

from devhelper import pykodi, quickjson
from devhelper.pykodi import log

addon = pykodi.Addon()
sys.path.append(addon.resourcelibs)

from artworkprocessor import ArtworkProcessor

class ArtworkService(xbmc.Monitor):
    def __init__(self):
        super(ArtworkService, self).__init__()
        self.abort = False
        self.processor = ArtworkProcessor(self)
        self.autograbepisodes = [] # From setting

    @property
    def processing(self):
        return pykodi.get_conditional('StringCompare(Window(Home).Property(ArtworkBeef.Status),Processing)')

    @processing.setter
    def processing(self, value):
        if not value:
            self.abort = False
        value = 'Processing' if value else 'Idle'
        pykodi.execute_builtin('SetProperty(ArtworkBeef.Status, {0}, Home)'.format(value))

    def run(self):
        while not self.reallyWaitForAbort(10):
            pass

    def abortRequested(self):
        return self.abort or super(ArtworkService, self).abortRequested()

    def waitForAbort(self, timeout=None):
        return self.abort or super(ArtworkService, self).waitForAbort(timeout)

    def reallyWaitForAbort(self, timeout=None):
        return super(ArtworkService, self).waitForAbort(timeout)

    def onNotification(self, sender, method, data):
        if method.startswith('Other.') and sender != 'script.artwork.beef':
            return
        if method == 'Other.CancelCurrent':
            log("I'm melting!")
            self.abort = True
        elif method == 'Other.ShowProgress':
            self.showprogress()
        elif method == 'Other.ProcessNewItems':
            self.process_recentitems()
        elif method == 'Other.ProcessAllItems':
            self.process_allitems()
        elif method in ('System.OnWake', 'VideoLibrary.OnScanFinished'):
            self.processor.process_recentitems()

    def process_allitems(self):
        if self.processing:
            self.showprogress()
            return
        self.processing = True
        currentdate = str(datetime.now())
        items = quickjson.get_movies()
        serieslist = quickjson.get_tvshows()
        if self.abortRequested():
            self.processing = False
            return
        for series in serieslist:
            items.append(series)
            if self.autograbepisodes and series['imdbnumber'] in self.autograbepisodes:
                items.extend(quickjson.get_episodes_list(series['tvshowid']))
                if self.abortRequested():
                    self.processing = False
                    return

        pykodi.execute_builtin("Notification(Artwork Beef, Grabbing artwork for all {0} items, 6500, -)".format(len(items)))
        self.processor.process_medialist(items)
        if not self.abortRequested():
            addon.set_setting('lastalldate', currentdate)
            addon.set_setting('lastdate', currentdate)
        self.processing = False

    def process_recentitems(self):
        if self.processing:
            self.showprogress()
            return
        self.processing = True
        lastdate = addon.get_setting('lastdate')
        if not lastdate:
            lastdate = '0'
        currentdate = str(datetime.now())
        if lastdate > currentdate:
            lastdate = str(datetime.now() - timedelta(weeks=2))
        newitems = quickjson.get_movies('dateadded', moviefilter={'field': 'dateadded', 'operator': 'greaterthan', 'value': lastdate})
        serieslist = quickjson.get_tvshows('dateadded', seriesfilter={'field': 'dateadded', 'operator': 'greaterthan', 'value': lastdate})
        if self.abortRequested():
            self.processing = False
            return
        for series in serieslist:
            # series dateadded from Kodi is the date that the last episode was added, so I gotta check the first added episode
            firstaddedepisode = quickjson.get_episodes_list(series['tvshowid'], 'dateadded', limit=1)
            if firstaddedepisode[0]['dateadded'] > lastdate:
                newitems.append(series)
            if self.autograbepisodes and series['imdbnumber'] in self.autograbepisodes:
                newitems.extend(quickjson.get_episodes_list(series['tvshowid'], 'dateadded', episodefilter={'field': 'dateadded', 'operator': 'greaterthan', 'value': lastdate}))
            if self.abortRequested():
                self.processing = False
                return

        pykodi.execute_builtin("Notification(Artwork Beef, Grabbing artwork for {0} new items, 6500, -)".format(len(newitems)))
        self.processor.process_medialist(newitems)
        if not self.abortRequested():
            addon.set_setting('lastdate', currentdate)
        self.processing = False

    def showprogress(self):
        pykodi.execute_builtin("Notification(Artwork Beef, Currently processing artwork, 6500, -)")

if __name__ == '__main__':
    log('Service started', xbmc.LOGINFO)
    monitor = ArtworkService()
    monitor.run()
    del monitor
    log('Service stopped', xbmc.LOGINFO)
