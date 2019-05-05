import xbmc
from itertools import chain

from lib.artworkprocessor import ArtworkProcessor
from lib.libs import mediainfo as info, mediatypes, pykodi, quickjson
from lib.libs.addonsettings import settings
from lib.libs.processeditems import ProcessedItems
from lib.libs.pykodi import log, json

STATUS_IDLE = 'idle'
STATUS_SIGNALLED = 'signalled'
STATUS_PROCESSING = 'processing'

ALBUM_CHUNK_SIZE = 200

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
        self._check_allepisodes = addon.get_setting('check_allepisodes')
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
    def check_allepisodes(self):
        return self._check_allepisodes

    @check_allepisodes.setter
    def check_allepisodes(self, value):
        addon.set_setting('check_allepisodes', value)
        self._check_allepisodes = value

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
                    self.notify_finished('Video', self.process_allvideos())
                elif signal == 'newvideos':
                    self.notify_finished('Video', self.process_allvideos(self.processed.does_not_exist))
                elif signal == 'oldvideos':
                    successful = self.process_allvideos(self.processed.is_stale)
                    if successful:
                        self.last_videoupdate = get_date()
                    self.notify_finished('Video', successful)
                elif signal == 'localvideos':
                    self.processor.localmode = True
                    self.notify_finished('Video', self.process_allvideos())
                    self.processor.localmode = False
                elif signal == 'recentvideos_really':
                    self.process_recentvideos()
                elif signal == 'allmusic':
                    self.notify_finished('Music', self.process_allmusic())
                elif signal == 'newmusic':
                    self.notify_finished('Music', self.process_allmusic(self.processed.does_not_exist))
                elif signal == 'oldmusic':
                    successful = self.process_allmusic(self.processed.is_stale)
                    if successful:
                        self.last_musicupdate = get_date()
                    self.notify_finished('Music', successful)

                self.status = STATUS_IDLE

    def abortRequested(self):
        return self.waitForAbort(0.0001)

    def waitForAbort(self, timeout=0):
        return self.abort or super(ArtworkService, self).waitForAbort(timeout)

    def really_waitforabort(self, timeout=0):
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
        elif method == 'Other.ProcessNewVideos':
            self.processor.create_progress()
            self.signal = 'newvideos'
        elif method == 'Other.ProcessNewAndOldVideos':
            self.processor.create_progress()
            self.signal = 'oldvideos'
        elif method == 'Other.ProcessAllVideos':
            self.processor.create_progress()
            self.signal = 'allvideos'
        elif method == 'Other.ProcessLocalVideos':
            self.processor.create_progress()
            self.signal = 'localvideos'
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
                self.signal = 'oldvideos' if scan_olditems else 'newvideos'
                self.processor.create_progress()
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
                    self.signal = 'oldmusic' if scan_olditems else 'newmusic'
            elif method == 'Other.ProcessNewMusic':
                self.processor.create_progress()
                self.signal = 'newmusic'
            elif method == 'Other.ProcessNewAndOldMusic':
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
        allvideos = self.check_allepisodes
        if not shouldinclude_fn:
            allvideos = True
            shouldinclude_fn = lambda id, type, label: True
        items = []
        if not mediatypes.disabled(mediatypes.MOVIESET):
            items.extend(info.MediaItem(mset) for mset in chain.from_iterable(
                    quickjson.gen_chunked_item_list(mediatypes.MOVIESET))
                if shouldinclude_fn(mset['setid'], mediatypes.MOVIESET, mset['label']))
        if not mediatypes.disabled(mediatypes.MOVIE):
            items.extend(info.MediaItem(movie) for movie in chain.from_iterable(
                    quickjson.gen_chunked_item_list(mediatypes.MOVIE))
                if shouldinclude_fn(movie['movieid'], mediatypes.MOVIE, movie['label']))
        if not mediatypes.disabled(mediatypes.MUSICVIDEO):
            items.extend(info.MediaItem(mvid) for mvid in chain.from_iterable(
                    quickjson.gen_chunked_item_list(mediatypes.MUSICVIDEO))
                if shouldinclude_fn(mvid['musicvideoid'], mediatypes.MUSICVIDEO, info.build_music_label(mvid)))

        serieslist = quickjson.get_tvshows()
        if self.abortRequested():
            return False
        if not mediatypes.disabled(mediatypes.TVSHOW):
            for series in serieslist:
                processed_season = self.processed.get_data(series['tvshowid'], mediatypes.TVSHOW, series['label'])
                if not processed_season or series['season'] > int(processed_season) \
                or shouldinclude_fn(series['tvshowid'], mediatypes.TVSHOW, series['label']):
                    items.append(info.MediaItem(series))
                if self.abortRequested():
                    return False
        if include_any_episode():
            seriesmap = dict((s['tvshowid'], s['imdbnumber']) for s in serieslist)
            episodes = []
            for episodelist in (quickjson.gen_chunked_item_list(mediatypes.EPISODE)
                    if allvideos else [quickjson.get_episodes(limit=500)]):
                for episode in episodelist:
                    ep = info.MediaItem(episode)
                    if seriesmap.get(ep.tvshowid) in settings.autoadd_episodes or include_episode(ep):
                        episodes.append(ep)
                if self.abortRequested():
                    return False
            self.check_allepisodes = len(episodes) > 400
            for episode in episodes:
                if seriesmap.get(episode.tvshowid) not in settings.autoadd_episodes:
                    episode.skip_artwork = ['fanart']
                    items.append(episode)
                elif shouldinclude_fn(episode.dbid, mediatypes.EPISODE, episode.label):
                    items.append(episode)
                if self.abortRequested():
                    return False
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
                jsonitem = quickjson.get_item_details(mediaid, mtype)
                if jsonitem.get('setid'):
                    newitems.append(info.MediaItem(quickjson.get_item_details(jsonitem['setid'], mediatypes.MOVIESET)))
                newitems.append(info.MediaItem(jsonitem))
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
            if not include_any_episode():
                if self.abortRequested():
                    return
                continue
            if episode.tvshowid in addepisodesfrom:
                newitems.append(episode)
            elif episode.tvshowid in ignoreepisodesfrom:
                if include_episode(episode):
                    episode.skip_artwork = ['fanart']
                    newitems.append(episode)
            else:
                if not series:
                    series = info.MediaItem(quickjson.get_item_details(episode.tvshowid, mediatypes.TVSHOW))
                if any(x for x in series.uniqueids.values() if x in settings.autoadd_episodes):
                    addepisodesfrom.add(episode.tvshowid)
                    newitems.append(episode)
                else:
                    ignoreepisodesfrom.add(episode.tvshowid)
                    if include_episode(episode):
                        episode.skip_artwork = ['fanart']
                        newitems.append(episode)
            if self.abortRequested():
                return

        self.reset_recent()
        self.processor.process_medialist(newitems)

    def process_allmusic(self, shouldinclude_fn=None):
        if mediatypes.disabled(mediatypes.ALBUM) and mediatypes.disabled(mediatypes.ARTIST):
            return True
        if not shouldinclude_fn:
            shouldinclude_fn = lambda id, type, label: True
        albums = []
        if not mediatypes.disabled(mediatypes.ALBUM):
            albums.extend(info.MediaItem(album) for album in quickjson.get_albums()
                if shouldinclude_fn(album['albumid'], mediatypes.ALBUM, info.build_music_label(album)))
        if self.abortRequested():
            return False
        artists = []
        if not mediatypes.disabled(mediatypes.ARTIST):
            artists.extend(info.MediaItem(artist) for artist in quickjson.get_item_list(mediatypes.ARTIST)
                if shouldinclude_fn(artist['artistid'], mediatypes.ARTIST, artist['label']))
        if self.abortRequested():
            return False
        if not albums and not artists:
            return True
        chunkedalbums = [albums[x:x+ALBUM_CHUNK_SIZE] for x in range(0, len(albums), ALBUM_CHUNK_SIZE)]
        def chunk_filler():
            for albumgroup in chunkedalbums:
                songs = _buildsongs(albumgroup)
                if self.abortRequested():
                    yield False
                itemgroup = []
                for album in albumgroup:
                    if not mediatypes.disabled(mediatypes.ARTIST):
                        artist = next((a for a in artists if a.dbid == album.artistid), None)
                        if artist:
                            itemgroup.append(artist)
                            artists.remove(artist)
                    if not mediatypes.disabled(mediatypes.ALBUM):
                        itemgroup.append(album)
                    if not mediatypes.disabled(mediatypes.SONG) and album.dbid in songs:
                        itemgroup.extend(info.MediaItem(song) for song in songs[album.dbid])
                    if self.abortRequested():
                        yield False

                yield itemgroup
            if artists: # New artists that didn't match an album
                yield artists
        return self.processor.process_chunkedlist(chunk_filler(), len(chunkedalbums))

    def onSettingsChanged(self):
        settings.update_settings()
        mediatypes.update_settings()
        if self.processaftersettings:
            self.processor.create_progress()
            xbmc.sleep(200)
            self.processaftersettings = False
            self.signal = 'newvideos'

    def notify_finished(self, content, success):
        if success:
            pykodi.execute_builtin('NotifyAll(script.artwork.beef, On{0}ProcessingFinished)'.format(content))
        else:
            self.processor.close_progress()

def get_date():
    return pykodi.get_infolabel('System.Date(yyyy-mm-dd)')

def include_any_episode():
    return not mediatypes.disabled(mediatypes.EPISODE) \
        and (mediatypes.generatethumb(mediatypes.EPISODE) or mediatypes.downloadanyartwork(mediatypes.EPISODE) \
            or settings.autoadd_episodes)

def include_episode(episode):
    return mediatypes.generatethumb(mediatypes.EPISODE) and not info.item_has_generated_thumbnail(episode) \
        or info.has_art_todownload(episode.art, mediatypes.EPISODE)

def _buildsongs(albumgroup):
    result = {}
    if mediatypes.disabled(mediatypes.SONG):
        return result
    songfilter = {'field': 'album', 'operator': 'is',
        'value': [album.label for album in albumgroup]}
    for song in quickjson.get_songs(songfilter=songfilter):
        if song['albumid'] not in result:
            result[song['albumid']] = []
        result[song['albumid']].append(song)
    return result

if __name__ == '__main__':
    log('Service started', xbmc.LOGINFO)
    ArtworkService().run()
    log('Service stopped', xbmc.LOGINFO)
