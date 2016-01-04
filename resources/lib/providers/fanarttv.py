import requests
import xbmc

from abc import ABCMeta

from devhelper.pykodi import log

import mediatypes
from base import AbstractProvider

class FanartTvAbstractProvider(AbstractProvider):
    #pylint: disable=W0223
    __metaclass__ = ABCMeta
    apikey = '13756cf3472ff6b3dbffee20bed9c6ec'
    apiurl = 'http://webservice.fanart.tv/v3/%s/%s'

class FanartTvSeriesProvider(FanartTvAbstractProvider):
    name = 'Fanart.tv series provider'
    mediatype = mediatypes.TVSHOW

    api_section = 'tv'
    artmap = {'hdclearart': 'clearart', 'tvbanner': 'banner', 'clearlogo': 'clearlogo', 'characterart': 'characterart',
        'showbackground': 'fanart', 'tvthumb': 'landscape', 'clearart': 'clearart', 'hdtvlogo': 'clearlogo',
        'seasonthumb': mediatypes.SEASON + '.%s.landscape', 'seasonbanner': mediatypes.SEASON + '.%s.banner'}
    # Leave out seasonposter and tvposter. Fanart.tv has a goofy ass poster ratio
    # Maybe I'll still want to keep them, but disabled by default and/or not for auto
    # showbackground is also iffy. There are often duplicates with TheTVDB. Maybe this guy's fanart isn't considered for auto, but can be selected in the gui.

    def log(self, message, level=xbmc.LOGDEBUG):
        log(message, level, tag='fanarttv.series')

    def get_images(self, media_id):
        response = self.session.get(self.apiurl % (self.api_section, media_id), headers={'api-key': self.apikey}, timeout=5)
        if response.status_code == requests.codes.not_found:
            return {}
        self.log(response.status_code)
        response.raise_for_status()
        data = response.json()
        self.log("Getting art for '%s'" % data['name'])
        result = {}
        for arttype, artlist in data.iteritems():
            generaltype = self.artmap.get(arttype)
            if not generaltype:
                continue
            for image in artlist:
                itype = generaltype
                # IDEA: Warn on empty language, for types that need text?
                if arttype in ('seasonthumb', 'seasonbanner'):
                    try:
                        itype = itype % int(image['season']) if image['season'] != 'all' else -1
                    except ValueError:
                        self.log('Data for \'%s\' from provider has a small problem: image season was set incorrectly, to "%s", so I can\'t tell which season it belongs to. The image URL is:\n%s' % (data['name'], image['season'], image['url']))
                        # throw it into the 'all' pile
                        itype = itype % (-1,)
                if itype not in result:
                    result[itype] = []
                rating = (5 + int(image['likes']) / 3.0, '%s likes' % image['likes'])
                if arttype in ('hdtvlogo', 'hdclearart'):
                    size = (50, 'HD')
                elif arttype in ('clearlogo', 'clearart'):
                    size = (10, 'SD')
                elif arttype in ('tvbanner', 'seasonbanner'):
                    size = (1000, '1000x185')
                elif arttype == 'showbackground':
                    size = (1920, '1920x1080')
                else:
                    size = (0, '')
                result[itype].append({'url': image['url'], 'language': image['lang'], 'rating': rating, 'size': size, 'provider': self.name})
        return result

class FanartTvMovieProvider(FanartTvAbstractProvider):
    name = 'Fanart.tv movie provider'
    mediatype = mediatypes.MOVIE

    api_section = 'movies'
    artmap = {'movielogo': 'clearlogo', 'hdmovielogo': 'clearlogo', 'hdmovieclearart': 'clearart', 'movieart': 'clearart',
        'moviedisc': 'discart', 'moviebanner': 'banner', 'moviethumb': 'landscape', 'moviebackground': 'fanart'}
    # Leave out movieposter. Fanart.tv has a goofy ass poster ratio
    # Maybe I'll still want to keep them, but disabled by default and/or not for auto
    # moviebackground has a lot of dupes, like shows

    def log(self, message, level=xbmc.LOGDEBUG):
        log(message, level, tag='fanarttv.movie')

    def get_images(self, media_id):
        response = self.session.get(self.apiurl % (self.api_section, media_id), headers={'api-key': self.apikey}, timeout=5)
        if response.status_code == requests.codes.not_found:
            return {}
        self.log(response.status_code)
        response.raise_for_status()
        log(response.headers)
        data = response.json()
        self.log("Getting art for '%s'" % data['name'])
        result = {}
        for arttype, artlist in data.iteritems():
            generaltype = self.artmap.get(arttype)
            if not generaltype:
                continue
            if artlist and generaltype not in result:
                result[generaltype] = []
            for image in artlist:
                resultimage = {'url': image['url'], 'language': image['lang'], 'provider': self.name}
                resultimage['rating'] = (5 + int(image['likes']) / 6.0, '%s likes' % image['likes'])
                if arttype in ('hdmovielogo', 'hdmovieclearart'):
                    resultimage['size'] = (50, 'HD')
                elif arttype in ('movielogo', 'movieart'):
                    resultimage['size'] = (10, 'SD')
                elif arttype == 'moviebackground':
                    resultimage['size'] = (1920, '1920x1080')
                else:
                    resultimage['size'] = (0, '')
                if arttype == 'moviedisc':
                    resultimage['subtype'] = image['disc_type']
                result[generaltype].append(resultimage)
        return result
