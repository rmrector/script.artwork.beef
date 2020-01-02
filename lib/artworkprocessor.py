import random
import xbmc
import xbmcgui
import os
import re
from datetime import timedelta

from lib import cleaner, reporting
from lib.artworkselection import prompt_for_artwork
from lib.filemanager import FileManager, FileError
from lib.gatherer import Gatherer
from lib.libs import mediainfo as info, mediatypes, pykodi, quickjson
from lib.libs.addonsettings import settings, PROGRESS_DISPLAY_FULLPROGRESS, PROGRESS_DISPLAY_NONE, EXCLUSION_PATH_TYPE_FOLDER, EXCLUSION_PATH_TYPE_PREFIX, EXCLUSION_PATH_TYPE_REGEX
from lib.libs.processeditems import ProcessedItems
from lib.libs.pykodi import datetime_now, get_kodi_version, localize as L, log
from lib.libs.utils import SortedDisplay, natural_sort, get_simpledict_updates
from lib.providers import search

MODE_AUTO = 'auto'
MODE_GUI = 'gui'
MODE_DEBUG = 'debug'

THROTTLE_TIME = 0.15

SOMETHING_MISSING = 32001
FINAL_MESSAGE = 32019
ADDING_ARTWORK_MESSAGE = 32020
NOT_AVAILABLE_MESSAGE = 32021
ARTWORK_UPDATED_MESSAGE = 32022
NO_ARTWORK_UPDATED_MESSAGE = 32023
PROVIDER_ERROR_MESSAGE = 32024
NOT_SUPPORTED_MESSAGE = 32025
CURRENT_ART = 13512
ENTER_COLLECTION_NAME = 32057
ENTER_ARTIST_TRACK_NAMES = 32058
NO_IDS_MESSAGE = 32030
FILENAME_ENCODING_ERROR = 32040

