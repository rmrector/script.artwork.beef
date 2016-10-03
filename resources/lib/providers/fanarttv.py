import re
import urllib
import xbmc
from abc import ABCMeta

from devhelper import pykodi

import mediatypes
from base import AbstractProvider, cache
from utils import SortedDisplay

addon = pykodi.get_main_addon()

class FanartTVAbstractProvider(AbstractProvider):
    # pylint: disable=W0223
    __metaclass__ = ABCMeta
    api_section = None

    name = SortedDisplay('fanart.tv', 'fanart.tv')
    apikey = '13756cf3472ff6b3dbffee20bed9c6ec'
    apiurl = 'http://webservice.fanart.tv/v3/%s/%s'

    def __init__(self):
        super(FanartTVAbstractProvider, self).__init__()
        self.set_contenttype('application/json')
        self.clientkey = addon.get_setting('fanarttv_key')

    def get_data(self, mediaid):
        return cache.cacheFunction(self._get_data, mediaid)

    def _get_data(self, mediaid):
        self.log('uncached', xbmc.LOGINFO)
        headers = {'api-key': self.apikey}
        if self.clientkey:
            headers['client-key'] = self.clientkey
        response = self.doget(self.apiurl % (self.api_section, mediaid), headers=headers)
        return 'Empty' if response is None else response.json()

class FanartTVSeriesProvider(FanartTVAbstractProvider):
    mediatype = mediatypes.TVSHOW

    api_section = 'tv'
    artmap = {
        'hdclearart': 'clearart',
        'tvbanner': 'banner',
        'clearlogo': 'clearlogo',
        'characterart': 'characterart',
        'showbackground': 'fanart',
        'tvthumb': 'landscape',
        'clearart': 'clearart',
        'hdtvlogo': 'clearlogo',
        'tvposter': 'poster',
        'seasonthumb': mediatypes.SEASON + '.%s.landscape',
        'seasonbanner': mediatypes.SEASON + '.%s.banner',
        'seasonposter': mediatypes.SEASON + '.%s.poster'
    }

    def get_images(self, mediaid, types=None):
        if types and not self.provides(types):
            return {}
        data = self.get_data(mediaid)
        if data == 'Empty':
            return {}
        result = {}
        for arttype, artlist in data.iteritems():
            generaltype = self.artmap.get(arttype)
            if not generaltype:
                continue
            for image in artlist:
                itype = generaltype
                if arttype in ('seasonthumb', 'seasonbanner', 'seasonposter'):
                    try:
                        itype = itype % (int(image['season']) if image['season'] != 'all' else -1)
                    except ValueError:
                        self.log("Data for '%s' from provider has a small problem: image season was set incorrectly, to \"%s\", so I can't tell which season it belongs to. The image URL is:\n%s" % (data['name'], image['season'], image['url']), xbmc.LOGINFO)
                        # throw it into the 'all seasons' image pile
                        itype = itype % -1
                if itype not in result:
                    result[itype] = []
                url = urllib.quote(image['url'], safe="%/:=&?~#+!$,;'@()*[]")
                resultimage = {'url': url, 'provider': self.name}
                resultimage['preview'] = url.replace('.fanart.tv/fanart/', '.fanart.tv/preview/')
                resultimage['rating'] = SortedDisplay(5 + int(image['likes']) / 3.0, '{0} likes'.format(image['likes']))
                resultimage['size'] = self._get_imagesize(arttype)
                resultimage['language'] = self._get_imagelanguage(arttype, image)
                if arttype == 'showbackground' and 'season' in image and image['season'] != 'all':
                    resultimage['title'] = 'Season {0}'.format(image['season'])
                result[itype].append(resultimage)
        return result

    def _get_imagesize(self, arttype):
        if arttype in ('hdtvlogo', 'hdclearart'):
            return SortedDisplay(400, 'HD')
        elif arttype in ('clearlogo', 'clearart'):
            return SortedDisplay(10, 'SD')
        elif arttype in ('tvbanner', 'seasonbanner'):
            return SortedDisplay(1000, '1000x185')
        elif arttype == 'showbackground':
            return SortedDisplay(1920, '1920x1080')
        elif arttype in ('tvposter', 'seasonposter'):
            return SortedDisplay(1426, '1000x1426')
        elif arttype == 'characterart':
            return SortedDisplay(512, '512x512')
        elif arttype in ('tvthumb', 'seasonthumb'):
            return SortedDisplay(500, '500x281')
        else:
            return SortedDisplay(0, '')

    def _get_imagelanguage(self, arttype, image):
        if arttype in ('showbackground', 'characterart'):
            return None
        if arttype in ('clearlogo', 'hdtvlogo', 'seasonposter', 'hdclearart', 'clearart', 'tvthumb', 'seasonthumb', 'tvbanner', 'seasonbanner'):
            return image['lang'] if image['lang'] not in ('', '00') else 'en'
        # tvposter may or may not have a title and thus need a language
        return image['lang'] if image['lang'] not in ('', '00') else None

    def provides(self, types):
        types = set(x if not x.startswith('season') else re.sub(r'[\d]', '%s', x) for x in types)
        return any(x in types for x in self.artmap.values())

