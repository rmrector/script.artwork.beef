import xbmc
import sys
from datetime import datetime, timedelta

from devhelper import pykodi, quickjson
from devhelper.pykodi import log

addon = pykodi.Addon()
sys.path.append(addon.resourcelibs)

from artworkprocessor import ArtworkProcessor
from processeditems import ProcessedItems

UNPROCESSED_WEEKS = 1
ALLITEMS_WEEKS = 8

class ArtworkService(xbmc.Monitor):
    def __init__(self):
        super(ArtworkService, self).__init__()
        self.abort = False
        self.processor = ArtworkProcessor(self)
        self.autograbepisodes = [] # From setting
        self.processed = ProcessedItems(addon.datapath)
        self.processed.load()
        self.signal = None

    @property
    def processing(self):
        return pykodi.get_conditional('StringCompare(Window(Home).Property(ArtworkBeef.Status),Processing)')

    @processing.setter
    def processing(self, value):
        self.abort = False
        value = 'Processing' if value else 'Idle'
        pykodi.execute_builtin('SetProperty(ArtworkBeef.Status, {0}, Home)'.format(value))

    def run(self):
        while not self.really_waitforabort(5):
            if self.signal:
                if not self.processing:
                    signal = self.signal
                    self.signal = None
                    self.processing = True
                    if signal == 'allitems':
                        self.process_allitems()
                    elif signal == 'recentitems':
                        self.process_recentitems()
                    elif signal == 'something':
                        self.process_something()
                    self.processing = False
                else:
                    self.signal = None
                    self.showprogress()

    def abortRequested(self):
        return self.abort or super(ArtworkService, self).abortRequested()

    def waitForAbort(self, timeout=None):
        return self.abort or super(ArtworkService, self).waitForAbort(timeout)

    def really_waitforabort(self, timeout=None):
        return super(ArtworkService, self).waitForAbort(timeout)

    def onNotification(self, sender, method, data):
        if method.startswith('Other.') and sender != 'script.artwork.beef':
            return
        if method == 'Other.CancelCurrent':
            if self.processing():
                self.abort = True
        elif method == 'Other.ShowProgress':
            self.showprogress()
        elif method == 'Other.ProcessNewItems':
            if addon.get_setting('lastdate') == '0':
                self.signal = 'allitems'
            else:
                self.signal = 'recentitems'
        elif method == 'Other.ProcessAllItems':
            self.signal = 'allitems'
        elif method == 'VideoLibrary.OnScanFinished':
            if addon.get_setting('enableservice'):
                if self.processing:
                    self.abort = True
                self.signal = 'something'

    def process_something(self):
        # Three possible loops:
        # Recent items, filtering on Kodi dateadded - Runs several times per day, after every library update
        # - dateadded is typically based on file date, not date item was added to Kodi library, so this can miss items
        # Unprocessed items, grab all items from Kodi then filter out already processed items - Once per week (UNPROCESSED_WEEKS)
        # - this contains only new items that were missed in the recent loops
        # All items, grab all items from Kodi, and process every single one of them - Once every 2 months (ALLITEMS_WEEKS)
        # - to grab any new artwork for old items that don't already have all artwork
        if addon.get_setting('lastdate') == '0':
            self.process_allitems()
            return
        lastdate = addon.get_setting('lastalldate')
        needall = lastdate < str(datetime.now() - timedelta(weeks=ALLITEMS_WEEKS))
        if needall:
            needunprocessed = False
        else:
            lastdate = addon.get_setting('lastunprocesseddate')
            needunprocessed = lastdate < str(datetime.now() - timedelta(weeks=UNPROCESSED_WEEKS))
        if needunprocessed:
            self.process_allitems(True)
            return

        self.process_recentitems()
        if not self.abortRequested() and needall:
            self.process_allitems()

    def process_allitems(self, excludeprocessed=False):
        pykodi.execute_builtin("Notification(Artwork Beef, Listing all media items, 5500, -)")
        currentdate = str(datetime.now())
        if not excludeprocessed:
            items = quickjson.get_movies()
        else:
            items = [movie for movie in quickjson.get_movies() if movie['movieid'] not in self.processed.movie]
        serieslist = quickjson.get_tvshows()
        if self.abortRequested():
            return
        for series in serieslist:
            if not excludeprocessed or series['tvshowid'] not in self.processed.tvshow:
                items.append(series)
            if self.autograbepisodes and series['imdbnumber'] in self.autograbepisodes:
                episodes = quickjson.get_episodes_list(series['tvshowid'])
                if not excludeprocessed:
                    items.extend(episodes)
                else:
                    items.extend((episode for episode in episodes if episode['dbid'] not in self.processed.episode))
                if self.abortRequested():
                    return
        if self.abortRequested():
            return
        if items:
            message = "Grabbing artwork for all {0} items" if not excludeprocessed else "Grabbing artwork for {0} unprocessed items"
            pykodi.execute_builtin("Notification(Artwork Beef, {0}, 6500, -)".format(message.format(len(items))))
            processed = self.processor.process_medialist(items)
            if not excludeprocessed:
                self.processed.set(processed)
                addon.set_setting('lastalldate', currentdate)
            else:
                self.processed.extend(processed)
            self.processed.save()
        else:
            pykodi.execute_builtin("Notification(Artwork Beef, No unprocessed items need artwork, 6500, -)")
        if not self.abortRequested():
            addon.set_setting('lastunprocesseddate', currentdate)
            addon.set_setting('lastdate', currentdate)

    def process_recentitems(self):
        pykodi.execute_builtin("Notification(Artwork Beef, Listing new media items, 5500, -)")
        lastdate = addon.get_setting('lastdate')
        currentdate = str(datetime.now())
        if lastdate > currentdate:
            lastdate = str(datetime.now() - timedelta(weeks=2))
        newitems = quickjson.get_movies('dateadded', moviefilter={'field': 'dateadded', 'operator': 'greaterthan', 'value': lastdate})
        serieslist = quickjson.get_tvshows('dateadded', seriesfilter={'field': 'dateadded', 'operator': 'greaterthan', 'value': lastdate})
        if self.abortRequested():
            return
        for series in serieslist:
            # series dateadded from Kodi is the date that the last episode was added, so I gotta check the first added episode
            firstaddedepisode = quickjson.get_episodes_list(series['tvshowid'], 'dateadded', limit=1)
            if firstaddedepisode[0]['dateadded'] > lastdate:
                newitems.append(series)
            if self.autograbepisodes and series['imdbnumber'] in self.autograbepisodes:
                newitems.extend(quickjson.get_episodes_list(series['tvshowid'], 'dateadded', episodefilter={'field': 'dateadded', 'operator': 'greaterthan', 'value': lastdate}))
            if self.abortRequested():
                return

        if newitems:
            pykodi.execute_builtin("Notification(Artwork Beef, Grabbing artwork for {0} new items, 6500, -)".format(len(newitems)))
            processed = self.processor.process_medialist(newitems)
            self.processed.extend(processed)
            self.processed.save()
        else:
            pykodi.execute_builtin("Notification(Artwork Beef, No new items need artwork, 6500, -)")
        if not self.abortRequested():
            addon.set_setting('lastdate', currentdate)

    def showprogress(self):
        pykodi.execute_builtin("Notification(Artwork Beef, Currently processing artwork, 6500, -)")

if __name__ == '__main__':
    log('Service started', xbmc.LOGINFO)
    monitor = ArtworkService()
    monitor.run()
    del monitor
    log('Service stopped', xbmc.LOGINFO)
