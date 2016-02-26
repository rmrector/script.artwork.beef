import xbmc
import sys
from datetime import datetime, timedelta

from devhelper import pykodi, quickjson
from devhelper.pykodi import log

addon = pykodi.get_main_addon()
sys.path.append(addon.resourcelibs)

from artworkprocessor import ArtworkProcessor, episode_properties, movie_properties, tvshow_properties
from processeditems import ProcessedItems
import mediatypes

UNPROCESSED_DAYS = 2
ALLITEMS_DAYS = 60

class ArtworkService(xbmc.Monitor):
    def __init__(self):
        super(ArtworkService, self).__init__()
        self.abort = False
        self.processor = ArtworkProcessor(self)
        self.processed = ProcessedItems(addon.datapath)
        self.processed.load()
        self.signal = None
        self.processaftersettings = False

    @property
    def processing(self):
        return pykodi.get_conditional('StringCompare(Window(Home).Property(ArtworkBeef.Status),Processing)')

    @processing.setter
    def processing(self, value):
        self.abort = False
        value = 'Processing' if value else 'Idle'
        pykodi.execute_builtin('SetProperty(ArtworkBeef.Status, {0}, Home)'.format(value))

    def run(self):
        oldsignal = 0
        while not self.really_waitforabort(5):
            if self.signal and not self.processing:
                signal = self.signal
                self.signal = None
                oldsignal = 0
                if signal == 'something':
                    # Add a delay to catch rapid fire library updates
                    self.signal = 'something_really'
                    continue
                self.processing = True
                if signal == 'allitems':
                    self.process_allitems()
                elif signal == 'unprocesseditems':
                    self.process_allitems(True)
                elif signal == 'something_really':
                    self.process_something()
                self.processing = False
                self.closeprogress()
            elif self.signal:
                oldsignal += 1
                if oldsignal > 3:
                    log("An old signal '{0}' had to be put down before the processor would give up, something is probably wrong".format(self.signal), xbmc.LOGWARNING)
                    self.signal = None
                    oldsignal = 0

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
            if self.processing:
                self.abort = True
        elif method == 'Other.ProcessNewItems':
            self.processor.progress.create("Adding extended artwork", "Listing all items")
            if addon.get_setting('lastalldate') == '0':
                self.signal = 'allitems'
            else:
                self.signal = 'unprocesseditems'
        elif method == 'Other.ProcessAllItems':
            self.processor.progress.create("Adding extended artwork", "Listing all items")
            self.signal = 'allitems'
        elif method == 'Other.ProcessAfterSettings':
            self.processaftersettings = True
        elif method == 'VideoLibrary.OnScanStarted':
            if addon.get_setting('enableservice') and self.processing:
                self.abort = True
        elif method == 'VideoLibrary.OnScanFinished':
            if addon.get_setting('enableservice'):
                self.signal = 'something'

    def process_something(self):
        # Three possible loops:
        # Recent items, filtering on Kodi dateadded - Runs several times per day, after every library update
        # - dateadded is typically based on file date, not date item was added to Kodi library, so this can miss items
        # Unprocessed items, list all items from Kodi then filter out already processed items - Once per week (UNPROCESSED_DAYS)
        # - this contains only new items that were missed in the recent loops
        # All items, process all configured media items in Kodi - Once every 2 months (ALLITEMS_DAYS)
        # - to add any new artwork for old items that don't already have all artwork
        self.processor.progress.create("Adding extended artwork", "Listing new items")
        if addon.get_setting('lastalldate') == '0':
            self.process_allitems()
            return
        lastdate = addon.get_setting('lastalldate')
        needall = lastdate < str(datetime.now() - timedelta(days=ALLITEMS_DAYS))
        if needall:
            needunprocessed = False
        else:
            lastdate = addon.get_setting('lastunprocesseddate')
            needunprocessed = lastdate < str(datetime.now() - timedelta(days=UNPROCESSED_DAYS))
        if needunprocessed:
            self.process_allitems(True)
            return

        self.process_recentitems()
        if not self.abortRequested() and needall:
            self.process_allitems()

    def process_allitems(self, excludeprocessed=False):
        currentdate = str(datetime.now())
        items = quickjson.get_movies(properties=movie_properties)
        if excludeprocessed:
            items = [movie for movie in items if movie['movieid'] not in self.processed.movie]
        serieslist = quickjson.get_tvshows(properties=tvshow_properties)
        if self.abortRequested():
            return
        autoaddepisodes = addon.get_setting('autoaddepisodes_list') if addon.get_setting('episode.fanart') else ()
        for series in serieslist:
            if not excludeprocessed or series['season'] > self.processed.tvshow.get(series['tvshowid']):
                items.append(series)
            if series['imdbnumber'] in autoaddepisodes:
                episodes = quickjson.get_episodes(series['tvshowid'], 'dateadded', properties=episode_properties)
                for episode in episodes:
                    if not excludeprocessed or episode['episodeid'] not in self.processed.episode:
                        items.append(episode)
            if self.abortRequested():
                return
        if items:
            processed = self.processor.process_medialist(items)
            if not excludeprocessed:
                self.processed.set(processed)
                addon.set_setting('lastalldate', currentdate)
            else:
                self.processed.extend(processed)
            self.processed.save()
        if not self.abortRequested():
            addon.set_setting('lastunprocesseddate', currentdate)
            addon.set_setting('lastdate', currentdate)

    def process_recentitems(self):
        lastdate = addon.get_setting('lastdate')
        currentdate = str(datetime.now())
        if lastdate > currentdate:
            lastdate = str(datetime.now() - timedelta(weeks=2))
        newitems = quickjson.get_movies('dateadded', properties=movie_properties, moviefilter={'field': 'dateadded', 'operator': 'greaterthan', 'value': lastdate})
        serieslist = quickjson.get_tvshows('dateadded', properties=tvshow_properties, seriesfilter={'field': 'dateadded', 'operator': 'greaterthan', 'value': lastdate})
        if self.abortRequested():
            return
        autoaddepisodes = addon.get_setting('autoaddepisodes_list') if addon.get_setting('episode.fanart') else ()
        for series in serieslist:
            if series['season'] > self.processed.tvshow.get(series['tvshowid']):
                newitems.append(series)
            if series['imdbnumber'] in autoaddepisodes:
                newitems.extend(quickjson.get_episodes(series['tvshowid'], 'dateadded', properties=episode_properties, episodefilter={'field': 'dateadded', 'operator': 'greaterthan', 'value': lastdate}))
            if self.abortRequested():
                return

        if newitems:
            processed = self.processor.process_medialist(newitems)
            self.processed.extend(processed)
            self.processed.save()
        if not self.abortRequested():
            addon.set_setting('lastdate', currentdate)

    def closeprogress(self):
        self.processor.progress.close()

    def onSettingsChanged(self):
        mediatypes.update_settings()
        self.processor.update_settings()
        if self.processaftersettings:
            self.processor.progress.create("Adding extended artwork", "Listing all items")
            xbmc.sleep(200)
            self.processaftersettings = False
            self.signal = 'unprocesseditems'

if __name__ == '__main__':
    log('Service started', xbmc.LOGINFO)
    monitor = ArtworkService()
    monitor.run()
    del monitor
    log('Service stopped', xbmc.LOGINFO)
