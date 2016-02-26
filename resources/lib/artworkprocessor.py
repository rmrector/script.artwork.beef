import xbmc
import xbmcgui

from devhelper import pykodi
from devhelper import quickjson
from devhelper.pykodi import log

import mediatypes
import providers
from sorteddisplaytuple import SortedDisplay
from artworkselection import ArtworkTypeSelector, ArtworkSelector

addon = pykodi.get_main_addon()

MODE_AUTO = 'auto'
MODE_GUI = 'gui'

HAPPY_IMAGE = SortedDisplay(0, 'happy')
NOAUTO_IMAGE = SortedDisplay(0, 'noauto')

THROTTLE_TIME = 0.15
PREFERRED_FANART_SIZE = 1920
PREFERRED_SIZE = 1000

tvshow_properties = ['art', 'imdbnumber', 'season']
movie_properties = ['art', 'imdbnumber']
episode_properties = ['art', 'uniqueid']

class ArtworkProcessor(object):
    def __init__(self, monitor=None):
        self.monitor = monitor or xbmc.Monitor()
        self.language = None
        self.autolanguages = None
        self.progress = xbmcgui.DialogProgressBG()

    @property
    def processing(self):
        return pykodi.get_conditional('StringCompare(Window(Home).Property(ArtworkBeef.Status),Processing)')

    def process_item(self, mediatype, dbid, mode):
        if self.processing:
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
            artwork_requested = self.add_available_artwork(mediaitem, mode)
            xbmc.executebuiltin('Dialog.Close(busydialog)')
            if not artwork_requested or not mediaitem.get('available art'):
                xbmcgui.Dialog().notification('No artwork available', "Something missing? Contribute or donate to the source\nfanart.tv, thetvdb.com, themoviedb.org", '-', 6500)
                return
            selected, count = self.prompt_for_artwork(mediaitem)
            if not selected:
                return
            mediaitem['selected art'] = selected
            self.add_art_to_library(mediaitem)
            self.notifycount(count)
        else:
            medialist = [mediaitem]
            autoaddepisodes = addon.get_setting('autoaddepisodes_list') if addon.get_setting('episode.fanart') else ()
            if mediatype == mediatypes.TVSHOW and mediaitem['imdbnumber'] in autoaddepisodes:
                medialist.extend(quickjson.get_episodes(dbid, properties=episode_properties))
            self.progress.create("Adding extended artwork", "Listing all items")
            self.process_medialist(medialist)
            self.progress.close()

    def process_medialist(self, medialist):
        processed = {'tvshow': {}, 'movie': [], 'episode': []}
        self.setlanguages()
        artcount = 0
        currentitem = 0
        for mediaitem in medialist:
            self.progress.update(currentitem * 100 // len(medialist), message=mediaitem['label'])
            currentitem += 1
            self.add_additional_iteminfo(mediaitem)
            artwork_requested = self.add_available_artwork(mediaitem, MODE_AUTO)
            if not artwork_requested:
                add_processeditem(processed, mediaitem)
                if self.monitor.abortRequested():
                    break
                continue
            if not mediaitem.get('available art'):
                add_processeditem(processed, mediaitem)
                if self.monitor.waitForAbort(THROTTLE_TIME):
                    break
                continue
            mediaitem['selected art'] = self.get_top_missing_art(mediaitem)
            self.add_art_to_library(mediaitem)
            artcount += len(mediaitem['selected art'])
            add_processeditem(processed, mediaitem)
            if self.monitor.waitForAbort(THROTTLE_TIME):
                break
        self.notifycount(artcount)
        return processed

    def add_available_artwork(self, mediaitem, mode):
        if mode == MODE_AUTO:
            if next(self.list_missing_arttypes(mediaitem), False):
                mediaitem['available art'] = self.get_available_artwork(mediaitem)
                return True
        else:
            mediaitem['available art'] = self.get_available_artwork(mediaitem)
            return True
        return False

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

    def get_available_artwork(self, mediaitem):
        if mediaitem['mediatype'] not in (mediatypes.TVSHOW, mediatypes.MOVIE, mediatypes.EPISODE):
            return
        images = {}
        for provider in providers.get_providers()[mediaitem['mediatype']]:
            for arttype, artlist in provider.get_images(mediaitem['imdbnumber']).iteritems():
                if arttype.startswith('season'):
                    season = arttype.rsplit('.', 2)[1]
                    if int(season) not in mediaitem['seasons']:
                        # Don't add artwork for seasons we don't have
                        continue
                if arttype not in images:
                    images[arttype] = []
                images[arttype].extend(artlist)
            if self.monitor.abortRequested():
                return
        for arttype, imagelist in images.iteritems():
            [self.apply_status(arttype, image) for image in imagelist] #pylint: disable=W0106
            self.sort_images(arttype, imagelist)
        return images

    def apply_status(self, arttype, image):
        image['status'] = HAPPY_IMAGE
        if arttype == 'fanart':
            if image.get('provider') == 'fanart.tv':
                image['status'] = NOAUTO_IMAGE
    def sort_images(self, arttype, imagelist):
        # 1. Match the primary language, for everything but fanart
        # 2. Separate on status, like goofy images
        # 3. Size (in 200px groups), up to PREFERRED_SIZE
        # 4. Rating
        imagelist.sort(key=lambda image: image['rating'].sort, reverse=True)
        preferredsize = PREFERRED_FANART_SIZE if arttype == 'fanart' else PREFERRED_SIZE
        imagelist.sort(key=lambda image: (image['size'].sort if image['size'].sort <= preferredsize else preferredsize) // 200, reverse=True)
        imagelist.sort(key=lambda image: image['status'].sort)
        if not arttype.endswith('fanart'):
            imagelist.sort(key=lambda image: (0 if image['language'] == self.language else 1, image['language']))

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

    def list_missing_arttypes(self, mediaitem, includenew=False):
        arttypes = mediaitem['art'].keys()
        if includenew:
            arttypes.extend(mediaitem['selected art'])
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
                if not arttype.startswith(('tvshow', 'season')):
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
        if arttype.endswith('fanart') and art['size'].sort < 1276:
            return False
        return (art['language'] in self.autolanguages or arttype.endswith('fanart')) and art['status'] != NOAUTO_IMAGE and art['url'] not in ignoreurls

    def prompt_for_artwork(self, mediaitem):
        items = mediaitem['available art'].keys()
        if not items:
            return {}, 0
        typeselectwindow = ArtworkTypeSelector('DialogSelect.xml', addon.path, existingart=mediaitem['art'], arttypes=items, medialabel=mediaitem['label'])
        selectedart = None
        hqpreview = addon.get_setting('highquality_preview')
        singlewindow = len(items) == 1
        # The loop shows the first window if viewer backs out of the second
        while not selectedart:
            if singlewindow:
                selectedarttype = items[0]
            else:
                selectedarttype = typeselectwindow.prompt()
            if not selectedarttype:
                return {}, 0
            artlist = mediaitem['available art'][selectedarttype]
            if selectedarttype.startswith('season'):
                stype = selectedarttype.rsplit('.', 1)[1]
                multi = mediatypes.artinfo[mediatypes.SEASON][stype]['multiselect']
            else:
                multi = mediatypes.artinfo[mediaitem['mediatype']][selectedarttype]['multiselect']
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

    def notifycount(self, count):
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
