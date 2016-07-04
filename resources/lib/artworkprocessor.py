import re
import xbmc
import xbmcgui

from devhelper import pykodi
from devhelper import quickjson
from devhelper.pykodi import log

import mediatypes
import providers
from utils import SortedDisplay, natural_sort
from artworkselection import ArtworkTypeSelector, ArtworkSelector
from providers import ProviderError

addon = pykodi.get_main_addon()

MODE_AUTO = 'auto'
MODE_GUI = 'gui'

HAPPY_IMAGE = SortedDisplay(0, 'happy')
NOAUTO_IMAGE = SortedDisplay(0, 'noauto')
GOOFY_IMAGE = SortedDisplay(1, 'goofy')

THROTTLE_TIME = 0.15

DEFAULT_IMAGESIZE = '1920x1080'
imagesizes = {'1920x1080': (1920, 1080, 700), '1280x720': (1280, 720, 520)}

tvshow_properties = ['art', 'imdbnumber', 'season', 'file']
movie_properties = ['art', 'imdbnumber', 'file']
episode_properties = ['art', 'uniqueid', 'tvshowid', 'season', 'file']

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
            self.progress.create("Adding extended artwork", "")
            self.visible = True

    def close_progress(self):
        if self.visible:
            self.progress.close()
            self.visible = False

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
            xbmcgui.Dialog().notification("Artwork Beef", "Media type '{0}' not currently supported.".format(mediatype), '-', 6500)
            return

        if mode == MODE_GUI:
            self.setlanguages()
            self.add_additional_iteminfo(mediaitem)
            artwork_requested = self.find_available_artwork(mediaitem, MODE_GUI)
            xbmc.executebuiltin('Dialog.Close(busydialog)')
            if not artwork_requested or not mediaitem.get('available art'):
                xbmcgui.Dialog().notification('No artwork available', "Something missing? Contribute or donate to the source\nfanart.tv, thetvdb.com, themoviedb.org", '-', 6500)
                return
            selected, count = self.prompt_for_artwork(mediaitem)
            if not selected:
                return
            mediaitem['selected art'] = selected
            self.add_art_to_library(mediaitem)
            notifycount(count)
        else:
            medialist = [mediaitem]
            autoaddepisodes = addon.get_setting('autoaddepisodes_list') if addon.get_setting('episode.fanart') else ()
            if mediatype == mediatypes.TVSHOW and mediaitem['imdbnumber'] in autoaddepisodes:
                medialist.extend(quickjson.get_episodes(dbid, properties=episode_properties))
            self.process_medialist(medialist, True)

    def process_medialist(self, medialist, alwaysnotify=False):
        if len(medialist) > 10:
            self.create_progress()
        processed = {'tvshow': {}, 'movie': [], 'episode': []}
        self.setlanguages()
        artcount = 0
        currentitem = 0
        for mediaitem in medialist:
            if self.visible:
                self.progress.update(currentitem * 100 // len(medialist), message=mediaitem['label'])
                currentitem += 1
            self.add_additional_iteminfo(mediaitem)
            artwork_requested = self.find_available_artwork(mediaitem, MODE_AUTO)
            if not artwork_requested:
                add_processeditem(processed, mediaitem)
                if self.monitor.abortRequested():
                    break
                continue
            if not mediaitem.get('available art') and not mediaitem.get('selected art'):
                add_processeditem(processed, mediaitem)
                if self.monitor.waitForAbort(THROTTLE_TIME):
                    break
                continue
            if 'selected art' in mediaitem:
                mediaitem['selected art'].update(self.get_top_missing_art(mediaitem))
            else:
                mediaitem['selected art'] = self.get_top_missing_art(mediaitem)
            self.add_art_to_library(mediaitem)
            artcount += len(mediaitem['selected art'])
            add_processeditem(processed, mediaitem)
            if self.monitor.waitForAbort(THROTTLE_TIME):
                break
        if self.visible:
            self.close_progress()
        if alwaysnotify or artcount:
            notifycount(artcount)
        return processed

    def find_available_artwork(self, mediaitem, mode):
        if mode == MODE_AUTO:
            result = False
            forcedartwork = self.get_forced_artwork(mediaitem)
            mediaitem['selected art'] = dict((arttype, image['url']) for arttype, image in forcedartwork.iteritems())
            result = True if mediaitem['selected art'] else False
            if not self.only_filesystem and next(self.list_missing_arttypes(mediaitem), False):
                mediaitem['available art'] = self.get_external_artwork(mediaitem)
                result = True
            return result
        else:
            localart = self.get_forced_artwork(mediaitem, True)
            mediaitem['available art'] = itemart = {}
            for exacttype in sorted(localart.keys(), key=natural_sort):
                arttype = exacttype.rstrip('0123456789')
                if arttype not in itemart:
                    itemart[arttype] = []
                itemart[arttype].extend(localart[exacttype])
            for arttype, artlist in self.get_external_artwork(mediaitem).iteritems():
                if arttype not in itemart:
                    itemart[arttype] = artlist
                else:
                    for art in artlist:
                        add_external_to_itemart(itemart, arttype, art, localart)
            return True

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
        elif 'tvshowid' in mediaitem:
            mediaitem['mediatype'] = mediatypes.TVSHOW
            mediaitem['dbid'] = mediaitem['tvshowid']
        elif 'movieid' in mediaitem:
            mediaitem['mediatype'] = mediatypes.MOVIE
            mediaitem['dbid'] = mediaitem['movieid']
        else:
            log('Not sure what mediatype this is.', xbmc.LOGWARNING)
            log(mediaitem, xbmc.LOGWARNING)
            return False
        if mediaitem['mediatype'] == mediatypes.TVSHOW:
            mediaitem['seasons'], art = self._get_seasons_artwork(quickjson.get_seasons(mediaitem['tvshowid']))
            mediaitem['art'].update(art)
        elif mediaitem['mediatype'] == mediatypes.EPISODE:
            mediaitem['imdbnumber'] = self._get_episodeid(mediaitem)

        return True

    def get_forced_artwork(self, mediaitem, allowmutiple=False):
        if mediaitem['mediatype'] not in (mediatypes.TVSHOW, mediatypes.MOVIE, mediatypes.EPISODE):
            return {}
        resultimages = {}
        for provider in providers.forced[mediaitem['mediatype']]:
            for arttype, image in provider.get_exact_images(mediaitem['file']).iteritems():
                if arttype.startswith('season.'):
                    season = arttype.rsplit('.', 2)[1]
                    if int(season) not in mediaitem['seasons']:
                        continue
                if allowmutiple:
                    if arttype not in resultimages:
                        resultimages[arttype] = []
                    resultimages[arttype].append(image)
                    self.apply_status(arttype, image)
                else:
                    if arttype not in resultimages:
                        resultimages[arttype] = image
                        self.apply_status(arttype, image)
            if self.monitor.abortRequested():
                break
        return resultimages

    def get_external_artwork(self, mediaitem):
        if mediaitem['mediatype'] not in (mediatypes.TVSHOW, mediatypes.MOVIE, mediatypes.EPISODE):
            return {}
        images = {}
        for provider in providers.external[mediaitem['mediatype']]:
            try:
                providerimages = provider.get_images(mediaitem['imdbnumber']).iteritems()
            except ProviderError as ex:
                header = 'Error with provider {0}'.format(provider.name.display)
                xbmcgui.Dialog().notification(header, ex.message, xbmcgui.NOTIFICATION_ERROR)
                log('{0}\n{1}'.format(header, ex.message))
                continue
            for arttype, artlist in providerimages:
                if arttype.startswith('season.'):
                    season = arttype.rsplit('.', 2)[1]
                    if int(season) not in mediaitem['seasons']:
                        # Don't add artwork for seasons we don't have
                        continue
                if arttype not in images:
                    images[arttype] = []
                images[arttype].extend(artlist)
            if self.monitor.abortRequested():
                break
        for arttype, imagelist in images.iteritems():
            [self.apply_status(arttype, image) for image in imagelist] #pylint: disable=W0106
            self.sort_images(arttype, imagelist, mediaitem['file'])
        return images

    def apply_status(self, arttype, image):
        image['status'] = HAPPY_IMAGE
        if arttype == 'fanart':
            if image.get('provider') == 'fanart.tv':
                image['status'] = NOAUTO_IMAGE
            if self.titlefree_fanart and image['language']:
                image['status'] = GOOFY_IMAGE

    def sort_images(self, arttype, imagelist, mediapath):
        # 1. Match the primary language, for everything but fanart
        # 2. Separate on status, like goofy images
        # 3. Size (in 200px groups), up to preferredsize
        # 4. Rating
        imagelist.sort(key=lambda image: image['rating'].sort, reverse=True)
        imagelist.sort(key=self.size_sort, reverse=True)
        imagelist.sort(key=lambda image: image['status'].sort)
        if arttype == 'discart':
            mediasubtype = get_media_subtype(mediapath)
            if mediasubtype != 'unknown':
                imagelist.sort(key=lambda image: 0 if image.get('subtype', SortedDisplay(None, '')).sort == mediasubtype else 1)
        if not arttype.endswith('fanart'):
            imagelist.sort(key=lambda image: (0 if image['language'] == self.language else 1, image['language']))

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

    def get_top_missing_art(self, mediaitem):
        if not mediaitem.get('available art'):
            return {}
        newartwork = {}
        for missingart in self.list_missing_arttypes(mediaitem):
            if missingart.startswith(mediatypes.SEASON):
                mediatype = mediatypes.SEASON
                artkey = missingart.rsplit('.', 1)[1]
            else:
                mediatype = mediaitem['mediatype']
                artkey = missingart
            if missingart not in mediaitem['available art']:
                continue
            if mediatypes.artinfo[mediatype][artkey]['multiselect']:
                existingurls = []
                existingartnames = []
                for art, url in mediaitem['art'].iteritems():
                    if art.startswith(missingart) and url:
                        existingurls.append(pykodi.unquoteimage(url))
                        existingartnames.append(art)

                missingartnames = []
                for i in range(0, mediatypes.artinfo[mediatype][artkey]['autolimit']):
                    multikey = '%s%s' % (artkey, i if i else '')
                    if multikey not in existingartnames:
                        missingartnames.append(multikey)

                newart = [art for art in mediaitem['available art'][missingart] if self._auto_filter(missingart, art, existingurls)]
                if not newart:
                    continue
                newartcount = 0
                for name in missingartnames:
                    if newartcount >= len(newart):
                        break
                    if name not in newartwork:
                        newartwork[name] = []
                    newartwork[name] = newart[newartcount]['url']
                    newartcount += 1
            else:
                newart = next((art for art in mediaitem['available art'][missingart] if self._auto_filter(missingart, art)), None)
                if newart:
                    newartwork[missingart] = newart['url']
        return newartwork

    def list_missing_arttypes(self, mediaitem):
        arttypes = mediaitem['art'].keys()
        if mediaitem.get('selected art'):
            arttypes.extend(mediaitem['selected art'].keys())
        fullartinfo = mediatypes.artinfo[mediaitem['mediatype']]
        for arttype, artinfo in fullartinfo.iteritems():
            if not artinfo['autolimit']:
                continue
            elif artinfo['autolimit'] == 1:
                if arttype not in arttypes:
                    yield arttype
            else:
                artcount = sum(1 for art in arttypes if art.startswith(arttype))
                if artcount < artinfo['autolimit']:
                    yield arttype

        if mediaitem['mediatype'] == mediatypes.TVSHOW:
            seasonartinfo = mediatypes.artinfo.get(mediatypes.SEASON)
            for season in mediaitem['seasons'].iteritems():
                for arttype, artinfo in seasonartinfo.iteritems():
                    arttype = '%s.%s.%s' % (mediatypes.SEASON, season[0], arttype)
                    if not artinfo['autolimit']:
                        continue
                    elif artinfo['autolimit'] == 1:
                        if arttype not in arttypes:
                            yield arttype
                    else:
                        artcount = sum(1 for art in arttypes if art.startswith(arttype))
                        if artcount < artinfo['autolimit']:
                            yield arttype

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

    def add_art_to_library(self, mediaitem):
        if not mediaitem.get('selected art'):
            return
        if mediaitem['mediatype'] == mediatypes.TVSHOW:
            seriesart = {}
            allseasonart = {}
            for arttype, url in mediaitem['selected art'].iteritems():
                if arttype.startswith(mediatypes.SEASON + '.'):
                    season, arttype = arttype.rsplit('.', 2)[1:3]
                    season = mediaitem['seasons'][int(season)]
                    if season not in allseasonart:
                        allseasonart[season] = {}
                    allseasonart[season][arttype] = url
                else:
                    seriesart[arttype] = url

            if seriesart:
                quickjson.set_tvshow_details(mediaitem['tvshowid'], art=seriesart)
            for seasonid, seasonart in allseasonart.iteritems():
                quickjson.set_season_details(seasonid, art=seasonart)

        elif mediaitem['mediatype'] == mediatypes.MOVIE:
            if mediaitem['selected art']:
                quickjson.set_movie_details(mediaitem['movieid'], art=mediaitem['selected art'])

        elif mediaitem['mediatype'] == mediatypes.EPISODE:
            if mediaitem['selected art']:
                quickjson.set_episode_details(mediaitem['episodeid'], art=mediaitem['selected art'])

    def _auto_filter(self, arttype, art, ignoreurls=()):
        if art['rating'].sort < 5:
            return False
        if arttype.endswith('fanart') and art['size'].sort < self.minimum_size:
            return False
        return (art['language'] in self.autolanguages or arttype.endswith('fanart')) and art['status'] != NOAUTO_IMAGE and art['url'] not in ignoreurls

    def prompt_for_artwork(self, mediaitem):
        if not mediaitem.get('available art'):
            return {}, 0
        items = [(arttype, len(artlist)) for arttype, artlist in mediaitem['available art'].iteritems()]
        typeselectwindow = ArtworkTypeSelector('DialogSelect.xml', addon.path, existingart=mediaitem['art'], arttypes=items, medialabel=mediaitem['label'])
        selectedart = None
        hqpreview = addon.get_setting('highquality_preview')
        singlewindow = len(items) == 1
        # The loop shows the first window if viewer backs out of the second
        while not selectedart:
            if singlewindow:
                selectedarttype = items[0][0]
            else:
                selectedarttype = typeselectwindow.prompt()
            if not selectedarttype:
                return {}, 0
            artlist = mediaitem['available art'][selectedarttype]
            if selectedarttype.startswith('season.'):
                stype = selectedarttype.rsplit('.', 1)[1]
                stype = mediatypes.artinfo[mediatypes.SEASON].get(stype)
            else:
                stype = mediatypes.artinfo[mediaitem['mediatype']].get(selectedarttype)
            multi = stype['multiselect'] if stype else False
            if multi:
                existingart = [pykodi.unquoteimage(url) for arttype, url in mediaitem['art'].iteritems() if arttype.startswith(selectedarttype)]
            else:
                existingart = []
                if selectedarttype in mediaitem['art']:
                    existingart.append(pykodi.unquoteimage(mediaitem['art'][selectedarttype]))
            artselectwindow = ArtworkSelector('DialogSelect.xml', addon.path, artlist=artlist, arttype=selectedarttype, medialabel=mediaitem['label'], existingart=existingart, multi=multi, hqpreview=hqpreview)
            selectedart = artselectwindow.prompt()
            if singlewindow and not selectedart:
                return {}, 0
            if self.monitor.abortRequested():
                return {}, 0

        if not multi:
            return {selectedarttype: selectedart}, 1

        for url in selectedart[1]:
            existingart.remove(url)
        existingart.extend(selectedart[0])

        result = {}
        count = 0
        for url in existingart:
            result[selectedarttype + (str(count) if count else '')] = url
            count += 1
        result.update(dict((arttype, None) for arttype in mediaitem['art'].keys() if arttype.startswith(selectedarttype) and arttype not in result.keys()))
        return result, len(selectedart[0])

def notifycount(count):
    log('{0} artwork added'.format(count), xbmc.LOGINFO)
    if count:
        xbmcgui.Dialog().notification('{0} artwork added'.format(count), "Contribute or donate to the awesomeness\nfanart.tv, thetvdb.com, themoviedb.org", '-', 6500)
    else:
        xbmcgui.Dialog().notification('No new artwork added', "Something missing? Contribute or donate to the source\nfanart.tv, thetvdb.com, themoviedb.org", '-', 6500)

def add_processeditem(processed, mediaitem):
    if mediaitem['mediatype'] == 'tvshow':
        processed['tvshow'][mediaitem['dbid']] = mediaitem['season']
    else:
        processed[mediaitem['mediatype']].append(mediaitem['dbid'])

def get_media_subtype(mediapath):
    mediapath = mediapath.lower()
    if re.search(r'\b3d\b', mediapath):
        return '3d'
    if re.search(r'blu-?ray|b[rd]rip', mediapath) or mediapath.endswith('.bdmv'):
        return 'bluray'
    if re.search(r'\bdvd', mediapath) or mediapath.endswith('.ifo'):
        return 'dvd'
    return 'unknown'

def add_external_to_itemart(itemart, arttype, art, localart):
    itemart[arttype].append(art)
    localmatch = next((local for ll in localart.values() for local in ll if local['url'] == art['url']), None)
    if localmatch:
        itemart[arttype].remove(localmatch)
        if 'title' in localmatch:
            art['title'] = localmatch['title']
        art['second provider'] = localmatch['provider'].display
