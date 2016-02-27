import sys
import xbmc
from datetime import datetime, timedelta

if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

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
        self.serviceenabled = addon.get_setting('enableservice')
        self.abort = False
        self.processor = ArtworkProcessor(self)
        self.processed = ProcessedItems(addon.datapath)
        self.processed.load()
        self.signal = None
        self.processaftersettings = False
        self.scanning = False
        self.recentitems = {'movie': [], 'tvshow': [], 'episode': []}
        self.stoppeditem = None

    @property
    def toomany_recentitems(self):
        return len(self.recentitems['movie']) + len(self.recentitems['tvshow']) + len(self.recentitems['episode']) > 100

    @property
    def processing(self):
        return pykodi.get_conditional('StringCompare(Window(Home).Property(ArtworkBeef.Status),Processing)')

    @processing.setter
    def processing(self, value):
        self.abort = False
        value = 'Processing' if value else 'Idle'
        pykodi.execute_builtin('SetProperty(ArtworkBeef.Status, {0}, Home)'.format(value))

    def reset_recent(self):
        self.recentitems = {'movie': [], 'tvshow': [], 'episode': []}

    def run(self):
        oldsignal = 0
        clearstopped = False
        while not self.really_waitforabort(5):
            if self.stoppeditem:
                if clearstopped:
                    self.stoppeditem = None
                clearstopped = not clearstopped
            if self.scanning:
                continue
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
        elif method == 'Player.OnStop':
            data = json.loads(data)
            if self.watchitem(data):
                self.stoppeditem = (data['item']['type'], data['item']['id'])
        elif method == 'VideoLibrary.OnScanStarted':
            self.scanning = True
            if self.serviceenabled and self.processing:
                self.abort = True
        elif method == 'VideoLibrary.OnScanFinished':
            self.scanning = False
            if self.serviceenabled:
                self.signal = 'something'
        elif method == 'VideoLibrary.OnUpdate':
            if not self.serviceenabled:
                return
            data = json.loads(data)
            if not self.watchitem(data) or self.stoppeditem == (data['item']['type'], data['item']['id']):
                return
            if not self.toomany_recentitems:
                self.recentitems[data['item']['type']].append(data['item']['id'])
            if not self.scanning:
                self.signal = 'something'

    def watchitem(self, data):
        return 'item' in data and data['item'].get('id') and data['item'].get('type') in self.recentitems

    def process_something(self):
        # Three possible loops:
        # 1. Recent items, can run several times per day, after every library update, and only for small updates
        # 2. Unprocessed items, at least once every UNPROCESSED_DAYS and after larger library updates
        #  - this contains only new items that were missed in the recent loops, maybe in a shared database
        # 3. All items, once every ALLITEMS_DAYS
        #  - adds new artwork for old items missing artwork
        self.processor.progress.create("Adding extended artwork", "Listing new items")
        lastdate = addon.get_setting('lastalldate')
        if lastdate == '0':
            self.process_allitems()
            self.reset_recent()
            return
        needall = lastdate < str(datetime.now() - timedelta(days=ALLITEMS_DAYS))
        if needall:
            needunprocessed = False
        else:
            needunprocessed = self.toomany_recentitems
            if not needunprocessed:
                lastdate = addon.get_setting('lastunprocesseddate')
                needunprocessed = lastdate < str(datetime.now() - timedelta(days=UNPROCESSED_DAYS))
        if needunprocessed:
            self.process_allitems(True)
            self.reset_recent()
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

    def process_recentitems(self):
        ignoreepisodesfrom = set()
        addepisodesfrom = set()
        seriesadded = set()
        newitems = []
        for movieid in self.recentitems['movie']:
            newitems.append(quickjson.get_movie_details(movieid, movie_properties))
            if self.abortRequested():
                return
        for seriesid in self.recentitems['tvshow']:
            seriesadded.add(seriesid)
            newitems.append(quickjson.get_tvshow_details(seriesid, tvshow_properties))
            if self.abortRequested():
                return
        autoaddepisodes = addon.get_setting('autoaddepisodes_list') if addon.get_setting('episode.fanart') else ()
        for episodeid in self.recentitems['episode']:
            episode = quickjson.get_episode_details(episodeid, ['art', 'uniqueid', 'tvshowid', 'season'])
            series = None
            if episode['season'] > self.processed.tvshow.get(episode['tvshowid']) and episode['tvshowid'] not in seriesadded:
                seriesadded.add(episode['tvshowid'])
                series = quickjson.get_tvshow_details(episode['tvshowid'], tvshow_properties)
                newitems.append(series)
            if episode['tvshowid'] in addepisodesfrom:
                newitems.append(episode)
            elif episode['tvshowid'] not in ignoreepisodesfrom:
                if not series:
                    series = quickjson.get_tvshow_details(episode['tvshowid'], tvshow_properties)
                if series['imdbnumber'] in autoaddepisodes:
                    addepisodesfrom.add(episode['tvshowid'])
                    newitems.append(episode)
                else:
                    ignoreepisodesfrom.add(episode['tvshowid'])
            if self.abortRequested():
                return
        self.reset_recent()
        if newitems:
            processed = self.processor.process_medialist(newitems)
            self.processed.extend(processed)
            self.processed.save()

    def closeprogress(self):
        self.processor.progress.close()

    def onSettingsChanged(self):
        self.serviceenabled = addon.get_setting('enableservice')
        mediatypes.update_settings()
        self.processor.update_settings()
        if self.processaftersettings:
            self.processor.progress.create("Adding extended artwork", "Listing all items")
            xbmc.sleep(200)
            self.processaftersettings = False
            self.signal = 'unprocesseditems'

if __name__ == '__main__':
    log('Service started', xbmc.LOGINFO)
    ArtworkService().run()
    log('Service stopped', xbmc.LOGINFO)
