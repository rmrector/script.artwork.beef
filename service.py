import xbmc

from lib.artworkprocessor import ArtworkProcessor
from lib.libs import mediainfo as info, mediatypes, pykodi, quickjson
from lib.libs.addonsettings import settings
from lib.libs.processeditems import ProcessedItems
from lib.libs.pykodi import log, json

STATUS_IDLE = 'idle'
STATUS_SIGNALLED = 'signalled'
STATUS_PROCESSING = 'processing'

addon = pykodi.get_main_addon()

class ArtworkService(xbmc.Monitor):
    def __init__(self):
        super(ArtworkService, self).__init__()
        self.abort = False
        self.processor = ArtworkProcessor(self)
        self.processed = ProcessedItems()
        self.processaftersettings = False
        self.recentitems = {'movie': [], 'tvshow': [], 'episode': []}
        self.stoppeditems = set()
        self._signal = None
        self._status = None
        self._last_itemupdate = addon.get_setting('last_itemupdate')
        self.status = STATUS_IDLE

    @property
    def scanning(self):
        return pykodi.get_conditional('Library.IsScanningVideo | Library.IsScanningMusic')

    @property
    def last_itemupdate(self):
        return self._last_itemupdate

    @last_itemupdate.setter
    def last_itemupdate(self, value):
        addon.set_setting('last_itemupdate', value)
        self._last_itemupdate = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        self.abort = False
        pykodi.execute_builtin('SetProperty(ArtworkBeef.Status, {0}, Home)'.format(value))

    @property
    def signal(self):
        return self._signal

    @signal.setter
    def signal(self, value):
        self._signal = value
        self.status = STATUS_SIGNALLED if value else STATUS_IDLE

    def reset_recent(self):
        self.recentitems = {'movie': [], 'tvshow': [], 'episode': []}

    def run(self):
        while not self.really_waitforabort(5):
            if self.scanning:
                continue
            if self.signal:
                signal = self.signal
                self._signal = None
                if signal == 'recentitems':
                    # Add a delay to catch rapid fire VideoLibrary.OnUpdate
                    self.signal = 'recentitems_really'
                    continue
                self.status = STATUS_PROCESSING
                if signal == 'allitems':
                    self.process_allitems()
                elif signal == 'unprocesseditems':
                    self.process_unprocesseditems()
                elif signal == 'olditems':
                    if self.process_oldandunprocesseditems():
                        self.last_itemupdate = get_date()
                elif signal == 'recentitems_really':
                    self.process_recentitems()
                self.status = STATUS_IDLE

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
            if self.status == STATUS_PROCESSING:
                self.abort = True
            elif self.signal:
                self.signal = None
                self.processor.close_progress()
        elif method == 'Other.ProcessUnprocessedItems':
            self.processor.create_progress()
            self.signal = 'unprocesseditems'
        elif method == 'Other.ProcessOldItems':
            self.processor.create_progress()
            self.signal = 'olditems'
        elif method == 'Other.ProcessAllItems':
            self.processor.create_progress()
            self.signal = 'allitems'
        elif method == 'Other.ProcessAfterSettings':
            self.processaftersettings = True
        elif method == 'Player.OnStop':
            if settings.enableservice:
                data = json.loads(data)
                if self.watchitem(data):
                    self.stoppeditems.add((data['item']['type'], data['item']['id']))
        elif method == 'VideoLibrary.OnScanStarted':
            if settings.enableservice and self.status == STATUS_PROCESSING:
                self.abort = True
        elif method == 'VideoLibrary.OnScanFinished':
            if settings.enableservice:
                scan_olditems = settings.enable_olditem_updates and get_date() > self.last_itemupdate
                self.signal = 'olditems' if scan_olditems else 'unprocesseditems'
        elif method == 'VideoLibrary.OnUpdate':
            if not settings.enableservice:
                return
            data = json.loads(data)
            if not self.watchitem(data):
                return
            if (data['item']['type'], data['item']['id']) in self.stoppeditems:
                self.stoppeditems.remove((data['item']['type'], data['item']['id']))
                return
            if not self.scanning:
                self.recentitems[data['item']['type']].append(data['item']['id'])
                self.signal = 'recentitems'

    def watchitem(self, data):
        can_use_data = 'item' in data and data['item'].get('id') and data['item'].get('id') != -1
        return can_use_data and 'playcount' not in data and data['item'].get('type') in self.recentitems

    def process_unprocesseditems(self):
        return self.process_allitems(self.processed.does_not_exist)

    def process_oldandunprocesseditems(self):
        return self.process_allitems(self.processed.is_stale)

    def process_allitems(self, shouldinclude_fn=None):
        allitems = False
        if not shouldinclude_fn:
            allitems = True
            shouldinclude_fn = lambda id, type, label: True
        items = [info.MediaItem(movie) for movie in quickjson.get_movies() if shouldinclude_fn(movie['movieid'], mediatypes.MOVIE, movie['label'])]
        items.extend([info.MediaItem(mset) for mset in quickjson.get_moviesets()
            if shouldinclude_fn(mset['setid'], mediatypes.MOVIESET, mset['label'])])

        serieslist = quickjson.get_tvshows()
        if self.abortRequested():
            return False
        serieseps_added = set()
        for series in serieslist:
            processed_season = self.processed.get_data(series['tvshowid'], mediatypes.TVSHOW)
            if not processed_season or series['season'] > int(processed_season) or \
                    shouldinclude_fn(series['tvshowid'], mediatypes.TVSHOW, series['label']):
                items.append(info.MediaItem(series))
                if series['imdbnumber'] not in settings.autoadd_episodes and not allitems:
                    for episode in quickjson.get_episodes(series['tvshowid']):
                        if info.has_generated_thumbnail(episode):
                            ep = info.MediaItem(episode)
                            ep.skip_artwork = ['fanart']
                            items.append(ep)
                    serieseps_added.add(series['tvshowid'])
            if series['imdbnumber'] in settings.autoadd_episodes and series['tvshowid'] not in serieseps_added:
                episodes = quickjson.get_episodes(series['tvshowid'])
                items.extend(info.MediaItem(ep) for ep in episodes if shouldinclude_fn(ep['episodeid'], mediatypes.EPISODE, ep['label']))
                serieseps_added.add(series['tvshowid'])
            if self.abortRequested():
                return False
        if settings.generate_episode_thumb:
            # Too many to get all of them, and filtering by a specific date for dateadded isn't much better
            for episode in quickjson.get_episodes() if allitems else quickjson.get_episodes(limit=500):
                if episode['tvshowid'] not in serieseps_added and not info.has_generated_thumbnail(episode):
                    ep = info.MediaItem(episode)
                    ep.skip_artwork = ['fanart']
                    items.append(ep)
        self.reset_recent()
        return self.processor.process_medialist(items)

    def process_recentitems(self):
        ignoreepisodesfrom = set()
        addepisodesfrom = set()
        seriesadded = set()
        newitems = []
        for movieid in self.recentitems['movie']:
            newitems.append(quickjson.get_item_details(movieid, mediatypes.MOVIE))
            if self.abortRequested():
                return
        for seriesid in self.recentitems['tvshow']:
            seriesadded.add(seriesid)
            newitems.append(quickjson.get_item_details(seriesid, mediatypes.TVSHOW))
            if self.abortRequested():
                return
        for episodeid in self.recentitems['episode']:
            episode = quickjson.get_item_details(episodeid, mediatypes.EPISODE)
            series = None
            if episode['tvshowid'] not in seriesadded and (episode['season'] >
                    self.processed.get_data(episode['tvshowid'], mediatypes.TVSHOW)):
                seriesadded.add(episode['tvshowid'])
                series = quickjson.get_item_details(episode['tvshowid'], mediatypes.TVSHOW)
                newitems.append(series)
            if episode['tvshowid'] in addepisodesfrom:
                newitems.append(episode)
            elif episode['tvshowid'] in ignoreepisodesfrom:
                if settings.generate_episode_thumb:
                    episode['skip'] = ['fanart']
                    newitems.append(episode)
            else:
                if not series:
                    series = quickjson.get_item_details(episode['tvshowid'], mediatypes.TVSHOW)
                if series['imdbnumber'] in settings.autoadd_episodes:
                    addepisodesfrom.add(episode['tvshowid'])
                    newitems.append(episode)
                else:
                    ignoreepisodesfrom.add(episode['tvshowid'])
                    if settings.generate_episode_thumb:
                        episode['skip'] = ['fanart']
                        newitems.append(episode)
            if self.abortRequested():
                return

        self.reset_recent()
        self.processor.process_medialist(newitems)

    def onSettingsChanged(self):
        settings.update_settings()
        mediatypes.update_settings()
        if self.processaftersettings:
            self.processor.create_progress()
            xbmc.sleep(200)
            self.processaftersettings = False
            self.signal = 'unprocesseditems'

def get_date():
    return pykodi.get_infolabel('System.Date(yyyy-mm-dd)')

if __name__ == '__main__':
    log('Service started', xbmc.LOGINFO)
    ArtworkService().run()
    log('Service stopped', xbmc.LOGINFO)
