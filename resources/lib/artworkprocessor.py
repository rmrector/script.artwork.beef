import xbmc

from devhelper import pykodi
from devhelper import quickjson

from devhelper.pykodi import log

import mediatypes
import providers

MODE_AUTO = 'auto'
MODE_GUI = 'gui'

class ArtworkProcessor(object):
    def __init__(self):
        self.monitor = xbmc.Monitor()
        self.dryrun = True

    def process_allartwork(self, mediatype):
        pass

    def process_itemartwork(self, mediatype, dbid, mode):
        mediaitem = None
        if mediatype == mediatypes.TVSHOW:
            mediaitem = quickjson.get_tvshow_details(dbid, ['art', 'imdbnumber'])
        elif mediatype == mediatypes.MOVIE:
            mediaitem = quickjson.get_movie_details(dbid, ['art', 'imdbnumber'])
        elif mediatype == mediatypes.EPISODE:
            mediaitem = quickjson.get_episode_details(dbid, ['art', 'uniqueid'])
        if not mediaitem:
            return
        mediaitem = self.process_mediaitem(mediaitem, mode)
        if not mediaitem:
            return
        if mode == MODE_GUI:
            pass # prompt with 'available art'

        self.add_art_to_library(mediaitem)

    def process_medialist(self, medialist):
        resultlist = []
        for mediaitem in medialist:
            mediaitem = self.process_mediaitem(mediaitem, MODE_AUTO)
            if not mediaitem:
                continue
            resultlist.append(mediaitem)
            self.add_art_to_library(mediaitem)
            if self.monitor.waitForAbort(0.5):
                break
        return resultlist

    def process_mediaitem(self, mediaitem, mode):
        if 'tvshowid' in mediaitem:
            mediaitem['mediatype'] = mediatypes.TVSHOW
        elif 'movieid' in mediaitem:
            mediaitem['mediatype'] = mediatypes.MOVIE
        elif 'episodeid' in mediaitem:
            mediaitem['mediatype'] = mediatypes.EPISODE
        else:
            log('Not sure what mediatype this is.')
            log(mediaitem)
            return
        self.add_additional_iteminfo(mediaitem)
        if mode == MODE_AUTO:
            missing = self.list_missing_arttypes(mediaitem)
            if missing:
                mediaitem['available art'] = self.get_available_artwork(mediaitem)
                mediaitem['selected art'] = self.get_top_missing_art(mediaitem, missing)
        else:
            mediaitem['available art'] = self.get_available_artwork(mediaitem)
        return mediaitem

    def add_additional_iteminfo(self, mediaitem):
        if mediaitem['mediatype'] == mediatypes.TVSHOW:
            mediaitem['seasons'], art = self._get_seasons_artwork(quickjson.get_seasons(mediaitem['tvshowid']))
            mediaitem['art'].update(art)
        elif mediaitem['mediatype'] == mediatypes.EPISODE:
            mediaitem['imdbnumber'] = self._get_episodeid(mediaitem)

        return mediaitem

    def get_available_artwork(self, mediaitem):
        if mediaitem['mediatype'] not in (mediatypes.TVSHOW, mediatypes.MOVIE, mediatypes.EPISODE):
            return
        images = {}
        for provider in providers.get_providers()[mediaitem['mediatype']]:
            images.update(provider.get_images(mediaitem['imdbnumber']))
        return images

    def get_top_missing_art(self, mediaitem, missing_art):
        newartwork = {}
        language = xbmc.getLanguage(xbmc.ISO_639_1)
        if language != 'en':
            language = (language, 'en')
        else:
            language = (language,)
        for missingart in missing_art:
            if missingart.startswith(mediatypes.SEASON):
                mediatype = mediatypes.SEASON
                artkey = missingart.rsplit('.', 1)[1]
            else:
                mediatype = mediaitem['mediatype']
                artkey = missingart
            if missingart not in mediaitem['available art']:
                continue
            if mediatypes.artinfo[mediatype][artkey]['multiselect']:
                existingart = []
                existingartnames = []
                for art, url in mediaitem['art'].iteritems():
                    if art.startswith(missingart):
                        existingart.append(pykodi.unquoteimage(url))
                        existingartnames.append(art)

                missingartnames = []
                for i in range(0, mediatypes.artinfo[mediatype][artkey]['autolimit']):
                    multikey = '%s%s' % (artkey, i if i else '')
                    if multikey not in existingartnames:
                        missingartnames.append(multikey)

                newart = [art for art in mediaitem['available art'][missingart] if art['language'] in language and art['url'] not in existingart]
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
                if mediaitem['available art'][missingart][0]['language'] in language:
                    newartwork[missingart] = mediaitem['available art'][missingart][0]['url']
        return newartwork

    def list_missing_arttypes(self, mediaitem):
        fullartinfo = mediatypes.artinfo[mediaitem['mediatype']]
        for arttype, artinfo in fullartinfo.iteritems():
            if not artinfo['autolimit']:
                continue
            elif artinfo['autolimit'] == 1:
                if arttype not in mediaitem['art'].keys():
                    yield arttype
            else:
                artcount = sum(1 for art in mediaitem['art'].keys() if art.startswith(arttype))
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
                        if arttype not in mediaitem['art'].keys():
                            yield arttype
                    else:
                        artcount = sum(1 for art in mediaitem['art'].keys() if art.startswith(arttype))
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
                log("Didn't find a uniqueid for episode '%s', can't look it up. I expect the ID from TheTVDB, which generally comes from the scraper." % episode['label'], xbmc.LOGINFO)
            return result

    def add_art_to_library(self, mediaitem):
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

            if self.dryrun:
                log((seriesart, allseasonart))
                return
            if seriesart:
                quickjson.set_tvshow_details(mediaitem['tvshowid'], art=seriesart)
            for seasonid, seasonart in allseasonart.iteritems():
                quickjson.set_season_details(seasonid, art=seasonart)

        elif mediaitem['mediatype'] == mediatypes.MOVIE:
            movieart = {arttype: url for arttype, url in mediaitem['selected art'].iteritems()}
            if self.dryrun:
                log(movieart)
                return
            if movieart:
                quickjson.set_movie_details(mediaitem['movieid'], art=movieart)