class ArtworkProcessor(object):
    def __init__(self, monitor=None):
        self.monitor = monitor or xbmc.Monitor()
        self.language = None
        self.autolanguages = None
        self.progress = xbmcgui.DialogProgressBG()
        self.visible = False
        self.freshstart = "0"
        self.processed = ProcessedItems()
        self.gatherer = None
        self.downloader = None
        self.chunkcount = 1
        self.currentchunk = 0
        self.debug = False
        self.localmode = False
        settings.update_settings()
        mediatypes.update_settings()

    def create_progress(self):
        if not self.visible and settings.progressdisplay == PROGRESS_DISPLAY_FULLPROGRESS:
            self.progress.create("Artwork Beef: " + L(ADDING_ARTWORK_MESSAGE), "")
            self.visible = True

    def update_progress(self, percent, message, heading=None):
        if self.chunkcount > 1:
            onechunkp = 100 / (self.chunkcount * 1.0)
            percent = int(onechunkp * self.currentchunk + percent / (self.chunkcount * 1.0))
        if self.visible and settings.progressdisplay == PROGRESS_DISPLAY_FULLPROGRESS:
            self.progress.update(percent, heading, message)

    def finalupdate(self, header, message):
        if settings.final_notification:
            xbmcgui.Dialog().notification("Artwork Beef: " + header, message, '-', 8000)
        elif settings.progressdisplay == PROGRESS_DISPLAY_FULLPROGRESS:
            self.update_progress(100, message, header)
            try:
                self.monitor.really_waitforabort(8)
            except AttributeError:
                self.monitor.waitForAbort(8)

    def close_progress(self):
        if self.visible and settings.progressdisplay == PROGRESS_DISPLAY_FULLPROGRESS:
            self.progress.close()
            self.visible = False

    def notify_warning(self, message, header=None, error=False):
        if settings.progressdisplay != PROGRESS_DISPLAY_NONE:
            header = "Artwork Beef: " + header if header else "Artwork Beef"
            xbmcgui.Dialog().notification(header, message,
                xbmcgui.NOTIFICATION_ERROR if error else xbmcgui.NOTIFICATION_WARNING)

    def init_run(self, show_progress=False, chunkcount=1):
        self.setlanguages()
        self.gatherer = Gatherer(self.monitor, self.autolanguages)
        self.downloader = FileManager(self.debug, chunkcount > 1)
        self.freshstart = str(datetime_now() - timedelta(days=365))
        self.chunkcount = chunkcount
        self.currentchunk = 0
        if get_kodi_version() >= 18:
            populate_musiccentraldir()
        if show_progress:
            self.create_progress()

    def set_debug(self, debug):
        if self.downloader:
            self.downloader.debug = debug
        reporting.debug = debug
        self.debug = debug

    def finish_run(self):
        info.clear_cache()
        self.downloader = None
        self.set_debug(False)
        self.close_progress()

    @property
    def processor_busy(self):
        # DEPRECATED: StringCompare is deprecated in Krypton, gone in Leia
        return pykodi.get_conditional('![StringCompare(Window(Home).Property(ArtworkBeef.Status),idle) | String.IsEqual(Window(Home).Property(ArtworkBeef.Status),idle)]')

    def process_item(self, mediatype, dbid, mode):
        if self.processor_busy:
            return
        if mode == MODE_DEBUG:
            mode = MODE_AUTO
            self.set_debug(True)
        if mode == MODE_GUI:
            busy = pykodi.get_busydialog()
            busy.create()
        if mediatype in mediatypes.artinfo and (mediatype not in mediatypes.audiotypes or get_kodi_version() >= 18):
            mediaitem = info.MediaItem(quickjson.get_item_details(dbid, mediatype))
            log("Processing {0} '{1}' {2}.".format(mediatype, mediaitem.label, 'automatically'
                if mode == MODE_AUTO else 'manually'))
        else:
            if mode == MODE_GUI:
                busy.close()
            xbmcgui.Dialog().notification("Artwork Beef", L(NOT_SUPPORTED_MESSAGE).format(mediatype), '-', 6500)
            return

        self.init_run()
        if mediatype == mediatypes.EPISODE:
            series = quickjson.get_item_details(mediaitem.tvshowid, mediatypes.TVSHOW)
            if not any(uniqueid in settings.autoadd_episodes for uniqueid in series['uniqueid'].itervalues()):
                mediaitem.skip_artwork = ['fanart']

        info.add_additional_iteminfo(mediaitem, self.processed, search)
        if not mediaitem.uniqueids and not mediatypes.only_filesystem(mediaitem.mediatype):
            if mediatype in mediatypes.require_manualid:
                self.manual_id(mediaitem)
        if mode == MODE_GUI:
            self._manual_item_process(mediaitem, busy)
        else:
            medialist = [mediaitem]
            if mediatype == mediatypes.TVSHOW and not mediatypes.disabled(mediatypes.EPISODE):
                gen_epthumb = mediatypes.generatethumb(mediatypes.EPISODE)
                download_ep = mediatypes.downloadanyartwork(mediatypes.EPISODE)
                if mediaitem.uniqueids and any(x in mediaitem.uniqueids.values() for x in settings.autoadd_episodes):
                    medialist.extend(info.MediaItem(ep) for ep in quickjson.get_episodes(dbid))
                elif gen_epthumb or download_ep:
                    for episode in quickjson.get_episodes(dbid):
                        if gen_epthumb and not info.has_generated_thumbnail(episode) \
                        or download_ep and info.has_art_todownload(episode['art'], mediatypes.EPISODE):
                            episode = info.MediaItem(episode)
                            episode.skip_artwork = ['fanart']
                            medialist.append(episode)
            elif mediatype == mediatypes.ARTIST and not mediatypes.disabled(mediatypes.ALBUM):
                medialist.extend(info.MediaItem(album) for album in quickjson.get_albums(mediaitem.label, mediaitem.dbid))
            if mediatype in (mediatypes.ALBUM, mediatypes.ARTIST) and not mediatypes.disabled(mediatypes.ALBUM) \
            and not mediatypes.disabled(mediatypes.SONG):
                medialist.extend(info.MediaItem(song)
                    for song in quickjson.get_songs(mediaitem.mediatype, mediaitem.dbid))
            self.process_medialist(medialist, True)

    def _manual_item_process(self, mediaitem, busy):
        self._process_item(mediaitem, True, False)
        busy.close()
        if mediaitem.availableart or mediaitem.forcedart:
            availableart = dict(mediaitem.availableart)
            if mediaitem.mediatype == mediatypes.TVSHOW and 'fanart' in availableart:
                # add unseasoned backdrops as manual-only options for each season fanart
                unseasoned_backdrops = [dict(art) for art in availableart['fanart'] if not art.get('hasseason')]
                if unseasoned_backdrops:
                    for season in mediaitem.seasons.keys():
                        key = 'season.{0}.fanart'.format(season)
                        if key in availableart:
                            availableart[key].extend(unseasoned_backdrops)
                        else:
                            availableart[key] = list(unseasoned_backdrops)
            if mediaitem.mediatype in (mediatypes.MOVIE, mediatypes.MOVIESET) and 'poster' in availableart:
                # add no-language posters from TMDB as manual-only options for 'keyart'
                nolang_posters = [dict(art) for art in availableart['poster'] if not art['language']]
                for art in nolang_posters:
                    if art['provider'].sort == 'themoviedb.org':
                        if 'keyart' not in availableart:
                            availableart['keyart'] = []
                        availableart['keyart'].append(art)
            tag_forcedandexisting_art(availableart, mediaitem.forcedart, mediaitem.art)
            selectedarttype, selectedart = prompt_for_artwork(mediaitem.mediatype, mediaitem.label,
                availableart, self.monitor)
            if selectedarttype and selectedarttype not in availableart:
                self.manual_id(mediaitem)
                return
            if selectedarttype and selectedart:
                if mediatypes.get_artinfo(mediaitem.mediatype, selectedarttype)['multiselect']:
                    selectedart = info.fill_multiart(mediaitem.art, selectedarttype, selectedart)
                else:
                    selectedart = {selectedarttype: selectedart}

                selectedart = get_simpledict_updates(mediaitem.art, selectedart)
                mediaitem.selectedart = selectedart
                toset = dict(selectedart)
                if settings.remove_deselected_files:
                    self.downloader.remove_deselected_files(mediaitem)
                if mediatypes.downloadanyartwork(mediaitem.mediatype):
                    try:
                        self.downloader.downloadfor(mediaitem, False)
                    except FileError as ex:
                        mediaitem.error = ex.message
                        log(ex.message, xbmc.LOGERROR)
                        xbmcgui.Dialog().notification("Artwork Beef", ex.message, xbmcgui.NOTIFICATION_ERROR)
                    toset.update(mediaitem.downloadedart)
                if toset:
                    mediaitem.updatedart = toset.keys()
                    add_art_to_library(mediaitem.mediatype, mediaitem.seasons, mediaitem.dbid, toset)
                self.cachelocal(mediaitem, toset)

                reporting.report_item(mediaitem, True, True, self.downloader.size)
                if not mediaitem.error:
                    notifycount(len(toset))
        else:
            xbmcgui.Dialog().notification(L(NOT_AVAILABLE_MESSAGE),
                L(SOMETHING_MISSING) + ' ' + L(FINAL_MESSAGE), '-', 8000)
        self.finish_run()

    def process_medialist(self, medialist, alwaysnotify=False):
        return self.process_chunkedlist([medialist], 1, alwaysnotify)

    def process_chunkedlist(self, chunkedlist, chunkcount, alwaysnotify=False):
        self.init_run(True, chunkcount)
        aborted = False
        artcount = 0
        for idx, medialist in enumerate(chunkedlist):
            self.currentchunk = idx
            if not idx and chunkcount == 1 and len(medialist) > 100:
                self.downloader.set_bigcache()
            if self.monitor.abortRequested() or medialist is False:
                aborted = True
                break
            reporting.report_start(medialist)
            this_aborted, updateditemcount, this_artcount = \
                self._process_chunk(medialist, len(medialist) == 1 and not idx, alwaysnotify)
            artcount += this_artcount
            reporting.report_end(medialist, updateditemcount if this_aborted else 0, self.downloader.size)
            self.downloader.size = 0
            if this_aborted:
                aborted = True
                break
        if artcount or alwaysnotify:
            self.finalupdate(*finalmessages(artcount))
        self.finish_run()
        return not aborted

    def _process_chunk(self, medialist, singleitemlist, singleitem):
        artcount = 0
        currentitem = 0
        aborted = False
        for mediaitem in medialist:
            if is_excluded(mediaitem):
                continue
            if mediaitem.mediatype in mediatypes.audiotypes and get_kodi_version() < 18:
                continue
            self.update_progress(currentitem * 100 // len(medialist), mediaitem.label)
            info.add_additional_iteminfo(mediaitem, self.processed, None if self.localmode else search)
            currentitem += 1
            try:
                services_hit = self._process_item(mediaitem, singleitem)
            except FileError as ex:
                services_hit = True
                mediaitem.error = ex.message
                log(ex.message, xbmc.LOGERROR)
                self.notify_warning(ex.message, None, True)
            reporting.report_item(mediaitem, singleitemlist or mediaitem.error)
            artcount += len(mediaitem.updatedart)

            if not services_hit:
                if self.monitor.abortRequested():
                    aborted = True
                    break
            elif self.monitor.waitForAbort(THROTTLE_TIME):
                aborted = True
                break
        return aborted, currentitem, artcount

    def _process_item(self, mediaitem, singleitem=False, auto=True):
        log("Processing {0} '{1}' automatically.".format(mediaitem.mediatype, mediaitem.label))
        mediatype = mediaitem.mediatype
        onlyfs = self.localmode or mediatypes.only_filesystem(mediaitem.mediatype)
        if not mediaitem.uniqueids and not onlyfs:
            mediaitem.missingid = True
            if singleitem:
                header = L(NO_IDS_MESSAGE)
                message = "{0} '{1}'".format(mediatype, mediaitem.label)
                log(header + ": " + message, xbmc.LOGNOTICE)
                xbmcgui.Dialog().notification("Artwork Beef: " + header, message, xbmcgui.NOTIFICATION_INFO)

        if auto:
            cleaned = get_simpledict_updates(mediaitem.art, cleaner.clean_artwork(mediaitem))
            if cleaned:
                if not self.debug:
                    add_art_to_library(mediatype, mediaitem.seasons, mediaitem.dbid, cleaned)
                mediaitem.art.update(cleaned)
                mediaitem.art = dict(item for item in mediaitem.art.iteritems() if item[1])

        mediaitem.missingart = list(info.iter_missing_arttypes(mediaitem, mediaitem.art))

        services_hit, error = self.gatherer.getartwork(mediaitem, onlyfs, auto)

        if auto:
            existingart = dict(mediaitem.art)
            selectedart = dict((key, image['url']) for key, image in mediaitem.forcedart.iteritems())
            existingart.update(selectedart)

            # Then add the rest of the missing art
            selectedart.update(self.get_top_missing_art(info.iter_missing_arttypes(mediaitem, existingart),
                mediatype, existingart, mediaitem.availableart))

            selectedart = get_simpledict_updates(mediaitem.art, selectedart)
            mediaitem.selectedart = selectedart
            toset = dict(selectedart)
            if not self.localmode and mediatypes.downloadanyartwork(mediaitem.mediatype):
                sh, er = self.downloader.downloadfor(mediaitem)
                services_hit = services_hit or sh
                error = error or er
                toset.update(mediaitem.downloadedart)
            if toset:
                mediaitem.updatedart = list(set(mediaitem.updatedart + toset.keys()))
                if not self.debug:
                    add_art_to_library(mediatype, mediaitem.seasons, mediaitem.dbid, toset)
            self.cachelocal(mediaitem, toset)

        if error:
            if isinstance(error, dict):
                header = L(PROVIDER_ERROR_MESSAGE).format(error['providername'])
                error = '{0}: {1}'.format(header, error['message'])
            mediaitem.error = error
            log(error, xbmc.LOGWARNING)
            self.notify_warning(error)
        elif auto and not self.debug and not self.localmode:
            if not (mediatype == mediatypes.EPISODE and 'fanart' in mediaitem.skip_artwork) and \
                    mediatype != mediatypes.SONG:
                self.processed.set_nextdate(mediaitem.dbid, mediatype, mediaitem.label,
                    datetime_now() + timedelta(days=self.get_nextcheckdelay(mediaitem)))
            if mediatype == mediatypes.TVSHOW:
                self.processed.set_data(mediaitem.dbid, mediatype, mediaitem.label, mediaitem.season)
        if mediaitem.borked_filename:
            msg = L(FILENAME_ENCODING_ERROR).format(mediaitem.file)
            if not mediaitem.error:
                mediaitem.error = msg
            log(msg, xbmc.LOGWARNING)
        if self.debug:
            log(mediaitem, xbmc.LOGNOTICE)
        return services_hit

    def cachelocal(self, mediaitem, toset):
        ismusic = mediaitem.mediatype in mediatypes.audiotypes
        if settings.cache_local_video_artwork and not ismusic or \
                settings.cache_local_music_artwork and ismusic:
            artmap = dict(mediaitem.art)
            artmap.update(toset)
            self.downloader.cachefor(artmap)

    def get_nextcheckdelay(self, mediaitem):
        weeks = 4 if mediatypes.only_filesystem(mediaitem.mediatype) \
            else 32 if mediaitem.missingid or not mediaitem.missingart \
                or mediaitem.mediatype in (mediatypes.MOVIE, mediatypes.TVSHOW) \
                    and mediaitem.premiered < self.freshstart \
            else 16
        return plus_some(weeks * 7, weeks)

    def manual_id(self, mediaitem):
        label = ENTER_COLLECTION_NAME if mediaitem.mediatype == mediatypes.MOVIESET else ENTER_ARTIST_TRACK_NAMES
        result = xbmcgui.Dialog().input(L(label), mediaitem.label)
        if not result:
            return False # Cancelled
        options = search[mediaitem.mediatype].search(result, mediaitem.mediatype)
        selected = xbmcgui.Dialog().select(mediaitem.label, [option['label'] for option in options])
        if selected < 0:
            return False # Cancelled
        uq = options[selected]['uniqueids']
        toset = uq.get('tmdb')
        if not toset and 'mbtrack' in uq and 'mbgroup' in uq and 'mbartist' in uq:
            toset = '{0}/{1}/{2}'.format(uq['mbtrack'], uq['mbgroup'], uq['mbartist'])
        if toset:
            self.processed.set_data(mediaitem.dbid, mediaitem.mediatype, mediaitem.label, toset)
        return bool(toset)

    def setlanguages(self):
        languages = []
        if settings.language_override:
            languages.append(settings.language_override)
        if settings.language_fallback_kodi:
            newlang = pykodi.get_language(xbmc.ISO_639_1)
            if newlang not in languages:
                languages.append(newlang)
        if settings.language_fallback_en and 'en' not in languages:
            languages.append('en')
        self.autolanguages = languages
        log("Working language filter: " + str(languages))

    def get_top_missing_art(self, missingarts, mediatype, existingart, availableart):
        # TODO: refactor to `get_top_artwork` that works on a single art type
        if not availableart:
            return {}
        newartwork = {}
        for missingart in missingarts:
            if missingart not in availableart:
                continue
            itemtype, artkey = mediatypes.hack_mediaarttype(mediatype, missingart)
            artinfo = mediatypes.get_artinfo(itemtype, artkey)
            if artinfo['multiselect']:
                existingurls = []
                existingartnames = []
                for art, url in existingart.iteritems():
                    if info.arttype_matches_base(art, missingart) and url:
                        existingurls.append(url)
                        existingartnames.append(art)

                newart = [art for art in availableart[missingart] if
                    self._auto_filter(missingart, art, mediatype, availableart[missingart], existingurls)]
                if not newart:
                    continue
                newartcount = 0
                for i in range(0, artinfo['autolimit']):
                    exacttype = '%s%s' % (artkey, i if i else '')
                    if exacttype not in existingartnames:
                        if newartcount >= len(newart):
                            break
                        if exacttype not in newartwork:
                            newartwork[exacttype] = []
                        newartwork[exacttype] = newart[newartcount]['url']
                        newartcount += 1
            else:
                newart = next((art for art in availableart[missingart] if
                    self._auto_filter(missingart, art, mediatype, availableart[missingart])), None)
                if newart:
                    newartwork[missingart] = newart['url']
        return newartwork

    def _auto_filter(self, basearttype, art, mediatype, availableart, ignoreurls=(), skippreferred=False):
        if art['rating'].sort < settings.minimum_rating:
            return False
        if not skippreferred and mediatypes.haspreferred_source(mediatype) and \
            not mediatypes.ispreferred_source(mediatype, art['provider'][0]) and \
            any(1 for i in availableart if mediatypes.ispreferred_source(mediatype, i['provider'][0]) and
                self._auto_filter(basearttype, i, mediatype, availableart, ignoreurls, True)):
            return False
        if basearttype.endswith('fanart') and art['size'].sort < settings.minimum_size:
            return False
        if art['provider'].sort == 'theaudiodb.com' or not art['language'] and \
            (basearttype.endswith('poster') and settings.titlefree_poster or
                basearttype.endswith(('fanart', 'keyart', 'characterart'))):
            return skippreferred or art['url'] not in ignoreurls
        return art['language'] in self.autolanguages and (skippreferred or art['url'] not in ignoreurls)

def add_art_to_library(mediatype, seasons, dbid, selectedart):
    if not selectedart:
        return
    for arttype, url in selectedart.items():
        # Kodi doesn't cache gifs, so force download in `downloader` and
        #   don't leave any HTTP URLs if they can't be saved
        if arttype.startswith('animated') and url and url.startswith('http'):
            selectedart[arttype] = None
    if mediatype == mediatypes.TVSHOW:
        for season, season_id in seasons.iteritems():
            info.update_art_in_library(mediatypes.SEASON, season_id, dict((arttype.split('.')[2], url)
                for arttype, url in selectedart.iteritems() if arttype.startswith('season.{0}.'.format(season))))
        info.update_art_in_library(mediatype, dbid, dict((arttype, url)
            for arttype, url in selectedart.iteritems() if '.' not in arttype))
    else:
        info.update_art_in_library(mediatype, dbid, selectedart)
    info.remove_local_from_texturecache(selectedart.values())

def finalmessages(count):
    return (L(ARTWORK_UPDATED_MESSAGE).format(count), L(FINAL_MESSAGE)) if count else \
        (L(NO_ARTWORK_UPDATED_MESSAGE), L(SOMETHING_MISSING) + ' ' + L(FINAL_MESSAGE))

def notifycount(count):
    header, message = finalmessages(count)
    xbmcgui.Dialog().notification("Artwork Beef: " + header, message, '-', 8000)

def plus_some(start, rng):
    return start + (random.randrange(-rng, rng + 1))

def populate_musiccentraldir():
    artistpath = quickjson.get_settingvalue('musiclibrary.artistsfolder')
    mediatypes.central_directories[mediatypes.ARTIST] = artistpath

def is_excluded(mediaitem):
    if mediaitem.file is None:
        return False
    for exclusion in settings.pathexclusion:
        if exclusion["type"] == EXCLUSION_PATH_TYPE_FOLDER:
            path_file = os.path.realpath(os.path.join(mediaitem.file, ''))
            path_excl = os.path.realpath(os.path.join(exclusion["folder"], ''))
            if os.path.commonprefix([path_file, path_excl]) == path_excl:
                return True
        if exclusion["type"] == EXCLUSION_PATH_TYPE_PREFIX:
            if mediaitem.file.startswith(exclusion["prefix"]):
                return True
        if exclusion["type"] == EXCLUSION_PATH_TYPE_REGEX:
            if re.match(exclusion["regex"], mediaitem.file):
                return True
    return False


def tag_forcedandexisting_art(availableart, forcedart, existingart):
    typeinsert = {}
    for exacttype, artlist in sorted(forcedart.iteritems(), key=lambda arttype: natural_sort(arttype[0])):
        arttype = info.get_basetype(exacttype)
        if arttype not in availableart:
            availableart[arttype] = artlist
        else:
            for image in artlist:
                match = next((available for available in availableart[arttype] if available['url'] == image['url']), None)
                if match:
                    if 'title' in image and 'title' not in match:
                        match['title'] = image['title']
                    match['second provider'] = image['provider'].display
                else:
                    typeinsert[arttype] = typeinsert[arttype] + 1 if arttype in typeinsert else 0
                    availableart[arttype].insert(typeinsert[arttype], image)

    typeinsert = {}
    for exacttype, existingurl in existingart.iteritems():
        arttype = info.get_basetype(exacttype)
        if arttype in availableart:
            match = next((available for available in availableart[arttype] if available['url'] == existingurl), None)
            if match:
                match['preview'] = existingurl
                match['existing'] = True
            else:
                typeinsert[arttype] = typeinsert[arttype] + 1 if arttype in typeinsert else 0
                image = {'url': existingurl, 'preview': existingurl, 'title': exacttype,
                    'existing': True, 'provider': SortedDisplay('current', L(CURRENT_ART))}
                availableart[arttype].insert(typeinsert[arttype], image)
