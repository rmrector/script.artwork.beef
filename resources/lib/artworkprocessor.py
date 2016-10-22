import re
import xbmc
import xbmcgui

from devhelper import pykodi
from devhelper import quickjson
from devhelper.pykodi import log

import mediatypes
from artworkselection import prompt_for_artwork
from gatherer import Gatherer, list_missing_arttypes
from utils import SortedDisplay, natural_sort, localize as L

addon = pykodi.get_main_addon()

MODE_AUTO = 'auto'
MODE_GUI = 'gui'

THROTTLE_TIME = 0.15

DEFAULT_IMAGESIZE = '1920x1080'
imagesizes = {'1920x1080': (1920, 1080, 700), '1280x720': (1280, 720, 520)}

tvshow_properties = ['art', 'imdbnumber', 'season', 'file']
movie_properties = ['art', 'imdbnumber', 'file']
episode_properties = ['art', 'uniqueid', 'tvshowid', 'season', 'file']

SOMETHING_MISSING = 32001
FINAL_MESSAGE = 32019
ADDING_ARTWORK_MESSAGE = 32020
NOT_AVAILABLE_MESSAGE = 32021
ARTWORK_ADDED_MESSAGE = 32022
NO_ARTWORK_ADDED_MESSAGE = 32023
PROVIDER_ERROR_MESSAGE = 32024
NOT_SUPPORTED_MESSAGE = 32025
CURRENT_ART = 13512

