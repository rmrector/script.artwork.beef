import re
import urllib
import xbmc
from abc import ABCMeta

from lib.providers.base import AbstractProvider, cache
from lib.libs import mediatypes
from lib.libs.pykodi import get_main_addon, json, UTF8JSONDecoder
from lib.libs.utils import SortedDisplay

addon = get_main_addon()

class FanartTVAbstractProvider(AbstractProvider):
    __metaclass__ = ABCMeta
    api_section = None

    name = SortedDisplay('fanart.tv', 'fanart.tv')
    apikey = '***REMOVED***'
    apiurl = 'http://webservice.fanart.tv/v3/%s/%s'

    def __init__(self, *args):
        super(FanartTVAbstractProvider, self).__init__(*args)
        self.set_accepted_contenttype('application/json')
        self.getter.retryon_servererror = True
        self.clientkey = addon.get_setting('fanarttv_key')

    def get_data(self, mediaid):
        result = cache.cacheFunction(self._get_data, mediaid)
        return result if result != 'Empty' else None

    def _get_data(self, mediaid):
        self.log('uncached', xbmc.LOGINFO)
        headers = {'api-key': self.apikey}
        if self.clientkey:
            headers['client-key'] = self.clientkey
        response = self.doget(self.apiurl % (self.api_section, mediaid), headers=headers)
        return 'Empty' if response is None else json.loads(response.text, cls=UTF8JSONDecoder)

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
        'seasonposter': mediatypes.SEASON + '.%s.poster',
        'showbackground-season': mediatypes.SEASON + '.%s.fanart'
    }

    def get_images(self, mediaid, types=None):
        if types and not self.provides(types):
            return {}
        data = self.get_data(mediaid)
        if not data:
            return {}
        result = {}
        for arttype, artlist in data.iteritems():
            generaltype = self.artmap.get(arttype)
            if not generaltype:
                continue
            for image in artlist:
                itype = generaltype
                isseasonimage = arttype in ('seasonthumb', 'seasonbanner', 'seasonposter')
                seasonnum = self._get_seasonnum(image, data['name'], not isseasonimage)
                if isseasonimage:
                    itype = itype % seasonnum
                if itype not in result:
                    result[itype] = []
                url = urllib.quote(image['url'], safe="%/:=&?~#+!$,;'@()*[]")
                resultimage = {'url': url, 'provider': self.name}
                resultimage['preview'] = url.replace('.fanart.tv/fanart/', '.fanart.tv/preview/')
                resultimage['rating'] = SortedDisplay(6 + int(image['likes']) / 3.0, '{0} likes'.format(image['likes']))
                resultimage['size'] = _get_imagesize(arttype)
                resultimage['language'] = _get_imagelanguage(arttype, image)
                if arttype == 'showbackground' and seasonnum is not None:
                    resultimage['hasseason'] = True
                    if seasonnum >= 0:
                        resultimage['title'] = 'Season {0}'.format(seasonnum if seasonnum else 'specials')
                    seasonfanarttype = 'season.{0}.fanart'.format(seasonnum)
                    if seasonfanarttype not in result:
                        result[seasonfanarttype] = []
                    result[seasonfanarttype].append(resultimage)
                result[itype].append(resultimage)
        return result

    def _get_seasonnum(self, image, itemname, ignoreall=False):
        allitem = None if ignoreall else -1
        if 'season' not in image:
            return None
        try:
            return int(image['season']) if image['season'] != 'all' else allitem
        except ValueError:
            if not ignoreall:
                self.log("Image season was set incorrectly for '%s', to \"%s\", so I can't tell which season "
                    "it belongs to. The image URL is:\n%s" % (itemname, image['season'], image['url']), xbmc.LOGINFO)
            # throw it into the 'all seasons' image pile
            return allitem

    def provides(self, types):
        types = set(x if not x.startswith('season.') else re.sub(r'[\d]', '%s', x) for x in types)
        return any(x in types for x in self.artmap.itervalues())

class FanartTVAbstractMovieProvider(FanartTVAbstractProvider):
    __metaclass__ = ABCMeta

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
        if not data:
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
                resultimage['rating'] = SortedDisplay(6 + int(image['likes']) / 5.0, '%s likes' % image['likes'])
                if arttype == 'moviedisc':
                    display = self.disctitles.get(image['disc_type']) or image['disc_type']
                    resultimage['subtype'] = SortedDisplay(image['disc_type'], display)
                resultimage['size'] = _get_imagesize(arttype)
                resultimage['language'] = _get_imagelanguage(arttype, image)
                result[generaltype].append(resultimage)
        return result

    def provides(self, types):
        return any(x in types for x in self.artmap.values())

# Arg
class FanartTVMovieProvider(FanartTVAbstractMovieProvider):
    mediatype = mediatypes.MOVIE

class FanartTVMovieSetProvider(FanartTVAbstractMovieProvider):
    mediatype = mediatypes.MOVIESET

def _get_imagesize(arttype):
    if arttype in ('hdtvlogo', 'hdclearart', 'hdmovielogo', 'hdmovieclearart'):
        return SortedDisplay(400, 'HD')
    elif arttype in ('clearlogo', 'clearart', 'movielogo', 'movieart'):
        return SortedDisplay(10, 'SD')
    elif arttype in ('tvbanner', 'seasonbanner', 'moviebanner'):
        return SortedDisplay(1000, '1000x185')
    elif arttype in ('showbackground', 'moviebackground'):
        return SortedDisplay(1920, '1920x1080')
    elif arttype in ('tvposter', 'seasonposter', 'movieposter'):
        return SortedDisplay(1426, '1000x1426')
    elif arttype in ('tvthumb', 'seasonthumb'):
        return SortedDisplay(500, '500x281 or 1000x562')
    elif arttype == 'characterart':
        return SortedDisplay(512, '512x512')
    elif arttype == 'moviethumb':
        return SortedDisplay(1000, '1000x562')
    elif arttype == 'moviedisc':
        return SortedDisplay(1000, '1000x1000')
    else:
        return SortedDisplay(0, '')

def _get_imagelanguage(arttype, image):
    if arttype in ('showbackground', 'characterart', 'moviebackground'):
        return None
    if arttype in ('clearlogo', 'hdtvlogo', 'seasonposter', 'hdclearart', 'clearart', 'tvthumb', 'seasonthumb',
            'tvbanner', 'seasonbanner', 'movielogo', 'hdmovielogo', 'hdmovieclearart', 'movieart', 'moviebanner',
            'moviethumb', 'moviedisc'):
        return image['lang'] if image['lang'] not in ('', '00') else 'en'
    # tvposter and movieposter may or may not have a title and thus need a language
    return image['lang'] if image['lang'] not in ('', '00') else None
