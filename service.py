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
        self.recentvideos = {'movie': [], 'tvshow': [], 'episode': [], 'musicvideo': []}
        self.stoppeditems = set()
        self._signal = None
        self._status = None
        self._last_videoupdate = addon.get_setting('last_videoupdate')
        self._last_musicupdate = addon.get_setting('last_musicupdate')
        self.status = STATUS_IDLE

    @property
    def scanning(self):
        return pykodi.get_conditional('Library.IsScanningVideo | Library.IsScanningMusic')

    @property
    def last_videoupdate(self):
        return self._last_videoupdate

    @last_videoupdate.setter
    def last_videoupdate(self, value):
        addon.set_setting('last_videoupdate', value)
        self._last_videoupdate = value

    @property
    def last_musicupdate(self):
        return self._last_musicupdate

    @last_musicupdate.setter
    def last_musicupdate(self, value):
        addon.set_setting('last_musicupdate', value)
        self._last_musicupdate = value

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
        self.recentvideos = {'movie': [], 'tvshow': [], 'episode': [], 'musicvideo': []}

    def run(self):
        while not self.really_waitforabort(5):
            if self.scanning:
                continue
            if self.signal:
                signal = self.signal
                self._signal = None
                if signal == 'recentvideos':
                    # Add a delay to catch rapid fire VideoLibrary.OnUpdate
                    self.signal = 'recentvideos_really'
                    continue
                self.status = STATUS_PROCESSING
                if signal == 'allvideos':
                    self.process_allvideos()
                elif signal == 'unprocessedvideos':
                    self.process_allvideos(self.processed.does_not_exist)
                elif signal == 'oldvideos':
                    if self.process_allvideos(self.processed.is_stale):
                        self.last_videoupdate = get_date()
                elif signal == 'recentvideos_really':
                    self.process_recentvideos()
                elif signal == 'allmusic':
                    self.process_allmusic()
                elif signal == 'unprocessedmusic':
                    self.process_allmusic(self.processed.does_not_exist)
                elif signal == 'oldmusic':
                    if self.process_allmusic(self.processed.is_stale):
                        self.last_musicupdate = get_date()
                self.status = STATUS_IDLE

    def abortRequested(self):
        return self.abort or super(ArtworkService, self).abortRequested()

    def waitForAbort(self, timeout=None):
        return self.abort or super(ArtworkService, self).waitForAbort(timeout)

    def really_waitforabort(self, timeout=None):
        return super(ArtworkService, self).waitForAbort(timeout)

    def onNotification(self, sender, method, data):
        if method.startswith('Other.') and sender != 'script.artwork.beef:control':
            return
        if method == 'Other.CancelCurrent':
            if self.status == STATUS_PROCESSING:
                self.abort = True
            elif self.signal:
                self.signal = None
                self.processor.close_progress()
        elif method == 'Other.ProcessUnprocessedVideos':
            self.processor.create_progress()
            self.signal = 'unprocessedvideos'
        elif method == 'Other.ProcessOldVideos':
            self.processor.create_progress()
            self.signal = 'oldvideos'
        elif method == 'Other.ProcessAllVideos':
            self.processor.create_progress()
            self.signal = 'allvideos'
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
                scan_olditems = settings.enable_olditem_updates and get_date() > self.last_videoupdate
                self.signal = 'oldvideos' if scan_olditems else 'unprocessedvideos'
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
                self.recentvideos[data['item']['type']].append(data['item']['id'])
                self.signal = 'recentvideos'
        elif pykodi.get_kodi_version() >= 18:
            if method == 'AudioLibrary.OnScanFinished':
                if settings.enableservice_music:
                    scan_olditems = settings.enable_olditem_updates and get_date() > self.last_musicupdate
                    self.signal = 'oldmusic' if scan_olditems else 'unprocessedmusic'
            elif method == 'Other.ProcessUnprocessedMusic':
                self.processor.create_progress()
                self.signal = 'unprocessedmusic'
            elif method == 'Other.ProcessOldMusic':
                self.processor.create_progress()
                self.signal = 'oldmusic'
            elif method == 'Other.ProcessAllMusic':
                self.processor.create_progress()
                self.signal = 'allmusic'

    def watchitem(self, data):
        can_use_data = 'item' in data and data['item'].get('id') and data['item'].get('id') != -1
        return can_use_data and 'playcount' not in data and data['item'].get('type') in self.recentvideos \
            and (pykodi.get_kodi_version() < 18 or data.get('added'))

    def process_allvideos(self, shouldinclude_fn=None):
        allvideos = False
        if not shouldinclude_fn:
            allvideos = True
            shouldinclude_fn = lambda id, type, label: True
        items = []
        if not mediatypes.disabled(mediatypes.MOVIE):
            items.extend(info.MediaItem(movie) for movie in quickjson.get_item_list(mediatypes.MOVIE)
                if shouldinclude_fn(movie['movieid'], mediatypes.MOVIE, movie['label']))
        if not mediatypes.disabled(mediatypes.MOVIESET):
            items.extend(info.MediaItem(mset) for mset in quickjson.get_item_list(mediatypes.MOVIESET)
                if shouldinclude_fn(mset['setid'], mediatypes.MOVIESET, mset['label']))
        if not mediatypes.disabled(mediatypes.MUSICVIDEO):
            items.extend(info.MediaItem(mvid) for mvid in quickjson.get_item_list(mediatypes.MUSICVIDEO)
                if shouldinclude_fn(mvid['musicvideoid'], mediatypes.MUSICVIDEO, info.musicvideo_label(mvid)))

        serieslist = quickjson.get_tvshows()
        if self.abortRequested():
            return False
        serieseps_added = set()
        for series in serieslist:
            processed_season = self.processed.get_data(series['tvshowid'], mediatypes.TVSHOW, series['label'])
            if not processed_season or series['season'] > int(processed_season) \
            or shouldinclude_fn(series['tvshowid'], mediatypes.TVSHOW, series['label']):
                if not mediatypes.disabled(mediatypes.TVSHOW):
                    items.append(info.MediaItem(series))
                if series['imdbnumber'] not in settings.autoadd_episodes and not allvideos:
                    if settings.generate_episode_thumb and not mediatypes.disabled(mediatypes.EPISODE):
                        for episode in quickjson.get_episodes(series['tvshowid']):
                            if not info.has_generated_thumbnail(episode):
                                ep = info.MediaItem(episode)
                                ep.skip_artwork = ['fanart']
                                items.append(ep)
                    serieseps_added.add(series['tvshowid'])
            if series['imdbnumber'] in settings.autoadd_episodes and series['tvshowid'] not in serieseps_added \
            and not mediatypes.disabled(mediatypes.EPISODE):
                episodes = quickjson.get_episodes(series['tvshowid'])
                items.extend(info.MediaItem(ep) for ep in episodes if shouldinclude_fn(ep['episodeid'], mediatypes.EPISODE, ep['label']))
                serieseps_added.add(series['tvshowid'])
            if self.abortRequested():
                return False
        if settings.generate_episode_thumb and not mediatypes.disabled(mediatypes.EPISODE):
            # Too many to get all of them, and filtering by a specific date for dateadded isn't much better
            for episode in quickjson.get_episodes() if allvideos else quickjson.get_episodes(limit=500):
                if episode['tvshowid'] not in serieseps_added and not info.has_generated_thumbnail(episode):
                    ep = info.MediaItem(episode)
                    ep.skip_artwork = ['fanart']
                    items.append(ep)
        self.reset_recent()
        return self.processor.process_medialist(items)

    def process_recentvideos(self):
        ignoreepisodesfrom = set()
        addepisodesfrom = set()
        seriesadded = set()
        newitems = []
        for mtype in ('movie', 'musicvideo', 'tvshow'):
            if mediatypes.disabled(mtype):
                continue
            for mediaid in self.recentvideos[mtype]:
                if mtype == 'tvshow':
                    seriesadded.add(mediaid)
                newitems.append(info.MediaItem(quickjson.get_item_details(mediaid, mtype)))
                if self.abortRequested():
                    return
        for episodeid in self.recentvideos['episode']:
            episode = info.MediaItem(quickjson.get_item_details(episodeid, mediatypes.EPISODE))
            series = None
            if not mediatypes.disabled(mediatypes.TVSHOW) and episode.tvshowid not in seriesadded \
            and episode.season > self.processed.get_data(episode.tvshowid, mediatypes.TVSHOW, episode.label):
                seriesadded.add(episode.tvshowid)
                series = info.MediaItem(quickjson.get_item_details(episode.tvshowid, mediatypes.TVSHOW))
                newitems.append(series)
            if mediatypes.disabled(mediatypes.EPISODE):
                if self.abortRequested():
                    return
                continue
            if episode.tvshowid in addepisodesfrom:
                newitems.append(episode)
            elif episode.tvshowid in ignoreepisodesfrom:
                if settings.generate_episode_thumb:
                    episode.skip_artwork = ['fanart']
                    newitems.append(episode)
            else:
                if not series:
                    series = info.MediaItem(quickjson.get_item_details(episode.tvshowid, mediatypes.TVSHOW))
                if any(x for x in series.uniqueids.itervalues() if x in settings.autoadd_episodes):
                    addepisodesfrom.add(episode.tvshowid)
                    newitems.append(episode)
                else:
                    ignoreepisodesfrom.add(episode.tvshowid)
                    if settings.generate_episode_thumb:
                        episode.skip_artwork = ['fanart']
                        newitems.append(episode)
            if self.abortRequested():
                return

        self.reset_recent()
        self.processor.process_medialist(newitems)

    def process_allmusic(self, shouldinclude_fn=None):
        if not shouldinclude_fn:
            shouldinclude_fn = lambda id, type, label: True
        items = []
        if not mediatypes.disabled(mediatypes.ARTIST):
            items.extend(info.MediaItem(artist) for artist in quickjson.get_item_list(mediatypes.ARTIST)
                if shouldinclude_fn(artist['artistid'], mediatypes.ARTIST, artist['label']))
        if self.abortRequested():
            return False
        if not mediatypes.disabled(mediatypes.ALBUM):
            albums = quickjson.get_albums()
            if self.abortRequested():
                return False
            for album in albums:
                if not shouldinclude_fn(album['albumid'], mediatypes.ALBUM, album['label']):
                    continue
                items.append(info.MediaItem(album))
                if len(albums) < 200 and not mediatypes.disabled(mediatypes.SONG):
                    items.extend(info.MediaItem(song) for song in quickjson.get_songs(mediatypes.ALBUM, album['albumid']))
                if self.abortRequested():
                    return False
        return self.processor.process_medialist(items)

    def onSettingsChanged(self):
        settings.update_settings()
        mediatypes.update_settings()
        if self.processaftersettings:
            self.processor.create_progress()
            xbmc.sleep(200)
            self.processaftersettings = False
            self.signal = 'unprocessedvideos'

def get_date():
    return pykodi.get_infolabel('System.Date(yyyy-mm-dd)')

if __name__ == '__main__':
    log('Service started', xbmc.LOGINFO)
    ArtworkService().run()
    log('Service stopped', xbmc.LOGINFO)
