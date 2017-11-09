import random
import xbmc
import xbmcgui
from datetime import timedelta

from lib import cleaner, reporting
from lib.artworkselection import prompt_for_artwork
from lib.gatherer import Gatherer
from lib.libs import mediainfo as info, mediatypes, pykodi, quickjson
from lib.libs.addonsettings import settings
from lib.libs.processeditems import ProcessedItems
from lib.libs.pykodi import datetime_now, localize as L, log
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

    def create_progress(self):
        if not self.visible:
            self.progress.create("Artwork Beef: " + L(ADDING_ARTWORK_MESSAGE), "")
            self.visible = True

    def update_progress(self, percent, message):
        if self.visible:
            self.progress.update(percent, message=message)

    def close_progress(self):
        if self.visible:
            self.progress.close()
            self.visible = False

    def init_run(self, show_progress=False):
        self.setlanguages()
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
        if mediatype in mediatypes.artinfo:
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
            if mediatype == mediatypes.TVSHOW:
                if mediaitem.uniqueids and any(x in mediaitem.uniqueids.itervalues() for x in settings.autoadd_episodes):
                    medialist.extend(info.MediaItem(ep) for ep in quickjson.get_episodes(dbid))
                elif settings.generate_episode_thumb:
                    for episode in quickjson.get_episodes(dbid):
                        if not info.has_generated_thumbnail(episode):
                            episode = info.MediaItem(episode)
                            episode.skip_artwork = ['fanart']
                            medialist.append(episode)
            self.process_medialist(medialist, True)

    def _manual_item_process(self, mediaitem, busy):
        self._process_item(Gatherer(self.monitor, settings.only_filesystem, self.autolanguages), mediaitem, True, False)
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
                    existingurls = [url for exacttype, url in mediaitem.art.iteritems()
                        if info.arttype_matches_base(exacttype, selectedarttype)]
                    urls_toset = [url for url in existingurls if url not in selectedart[1]]
                    urls_toset.extend([url for url in selectedart[0] if url not in urls_toset])
                    selectedart = dict(info.iter_renumbered_artlist(urls_toset, selectedarttype, mediaitem.art.keys()))
                else:
                    selectedart = {selectedarttype: selectedart}

                selectedart = get_simpledict_updates(mediaitem.art, selectedart)
                if selectedart:
                    mediaitem.selectedart = selectedart
                    mediaitem.updatedart = selectedart.keys()
                    add_art_to_library(mediaitem.mediatype, mediaitem.seasons, mediaitem.dbid, selectedart)
                reporting.report_item(mediaitem, True, True)
                notifycount(len(selectedart))
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
        if medialist:
            gatherer = Gatherer(self.monitor, settings.only_filesystem, self.autolanguages)
        for mediaitem in medialist:
            self.update_progress(currentitem * 100 // len(medialist), mediaitem.label)
            info.add_additional_iteminfo(mediaitem, self.processed, search)
            currentitem += 1
            services_hit = self._process_item(gatherer, mediaitem)
            reporting.report_item(mediaitem, singleitemlist)
            artcount += len(mediaitem.updatedart)

            if not services_hit:
                if self.monitor.abortRequested():
                    aborted = True
                    break
            elif self.monitor.waitForAbort(THROTTLE_TIME):
                aborted = True
                break

        self.finish_run()
        reporting.report_end(medialist, currentitem if aborted else 0)
        if artcount or alwaysnotify:
            notifycount(artcount)
        return not aborted

    def _process_item(self, gatherer, mediaitem, singleitem=False, auto=True):
        mediatype = mediaitem.mediatype
        if not mediaitem.uniqueids and not settings.only_filesystem:
            header = L(NO_IDS_MESSAGE)
            mediaitem.error = header
            if singleitem:
                message = "{0} '{1}'".format(mediatype, mediaitem.label)
                log(header + ": " + message, xbmc.LOGNOTICE)
                log(mediaitem, xbmc.LOGNOTICE)
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

        services_hit, error = gatherer.getartwork(mediaitem, auto)

        if auto:
            # Remove existing local artwork if it is no longer available
            existingart = dict(mediaitem.art)
            localart = [(arttype, image['url']) for arttype, image in mediaitem.forcedart.iteritems()
                if not image['url'].startswith('http')]
            selectedart = dict((arttype, None) for arttype, url in existingart.iteritems()
                if not url.startswith(('http', 'image://video@')) and arttype not in ('animatedposter', 'animatedfanart')
                    and (arttype, url) not in localart)

            selectedart.update((key, image['url']) for key, image in mediaitem.forcedart.iteritems())
            selectedart = info.renumber_all_artwork(selectedart)

            existingart.update(selectedart)

            # Then add the rest of the missing art
            existingkeys = [key for key, url in existingart.iteritems() if url]
            selectedart.update(self.get_top_missing_art(info.iter_missing_arttypes(mediaitem, existingkeys),
                mediatype, existingart, mediaitem.availableart))

            # Identify actual changes, and save them
            selectedart = get_simpledict_updates(mediaitem.art, selectedart)
            if selectedart:
                mediaitem.selectedart = selectedart
                mediaitem.updatedart = list(set(mediaitem.updatedart + selectedart.keys()))
                add_art_to_library(mediatype, mediaitem.seasons, mediaitem.dbid, mediaitem.selectedart)

        if error:
            if 'message' in error:
                header = L(PROVIDER_ERROR_MESSAGE).format(error['providername'])
                msg = '{0}: {1}'.format(header, error['message'])
                mediaitem.error = msg
                log(msg, xbmc.LOGWARNING)
                xbmcgui.Dialog().notification(header, error['message'], xbmcgui.NOTIFICATION_WARNING)
        elif auto:
            if not (mediatype == mediatypes.EPISODE and 'fanart' in mediaitem.skip_artwork):
                self.processed.set_nextdate(mediaitem.dbid, mediatype, mediaitem.label,
                    datetime_now() + timedelta(days=self.get_nextcheckdelay(mediaitem)))
            if mediatype == mediatypes.TVSHOW:
                self.processed.set_data(mediaitem.dbid, mediatype, mediaitem.label, mediaitem.season)
        return services_hit

    def get_nextcheckdelay(self, mediaitem):
        if settings.only_filesystem:
            return plus_some(5, 3)
        elif not mediaitem.uniqueids:
            return plus_some(30, 5)
        elif not mediaitem.missingart:
            return plus_some(120, 25)
        elif mediaitem.mediatype in (mediatypes.MOVIE, mediatypes.TVSHOW) and \
                mediaitem.premiered > self.freshstart:
            return plus_some(30, 10)
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
        if not toset and 'mbid_track' in uq and 'mbid_album' in uq and 'mbid_artist' in uq:
            toset = '{0}/{1}/{2}'.format(uq['mbid_track'], uq['mbid_album'], uq['mbid_artist'])
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

def notifycount(count):
    if count:
        xbmcgui.Dialog().notification("Artwork Beef: " + L(ARTWORK_UPDATED_MESSAGE).format(count), L(FINAL_MESSAGE), '-', 7500)
    else:
        xbmcgui.Dialog().notification("Artwork Beef: " + L(NO_ARTWORK_UPDATED_MESSAGE),
            L(SOMETHING_MISSING) + ' ' + L(FINAL_MESSAGE), '-', 8000)

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