class FanartTVMovieProvider(FanartTVAbstractProvider):
    mediatype = mediatypes.MOVIE

    api_section = 'movies'
    artmap = {
        'movielogo': 'clearlogo',
        'hdmovielogo': 'clearlogo',
        'hdmovieclearart': 'clearart',
        'movieart': 'clearart',
        'moviedisc': 'discart',
        'moviebanner': 'banner',
        'moviethumb': 'landscape',
        'moviebackground': 'fanart',
        'movieposter': 'poster'
    }

    disctitles = {'dvd': 'DVD', '3d': '3D', 'bluray': 'Blu-ray'}

    def get_images(self, mediaid, types=None):
        if types and not self.provides(types):
            return {}
        data = self.get_data(mediaid)
        if data == 'Empty':
            return {}
        result = {}
        for arttype, artlist in data.iteritems():
            generaltype = self.artmap.get(arttype)
            if not generaltype:
                continue
            if artlist and generaltype not in result:
                result[generaltype] = []
            for image in artlist:
                url = urllib.quote(image['url'], safe="%/:=&?~#+!$,;'@()*[]")
                resultimage = {'url': url, 'provider': self.name}
                resultimage['preview'] = url.replace('.fanart.tv/fanart/', '.fanart.tv/preview/')
                resultimage['rating'] = SortedDisplay(5 + int(image['likes']) / 5.0, '%s likes' % image['likes'])
                if arttype == 'moviedisc':
                    display = self.disctitles.get(image['disc_type']) or image['disc_type']
                    resultimage['subtype'] = SortedDisplay(image['disc_type'], display)
                resultimage['size'] = self._get_imagesize(arttype)
                resultimage['language'] = self._get_imagelanguage(arttype, image)
                result[generaltype].append(resultimage)
        return result

    def _get_imagesize(self, arttype):
        if arttype in ('hdmovielogo', 'hdmovieclearart'):
            return SortedDisplay(400, 'HD')
        elif arttype in ('movielogo', 'movieart'):
            return SortedDisplay(10, 'SD')
        elif arttype == 'moviebackground':
            return SortedDisplay(1920, '1920x1080')
        elif arttype == 'movieposter':
            return SortedDisplay(1426, '1000x1426')
        elif arttype == 'moviedisc':
            return SortedDisplay(1000, '1000x1000')
        elif arttype == 'moviebanner':
            return SortedDisplay(1000, '1000x185')
        elif arttype == 'moviethumb':
            return SortedDisplay(1000, '1000x562')
        else:
            return SortedDisplay(0, '')

    def _get_imagelanguage(self, arttype, image):
        if arttype == 'moviebackground':
            return None
        if arttype in ('movielogo', 'hdmovielogo', 'hdmovieclearart', 'movieart', 'moviebanner', 'moviethumb', 'moviedisc'):
            return image['lang'] if image['lang'] not in ('', '00') else 'en'
        # movieposter may or may not have a title
        return image['lang'] if image['lang'] not in ('', '00') else None

    def provides(self, types):
        return any(x in types for x in self.artmap.values())
