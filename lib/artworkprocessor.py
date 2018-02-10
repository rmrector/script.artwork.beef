import random
import xbmc
import xbmcgui
from datetime import timedelta

from lib import cleaner, reporting
from lib.artworkselection import prompt_for_artwork
from lib.filemanager import FileManager, FileError
from lib.gatherer import Gatherer
from lib.libs import mediainfo as info, mediatypes, pykodi, quickjson
from lib.libs.addonsettings import settings, PROGRESS_DISPLAY_FULLPROGRESS, PROGRESS_DISPLAY_NONE
from lib.libs.processeditems import ProcessedItems
from lib.libs.pykodi import datetime_now, get_kodi_version, localize as L, log
from lib.libs.utils import SortedDisplay, natural_sort, get_simpledict_updates
from lib.providers import search

MODE_AUTO = 'auto'
MODE_GUI = 'gui'

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

    def create_progress(self):
        if not self.visible and settings.progressdisplay == PROGRESS_DISPLAY_FULLPROGRESS:
            self.progress.create("Artwork Beef: " + L(ADDING_ARTWORK_MESSAGE), "")
            self.visible = True

    def update_progress(self, percent, message, heading=None):
        if self.visible and settings.progressdisplay == PROGRESS_DISPLAY_FULLPROGRESS:
            self.progress.update(percent, heading, message)

    def finalupdate(self, header, message):
        if settings.final_notification:
            xbmcgui.Dialog().notification("Artwork Beef: " + header, message, '-', 8000)
        elif settings.progressdisplay == PROGRESS_DISPLAY_FULLPROGRESS:
            self.update_progress(100, message, header)
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

    def init_run(self, show_progress=False):
        self.setlanguages()
        self.gatherer = Gatherer(self.monitor, settings.only_filesystem, self.autolanguages)
        self.downloader = FileManager()
        self.freshstart = str(datetime_now() - timedelta(days=365))
        if show_progress:
            self.create_progress()

    def finish_run(self):
        self.close_progress()

    @property
    def processor_busy(self):
        # DEPRECATED: StringCompare is deprecated in Krypton, gone in Leia
        return pykodi.get_conditional('![StringCompare(Window(Home).Property(ArtworkBeef.Status),idle) | String.IsEqual(Window(Home).Property(ArtworkBeef.Status),idle)]')

    def process_item(self, mediatype, dbid, mode):
        if self.processor_busy:
            return
        if mode == MODE_GUI:
            busy = pykodi.get_busydialog()
            busy.create()
        if mediatype in mediatypes.artinfo and (mediatype not in mediatypes.audiotypes or get_kodi_version() >= 18):
            mediaitem = info.MediaItem(quickjson.get_item_details(dbid, mediatype))
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
        if not mediaitem.uniqueids and not settings.only_filesystem:
            if mediatype == mediatypes.MOVIESET:
                self.manual_id(mediaitem)
        if mode == MODE_GUI:
            self._manual_item_process(mediaitem, busy)
        else:
            medialist = [mediaitem]
            if mediatype == mediatypes.TVSHOW and not mediatypes.disabled(mediatypes.EPISODE):
                if mediaitem.uniqueids and any(x in mediaitem.uniqueids.itervalues() for x in settings.autoadd_episodes):
                    medialist.extend(info.MediaItem(ep) for ep in quickjson.get_episodes(dbid))
                elif settings.generate_episode_thumb or settings.download_artwork:
                    for episode in quickjson.get_episodes(dbid):
                        if settings.generate_episode_thumb and not info.has_generated_thumbnail(episode) \
                        or settings.download_artwork and info.has_art_todownload(episode['art']):
                            episode = info.MediaItem(episode)
                            episode.skip_artwork = ['fanart']
                            medialist.append(episode)
            elif mediatype == mediatypes.ARTIST and not mediatypes.disabled(mediatypes.ALBUM):
                medialist.extend(info.MediaItem(album) for album in quickjson.get_albums(mediaitem.dbid))
            if mediatype in (mediatypes.ALBUM, mediatypes.ARTIST) and not mediatypes.disabled(mediatypes.SONG):
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
                    self.downloader.handle_removed_files(mediaitem)
                if settings.download_artwork:
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
                reporting.report_item(mediaitem, True, True)
                if not mediaitem.error:
                    notifycount(len(toset))
        else:
            xbmcgui.Dialog().notification(L(NOT_AVAILABLE_MESSAGE),
                L(SOMETHING_MISSING) + ' ' + L(FINAL_MESSAGE), '-', 8000)
        self.finish_run()

    def process_medialist(self, medialist, alwaysnotify=False):
        self.init_run(len(medialist) > 0)
        artcount = 0
        currentitem = 0
        aborted = False
        singleitemlist = len(medialist) == 1
        if not singleitemlist:
            reporting.report_start(medialist)
        for mediaitem in medialist:
            if mediaitem.mediatype in mediatypes.audiotypes and get_kodi_version() < 18:
                continue
            self.update_progress(currentitem * 100 // len(medialist), mediaitem.label)
            info.add_additional_iteminfo(mediaitem, self.processed, search)
            currentitem += 1
            try:
                services_hit = self._process_item(mediaitem)
            except FileError as ex:
                mediaitem.error = ex.message
                log(ex.message, xbmc.LOGERROR)
                self.notify_warning(ex.message, None, True)
                reporting.report_item(mediaitem, True)
                aborted = True
                break
            reporting.report_item(mediaitem, singleitemlist or mediaitem.error)
            artcount += len(mediaitem.updatedart)

            if not services_hit:
                if self.monitor.abortRequested():
                    aborted = True
                    break
            elif self.monitor.waitForAbort(THROTTLE_TIME):
                aborted = True
                break

        reporting.report_end(medialist, currentitem if aborted else 0, self.downloader.size)
        if artcount or alwaysnotify:
            self.finalupdate(*finalmessages(artcount))
        self.finish_run()
        return not aborted

    def _process_item(self, mediaitem, singleitem=False, auto=True):
        mediatype = mediaitem.mediatype
        if not mediaitem.uniqueids and not settings.only_filesystem:
            header = L(NO_IDS_MESSAGE)
            mediaitem.error = header
            if singleitem:
                message = "{0} '{1}'".format(mediatype, mediaitem.label)
                log(header + ": " + message, xbmc.LOGNOTICE)
                xbmcgui.Dialog().notification("Artwork Beef: " + header, message, xbmcgui.NOTIFICATION_INFO)

        if auto:
            cleaned = get_simpledict_updates(mediaitem.art, cleaner.clean_artwork(mediaitem))
            if cleaned:
                add_art_to_library(mediatype, mediaitem.seasons, mediaitem.dbid, cleaned)
                mediaitem.art.update(cleaned)
                mediaitem.art = dict(item for item in mediaitem.art.iteritems() if item[1])
                mediaitem.updatedart = cleaned.keys()

        existingkeys = [key for key, url in mediaitem.art.iteritems() if url]
        mediaitem.missingart = list(info.iter_missing_arttypes(mediaitem, existingkeys))

        services_hit, error = self.gatherer.getartwork(mediaitem, auto)

        if auto:
            existingart = dict(mediaitem.art)
            selectedart = dict((key, image['url']) for key, image in mediaitem.forcedart.iteritems())
            existingart.update(selectedart)

            # Then add the rest of the missing art
            existingkeys = [key for key, url in existingart.iteritems() if url]
            selectedart.update(self.get_top_missing_art(info.iter_missing_arttypes(mediaitem, existingkeys),
                mediatype, existingart, mediaitem.availableart))

            selectedart = get_simpledict_updates(mediaitem.art, selectedart)
            mediaitem.selectedart = selectedart
            toset = dict(selectedart)
            if settings.remove_deselected_files:
                self.downloader.handle_removed_files(mediaitem)
            if settings.download_artwork:
                sh, er = self.downloader.downloadfor(mediaitem)
                services_hit = services_hit or sh
                error = error or er
                toset.update(mediaitem.downloadedart)
            if toset:
                mediaitem.updatedart = list(set(mediaitem.updatedart + toset.keys()))
                add_art_to_library(mediatype, mediaitem.seasons, mediaitem.dbid, toset)

        if error:
            if 'message' in error:
                header = L(PROVIDER_ERROR_MESSAGE).format(error['providername'])
                msg = '{0}: {1}'.format(header, error['message'])
                mediaitem.error = msg
                log(msg, xbmc.LOGWARNING)
                self.notify_warning(error['message'], header)
        elif auto:
            if not (mediatype == mediatypes.EPISODE and 'fanart' in mediaitem.skip_artwork) and \
                    mediatype != mediatypes.SONG:
                self.processed.set_nextdate(mediaitem.dbid, mediatype, mediaitem.label,
                    datetime_now() + timedelta(days=self.get_nextcheckdelay(mediaitem)))
            if mediatype == mediatypes.TVSHOW:
                self.processed.set_data(mediaitem.dbid, mediatype, mediaitem.label, mediaitem.season)
        return services_hit

    def get_nextcheckdelay(self, mediaitem):
        if settings.only_filesystem and not mediaitem.mediatype in (mediatypes.ARTIST, mediatypes.ALBUM):
            return plus_some(15, 3)
        elif not mediaitem.uniqueids:
            return plus_some(30, 5)
        elif not mediaitem.missingart:
            return plus_some(120, 25)
        elif mediaitem.mediatype in (mediatypes.MOVIE, mediatypes.TVSHOW) and \
                mediaitem.premiered > self.freshstart:
            return plus_some(30, 10)
        elif mediaitem.mediatype in (mediatypes.ARTIST, mediatypes.ALBUM):
            return plus_some(120, 25)
        else:
            return plus_some(60, 15)

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
        languages = [pykodi.get_language(xbmc.ISO_639_1)]
        if settings.language_override and settings.language_override not in languages:
            languages.insert(0, settings.language_override)
        if 'en' not in languages:
            languages.append('en')
        languages.append(None)
        self.autolanguages = languages

    def get_top_missing_art(self, missingarts, mediatype, existingart, availableart):
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

                newart = [art for art in availableart[missingart] if self._auto_filter(missingart, art, existingurls)]
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
                newart = next((art for art in availableart[missingart] if self._auto_filter(missingart, art)), None)
                if newart:
                    newartwork[missingart] = newart['url']
        return newartwork

    def _auto_filter(self, arttype, art, ignoreurls=()):
        if art['rating'].sort < settings.minimum_rating:
            return False
        if arttype.endswith('fanart') and art['size'].sort < settings.minimum_size:
            return False
        return art['language'] in self.autolanguages and art['url'] not in ignoreurls

def add_art_to_library(mediatype, seasons, dbid, selectedart):
    if not selectedart:
        return
    if mediatype == mediatypes.TVSHOW:
        for season, season_id in seasons.iteritems():
            info.update_art_in_library(mediatypes.SEASON, season_id, dict((arttype.split('.')[2], url)
                for arttype, url in selectedart.iteritems() if arttype.startswith('season.{0}.'.format(season))))
        info.update_art_in_library(mediatype, dbid, dict((arttype, url)
            for arttype, url in selectedart.iteritems() if '.' not in arttype))
    else:
        info.update_art_in_library(mediatype, dbid, selectedart)
    for arttype, url in selectedart.iteritems():
        # Remove local images from cache so Kodi caches the new ones
        if not url or url.startswith(pykodi.notlocalimages):
            continue
        textures = quickjson.get_textures(url)
        if textures:
            quickjson.remove_texture(textures[0]['textureid'])

def finalmessages(count):
    return (L(ARTWORK_UPDATED_MESSAGE).format(count), L(FINAL_MESSAGE)) if count else \
        (L(NO_ARTWORK_UPDATED_MESSAGE), L(SOMETHING_MISSING) + ' ' + L(FINAL_MESSAGE))

def notifycount(count):
    header, message = finalmessages(count)
    xbmcgui.Dialog().notification("Artwork Beef: " + header, message, '-', 8000)

def plus_some(start, rng):
    return start + (random.randrange(-rng, rng + 1))

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
