import xbmc
from datetime import timedelta

from lib.artworkprocessor import ArtworkProcessor
from lib.libs import mediatypes, pykodi, quickjson
from lib.libs.processeditems import ProcessedItems
from lib.libs.pykodi import log, datetime_now, json
from lib.maintenance import check_upgrades

STATUS_IDLE = 'idle'
STATUS_SIGNALLED = 'signalled'
STATUS_PROCESSING = 'processing'

UNPROCESSED_DAYS = 1

addon = pykodi.get_main_addon()

class ArtworkService(xbmc.Monitor):
    def __init__(self):
        super(ArtworkService, self).__init__()
        self.serviceenabled = addon.get_setting('enableservice')
        self.only_filesystem = addon.get_setting('only_filesystem')
        self.abort = False
        self.processor = ArtworkProcessor(self)
        self.processed = ProcessedItems()
        self.signal = None
        self.processaftersettings = False
        self.recentitems = {'movie': [], 'tvshow': [], 'episode': []}
        self.stoppeditems = set()
        self.set_status(STATUS_IDLE)

    @property
    def toomany_recentitems(self):
        return len(self.recentitems['movie']) + len(self.recentitems['tvshow']) + len(self.recentitems['episode']) > 100

    @property
    def scanning(self):
        return pykodi.get_conditional('Library.IsScanningVideo | Library.IsScanningMusic')

    def set_status(self, value):
        self.abort = False
        self.status = value
        pykodi.execute_builtin('SetProperty(ArtworkBeef.Status, {0}, Home)'.format(value))

    def set_signal(self, value):
        self.set_status(STATUS_SIGNALLED if value else STATUS_IDLE)
        self.signal = value

    def reset_recent(self):
        self.recentitems = {'movie': [], 'tvshow': [], 'episode': []}

    def run(self):
        check_upgrades()
        while not self.really_waitforabort(5):
            if self.scanning:
                continue
            if self.signal:
                signal = self.signal
                self.signal = None
                if signal == 'something':
                    # Add a delay to catch rapid fire library updates
                    self.signal = 'something_really'
                    continue
                self.set_status(STATUS_PROCESSING)
                if signal == 'allitems':
                    self.process_allitems()
                elif signal == 'unprocesseditems':
                    self.process_allitems(True)
                elif signal == 'something_really':
                    self.process_something()
                self.set_status(STATUS_IDLE)

    def abortRequested(self):
        return self.abort or super(ArtworkService, self).abortRequested()

    def waitForAbort(self, timeout=None):
        return self.abort or super(ArtworkService, self).waitForAbort(timeout)

    def really_waitforabort(self, timeout=None):
        return super(ArtworkService, self).waitForAbort(timeout)

    def onNotification(self, sender, method, data):
        if method.startswith('Other.'):
            if sender == 'script.artwork.beef':
                message = 'Received notification "{0}"'.format(method)
                if data != 'null':
                    message += " - data:\n" + data
                log(message, xbmc.LOGINFO)
            else:
                return
        if method == 'Other.CancelCurrent':
            if self.status == STATUS_PROCESSING:
                self.abort = True
            elif self.signal:
                self.set_signal(None)
                self.processor.close_progress()
        elif method == 'Other.ProcessNewItems':
            self.processor.create_progress()
            self.set_signal('unprocesseditems')
        elif method == 'Other.ProcessAllItems':
            self.processor.create_progress()
            self.set_signal('allitems')
        elif method == 'Other.ProcessAfterSettings':
            self.processaftersettings = True
        elif method == 'Player.OnStop':
            if self.serviceenabled:
                data = json.loads(data)
                if self.watchitem(data):
                    self.stoppeditems.add((data['item']['type'], data['item']['id']))
        elif method == 'VideoLibrary.OnScanStarted':
            if self.serviceenabled and self.status == STATUS_PROCESSING:
                self.abort = True
        elif method == 'VideoLibrary.OnScanFinished':
            if self.serviceenabled:
                self.set_signal('something')
        elif method == 'VideoLibrary.OnUpdate':
            if not self.serviceenabled:
                return
            data = json.loads(data)
            if not self.watchitem(data):
                return
            if (data['item']['type'], data['item']['id']) in self.stoppeditems:
                self.stoppeditems.remove((data['item']['type'], data['item']['id']))
                return
            if not self.toomany_recentitems:
                self.recentitems[data['item']['type']].append(data['item']['id'])
            if not self.scanning:
                self.set_signal('something')

    def watchitem(self, data):
        usabledata = 'item' in data and data['item'].get('id') and data['item'].get('id') != -1
        return usabledata and 'playcount' not in data and data['item'].get('type') in self.recentitems

    def process_something(self):
        # 1. Recent items, can run several times per day, after every library update, and only for small updates
        # 2. Deep dive, at least once every UNPROCESSED_DAYS and after larger library updates
        #  - this contains new items that were missed in the recent loops, maybe in a shared database
        #    and items that are due to be rechecked for artwork
        lastdate = addon.get_setting('lastdate')
        if self.toomany_recentitems or lastdate < str(datetime_now() - timedelta(days=UNPROCESSED_DAYS)):
            self.process_allitems(True)
            self.reset_recent()
        else:
            self.process_recentitems()

    def process_allitems(self, excludeprocessed=False):
        currentdate = str(datetime_now())
        items = quickjson.get_movies()
        sets = quickjson.get_moviesets()
        if excludeprocessed:
            items = [movie for movie in items if self.processed.should_update(movie['movieid'], mediatypes.MOVIE)]
            sets = [mset for mset in sets if self.processed.should_update(mset['setid'], mediatypes.MOVIESET)]
        items.extend(sets)
        serieslist = quickjson.get_tvshows()
        if self.abortRequested():
            return
        autoaddepisodes = addon.get_setting('autoaddepisodes_list') if addon.get_setting('episode.fanart') else ()
        for series in serieslist:
            pseason = self.processed.get_data(series['tvshowid'], mediatypes.TVSHOW)
            if not excludeprocessed or self.processed.should_update(series['tvshowid'], mediatypes.TVSHOW) or \
                    not pseason or series['season'] > int(pseason):
                items.append(series)
            if series['imdbnumber'] in autoaddepisodes:
                episodes = quickjson.get_episodes(series['tvshowid'])
                if not excludeprocessed:
                    items.extend(episodes)
                else:
                    items.extend(ep for ep in episodes if self.processed.should_update(ep['episodeid'], mediatypes.EPISODE))
            if self.abortRequested():
                return

        self.processor.process_medialist(items)
        if not self.abortRequested():
            addon.set_setting('lastdate', currentdate)

    def process_recentitems(self):
        ignoreepisodesfrom = set()
        addepisodesfrom = set()
        seriesadded = set()
        newitems = []
        for movieid in self.recentitems['movie']:
            newitems.append(quickjson.get_movie_details(movieid))
            if self.abortRequested():
                return
        for seriesid in self.recentitems['tvshow']:
            seriesadded.add(seriesid)
            newitems.append(quickjson.get_tvshow_details(seriesid))
            if self.abortRequested():
                return
        autoaddepisodes = addon.get_setting('autoaddepisodes_list') if addon.get_setting('episode.fanart') else ()
        for episodeid in self.recentitems['episode']:
            episode = quickjson.get_episode_details(episodeid)
            series = None
            if episode['tvshowid'] not in seriesadded and (episode['season'] >
                    self.processed.get_data(episode['tvshowid'], mediatypes.TVSHOW)):
                seriesadded.add(episode['tvshowid'])
                series = quickjson.get_tvshow_details(episode['tvshowid'])
                newitems.append(series)
            if episode['tvshowid'] in addepisodesfrom:
                newitems.append(episode)
            elif episode['tvshowid'] not in ignoreepisodesfrom:
                if not series:
                    series = quickjson.get_tvshow_details(episode['tvshowid'])
                if series['imdbnumber'] in autoaddepisodes:
                    addepisodesfrom.add(episode['tvshowid'])
                    newitems.append(episode)
                else:
                    ignoreepisodesfrom.add(episode['tvshowid'])
            if self.abortRequested():
                return

        self.reset_recent()
        self.processor.process_medialist(newitems)

    def onSettingsChanged(self):
        self.serviceenabled = addon.get_setting('enableservice')
        self.only_filesystem = addon.get_setting('only_filesystem')
        mediatypes.update_settings()
        self.processor.update_settings()
        if self.processaftersettings:
            self.processor.create_progress()
            xbmc.sleep(200)
            self.processaftersettings = False
            self.set_signal('unprocesseditems')

if __name__ == '__main__':
    log('Service started', xbmc.LOGINFO)
    ArtworkService().run()
    log('Service stopped', xbmc.LOGINFO)