class ArtworkProcessor(object):
    def __init__(self, monitor=None):
        self.monitor = monitor or xbmc.Monitor()
        self.language = None
        self.autolanguages = None
        self.progress = xbmcgui.DialogProgressBG()
        self.visible = False
        self.update_settings()

    def update_settings(self):
        self.titlefree_fanart = addon.get_setting('titlefree_fanart')
        self.only_filesystem = addon.get_setting('only_filesystem')
        try:
            self.minimum_rating = int(addon.get_setting('minimum_rating'))
        except ValueError:
            self.minimum_rating = 5
        sizesetting = addon.get_setting('preferredsize')
        if sizesetting in imagesizes:
            self.preferredsize = imagesizes[sizesetting][0:2]
            self.minimum_size = imagesizes[sizesetting][2]
        else:
            self.preferredsize = imagesizes[DEFAULT_IMAGESIZE][0:2]
            self.minimum_size = imagesizes[DEFAULT_IMAGESIZE][2]
            addon.set_setting('preferredsize', DEFAULT_IMAGESIZE)

    def create_progress(self):
        if not self.visible:
            self.progress.create(L(ADDING_ARTWORK_MESSAGE), "")
            self.visible = True

    def close_progress(self):
        if self.visible:
            self.progress.close()
            self.visible = False

    def init_run(self, show_progress=False):
        self.setlanguages()
        if show_progress:
            self.create_progress()

    def finish_run(self):
        self.close_progress()

    @property
    def processor_busy(self):
        return pykodi.get_conditional('!StringCompare(Window(Home).Property(ArtworkBeef.Status),idle)')

    def process_item(self, mediatype, dbid, mode):
        if self.processor_busy:
            return
        if mode == MODE_GUI:
            xbmc.executebuiltin('ActivateWindow(busydialog)')
        if mediatype == mediatypes.TVSHOW:
            mediaitem = quickjson.get_tvshow_details(dbid, tvshow_properties)
        elif mediatype == mediatypes.MOVIE:
            mediaitem = quickjson.get_movie_details(dbid, movie_properties)
        elif mediatype == mediatypes.EPISODE:
            mediaitem = quickjson.get_episode_details(dbid, episode_properties)
        else:
            xbmc.executebuiltin('Dialog.Close(busydialog)')
            xbmcgui.Dialog().notification("Artwork Beef", L(NOT_SUPPORTED_MESSAGE).format(mediatype), '-', 6500)
            return

        if mode == MODE_GUI:
            self.init_run()
            self.add_additional_iteminfo(mediaitem)
            gatherer = Gatherer(self.monitor, self.only_filesystem)
            forcedart, availableart, _, error = gatherer.getartwork(mediaitem, False)
            if error:
                header = L(PROVIDER_ERROR_MESSAGE).format(error['providername'])
                xbmcgui.Dialog().notification(header, error['message'], xbmcgui.NOTIFICATION_ERROR)
                log('{0}\n{1}'.format(header, error['message']))

            for arttype, imagelist in availableart.iteritems():
                self.sort_images(arttype, imagelist, mediaitem['file'])
            xbmc.executebuiltin('Dialog.Close(busydialog)')
            if availableart:
                tag_forcedandexisting_art(availableart, forcedart, mediaitem['art'])
                selectedarttype, selectedart = prompt_for_artwork(mediaitem['mediatype'],
                    mediaitem['label'], availableart, self.monitor)
                if selectedarttype:
                    multiselect = False
                    if selectedarttype.startswith('season.'):
                        gentype = selectedarttype.rsplit('.', 1)[1]
                        multiselect = mediatypes.artinfo[mediatypes.SEASON].get(gentype)
                        if multiselect:
                            multiselect = multiselect['multiselect']
                    else:
                        multiselect = mediatypes.artinfo[mediaitem['mediatype']][selectedarttype]['multiselect']
                    if multiselect:
                        existingurls = [url for exacttype, url in mediaitem['art'].iteritems() if exacttype.startswith(selectedarttype)]
                        urls_toset = [url for url in existingurls if url not in selectedart[1]]
                        newurls = [url for url in selectedart[0] if url not in urls_toset]
                        count = len(newurls)
                        urls_toset.extend(newurls)
                        selectedart = {}
                        i = 0
                        for url in urls_toset:
                            selectedart[selectedarttype + (str(i) if i else '')] = url
                            i += 1
                        selectedart.update(dict((arttype, None) for arttype in mediaitem['art'].keys()
                            if arttype.startswith(selectedarttype) and arttype not in selectedart.keys()))
                    else:
                        selectedart = {selectedarttype: selectedart}
                        count = 1
                    add_art_to_library(mediaitem['mediatype'], mediaitem.get('seasons'), mediaitem['dbid'], selectedart)
                    notifycount(count)
            else:
                xbmcgui.Dialog().notification(L(NOT_AVAILABLE_MESSAGE),
                    L(SOMETHING_MISSING) + ' ' + L(FINAL_MESSAGE), '-', 8000)
            self.finish_run()
        else:
            medialist = [mediaitem]
            autoaddepisodes = addon.get_setting('autoaddepisodes_list') if addon.get_setting('episode.fanart') else ()
            if mediatype == mediatypes.TVSHOW and mediaitem['imdbnumber'] in autoaddepisodes:
                medialist.extend(quickjson.get_episodes(dbid, properties=episode_properties))
            self.process_medialist(medialist, True)

    def process_medialist(self, medialist, alwaysnotify=False, stop_on_error=False):
        self.init_run(len(medialist) > 0)
        processed = {'tvshow': {}, 'movie': [], 'episode': []}
        artcount = 0
        currentitem = 0
        if medialist:
            gatherer = Gatherer(self.monitor, self.only_filesystem)
        for mediaitem in medialist:
            if self.visible:
                self.progress.update(currentitem * 100 // len(medialist), message=mediaitem['label'])
                currentitem += 1
            self.add_additional_iteminfo(mediaitem)
            forcedart, availableart, services_hit, error = gatherer.getartwork(mediaitem)
            if error:
                header = L(PROVIDER_ERROR_MESSAGE).format(error['providername'])
                xbmcgui.Dialog().notification(header, error['message'], xbmcgui.NOTIFICATION_ERROR)
                log('{0}\n{1}'.format(header, error['message']))
                if stop_on_error:
                    break
            add_processeditem(processed, mediaitem)
            for arttype, imagelist in availableart.iteritems():
                self.sort_images(arttype, imagelist, mediaitem['file'])
            existingart = dict(mediaitem['art'])
            selectedart = {}
            # Remove existing local artwork if it is no longer available
            localurls = [(arttype, image['url']) for arttype, image in forcedart.iteritems() if not image['url'].startswith(('http', 'image://video'))]
            for arttype, url in existingart.iteritems():
                if ('.' not in arttype or arttype.startswith('season.')) and \
                        not url.startswith(('http', 'image://video')) and \
                        (arttype, url) not in localurls:
                    selectedart[arttype] = None
            selectedart.update(dict((key, image['url']) for key, image in forcedart.iteritems()))
            existingart.update(selectedart)

            selectedart.update(self.get_top_missing_art(mediaitem['mediatype'], existingart, availableart, mediaitem.get('seasons')))
            # don't set already existing artwork
            selectedart = dict((arttype, url) for arttype, url in selectedart.iteritems() if url != mediaitem['art'].get(arttype))
            if selectedart:
                add_art_to_library(mediaitem['mediatype'], mediaitem.get('seasons'), mediaitem['dbid'], selectedart)
                artcount += sum(1 for url in selectedart.values() if url)
            if not services_hit:
                if self.monitor.abortRequested():
                    break
            elif self.monitor.waitForAbort(THROTTLE_TIME):
                break
        self.finish_run()
        if alwaysnotify or artcount:
            notifycount(artcount)
        return processed

    def setlanguages(self):
        self.language = pykodi.get_language(xbmc.ISO_639_1)
        if self.language == 'en':
            self.autolanguages = (self.language, None)
        else:
            self.autolanguages = (self.language, 'en', None)

    def add_additional_iteminfo(self, mediaitem):
        log('Processing {0}'.format(mediaitem['label']), xbmc.LOGINFO)
        if 'episodeid' in mediaitem:
            mediaitem['mediatype'] = mediatypes.EPISODE
            mediaitem['dbid'] = mediaitem['episodeid']
            mediaitem['imdbnumber'] = self._get_episodeid(mediaitem)
            # Remove existing tvshow.* and season.* artwork
            mediaitem['art'] = dict((arttype, url) for arttype, url in mediaitem['art'].iteritems() if '.' not in arttype)
        elif 'tvshowid' in mediaitem:
            mediaitem['mediatype'] = mediatypes.TVSHOW
            mediaitem['dbid'] = mediaitem['tvshowid']
            mediaitem['seasons'], art = self._get_seasons_artwork(quickjson.get_seasons(mediaitem['dbid']))
            mediaitem['art'].update(art)
        elif 'movieid' in mediaitem:
            mediaitem['mediatype'] = mediatypes.MOVIE
            mediaitem['dbid'] = mediaitem['movieid']
        else:
            log('Not sure what mediatype this is.', xbmc.LOGWARNING)
            log(mediaitem, xbmc.LOGWARNING)
            return False

        mediaitem['art'] = dict((arttype, pykodi.unquoteimage(url)) for arttype, url in mediaitem['art'].iteritems())
        return True

    def sort_images(self, arttype, imagelist, mediapath):
        # 1. Language, preferring fanart with no language/title if configured
        # 2. Match discart to media source
        # 3. Size (in 200px groups), up to preferredsize
        # 4. Rating
        imagelist.sort(key=lambda image: image['rating'].sort, reverse=True)
        imagelist.sort(key=self.size_sort, reverse=True)
        if arttype == 'discart':
            mediasubtype = get_media_source(mediapath)
            if mediasubtype != 'unknown':
                imagelist.sort(key=lambda image: 0 if image.get('subtype', SortedDisplay(None, '')).sort == mediasubtype else 1)
        imagelist.sort(key=lambda image: self._imagelanguage_sort(image, arttype))

    def size_sort(self, image):
        imagesplit = image['size'].display.split('x')
        if len(imagesplit) != 2:
            return image['size'].sort
        try:
            imagesize = int(imagesplit[0]), int(imagesplit[1])
        except ValueError:
            return image['size'].sort
        if imagesize[0] > self.preferredsize[0]:
            shrink = self.preferredsize[0] / float(imagesize[0])
            imagesize = self.preferredsize[0], imagesize[1] * shrink
        if imagesize[1] > self.preferredsize[1]:
            shrink = self.preferredsize[1] / float(imagesize[1])
            imagesize = imagesize[0] * shrink, self.preferredsize[1]
        return max(imagesize) // 200

    def _imagelanguage_sort(self, image, arttype):
        primary = 0
        if arttype.endswith('fanart'):
            if image['language'] == self.language:
                primary = 1 if self.titlefree_fanart else 0
            else:
                primary = 2 if image['language'] else 0
        else:
            primary = 0 if image['language'] == self.language else 1
        return primary, image['language']

    def get_top_missing_art(self, mediatype, existingart, availableart, seasons):
        if not availableart:
            return {}
        newartwork = {}
        existingkeys = [key for key, url in existingart.iteritems() if url]
        for missingart in list_missing_arttypes(mediatype, seasons, existingkeys):
            if missingart.startswith(mediatypes.SEASON):
                itemtype = mediatypes.SEASON
                artkey = missingart.rsplit('.', 1)[1]
            else:
                itemtype = mediatype
                artkey = missingart
            if missingart not in availableart:
                continue
            if mediatypes.artinfo[itemtype][artkey]['multiselect']:
                existingurls = []
                existingartnames = []
                for art, url in existingart.iteritems():
                    if art.startswith(missingart) and url:
                        existingurls.append(url)
                        existingartnames.append(art)

                newart = [art for art in availableart[missingart] if self._auto_filter(missingart, art, existingurls)]
                if not newart:
                    continue
                newartcount = 0
                for i in range(0, mediatypes.artinfo[itemtype][artkey]['autolimit']):
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

    def _get_seasons_artwork(self, seasons):
        resultseasons = {}
        resultart = {}
        for season in seasons:
            resultseasons[season['season']] = season['seasonid']
            for arttype, url in season['art'].iteritems():
                if not arttype.startswith(('tvshow.', 'season.')):
                    resultart['%s.%s.%s' % (mediatypes.SEASON, season['season'], arttype)] = url
        return resultseasons, resultart

    def _get_episodeid(self, episode):
        if 'unknown' in episode['uniqueid']:
            return episode['uniqueid']['unknown']
        else:
            idsource, result = episode['uniqueid'].iteritems()[0] if episode['uniqueid'] else '', ''
            if result:
                # I don't know what this might be, I'm not even sure Kodi can do anything else at the moment, but just in case
                log("Didn't find 'unknown' uniqueid for episode, just picked the first, from '%s'." % idsource, xbmc.LOGINFO)
            else:
                log("Didn't find a uniqueid for episode '%s', can't look it up. I expect the ID from TheTVDB, which generally comes from the scraper." % episode['label'], xbmc.LOGNOTICE)
            return result

    def _auto_filter(self, arttype, art, ignoreurls=()):
        if art['rating'].sort < self.minimum_rating:
            return False
        if arttype.endswith('fanart') and art['size'].sort < self.minimum_size:
            return False
        return art['language'] in self.autolanguages and art['url'] not in ignoreurls

def add_art_to_library(mediatype, seasons, dbid, selectedart):
    if not selectedart:
        return
    if mediatype == mediatypes.TVSHOW:
        seriesart = {}
        allseasonart = {}
        for arttype, url in selectedart.iteritems():
            if arttype.startswith(mediatypes.SEASON + '.'):
                season, arttype = arttype.rsplit('.', 2)[1:3]
                season = seasons[int(season)]
                if season not in allseasonart:
                    allseasonart[season] = {}
                allseasonart[season][arttype] = url
            else:
                seriesart[arttype] = url
        if seriesart:
            quickjson.set_tvshow_details(dbid, art=seriesart)
        for seasonid, seasonart in allseasonart.iteritems():
            quickjson.set_season_details(seasonid, art=seasonart)
    elif mediatype == mediatypes.MOVIE:
        quickjson.set_movie_details(dbid, art=selectedart)
    elif mediatype == mediatypes.EPISODE:
        quickjson.set_episode_details(dbid, art=selectedart)

def notifycount(count):
    log(L(ARTWORK_ADDED_MESSAGE).format(count), xbmc.LOGINFO)
    if count:
        xbmcgui.Dialog().notification(L(ARTWORK_ADDED_MESSAGE).format(count), L(FINAL_MESSAGE), '-', 7500)
    else:
        xbmcgui.Dialog().notification(L(NO_ARTWORK_ADDED_MESSAGE),
            L(SOMETHING_MISSING) + ' ' + L(FINAL_MESSAGE), '-', 8000)

def add_processeditem(processed, mediaitem):
    if mediaitem['mediatype'] == 'tvshow':
        processed['tvshow'][mediaitem['dbid']] = mediaitem['season']
    else:
        processed[mediaitem['mediatype']].append(mediaitem['dbid'])

def get_media_source(mediapath):
    mediapath = mediapath.lower()
    if re.search(r'\b3d\b', mediapath):
        return '3d'
    if re.search(r'blu-?ray|b[rd]-?rip', mediapath) or mediapath.endswith('.bdmv'):
        return 'bluray'
    if re.search(r'\bdvd', mediapath) or mediapath.endswith('.ifo'):
        return 'dvd'
    return 'unknown'

def tag_forcedandexisting_art(availableart, forcedart, existingart):
    typeinsert = {}
    for exacttype, artlist in sorted(forcedart.iteritems(), key=lambda arttype: natural_sort(arttype[0])):
        arttype = exacttype.rstrip('0123456789')
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
        arttype = exacttype.rstrip('0123456789')
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
