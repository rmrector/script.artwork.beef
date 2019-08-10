import re
import urllib
import xbmc
from abc import ABCMeta, abstractmethod

from lib.providers.base import AbstractImageProvider, cache, build_key_error
from lib.libs import mediatypes
from lib.libs.addonsettings import settings
from lib.libs.pykodi import json, UTF8JSONDecoder
from lib.libs.utils import SortedDisplay

class FanartTVAbstractProvider(AbstractImageProvider):
    __metaclass__ = ABCMeta
    api_section = None
    mediatype = None
    contenttype = 'application/json'

    name = SortedDisplay('fanart.tv', 'fanart.tv')
    apiurl = 'https://webservice.fanart.tv/v3/%s/%s'

    def get_images(self, uniqueids, types=None):
        if not settings.get_apienabled('fanarttv'):
            return {}
        if types is not None and not self.provides(types):
            return {}
        mediaid = get_mediaid(uniqueids, self.mediatype)
        if not mediaid or isinstance(mediaid, tuple) and not mediaid[0]:
            return {}
        data = self.get_data(mediaid[0] if isinstance(mediaid, tuple) else mediaid)
        if not data:
            return {}
        if self.mediatype == mediatypes.MUSICVIDEO:
            return self._get_images(data, mediaid)
        elif self.mediatype == mediatypes.ALBUM:
            if not data.get('albums', {}).get(mediaid):
                return {}
            return self._get_images(data['albums'][mediaid])
        else:
            return self._get_images(data)

    def get_data(self, mediaid):
        result = cache.cacheFunction(self._get_data, mediaid)
        return result if result != 'Empty' else None

    def _get_data(self, mediaid):
        apikey = settings.get_apikey('fanarttv')
        if not apikey:
            raise build_key_error('fanarttv')
        self.log('uncached', xbmc.LOGINFO)
        headers = {'api-key': apikey}
        if settings.fanarttv_clientkey:
            headers['client-key'] = settings.fanarttv_clientkey
        response = self.doget(self.apiurl % (self.api_section, mediaid), headers=headers)
        return 'Empty' if response is None else json.loads(response.text, cls=UTF8JSONDecoder)

    def login(self):
        raise build_key_error('fanarttv')

    def build_image(self, url, arttype, image, likediv=5.0):
        result = {'url': url, 'provider': self.name}
        result['preview'] = url.replace('.fanart.tv/fanart/', '.fanart.tv/preview/')
        result['rating'] = SortedDisplay(5.25 + int(image['likes']) / float(likediv), '{0} likes'.format(image['likes']))
        result['size'] = _get_imagesize(arttype)
        result['language'] = _get_imagelanguage(arttype, image)
        return result

    @abstractmethod
    def _get_images(self, data, mediaid=None):
        pass

    @abstractmethod
    def provides(self, types):
        pass

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
        'tvposter-alt': 'keyart',
        'seasonthumb': mediatypes.SEASON + '.%s.landscape',
        'seasonbanner': mediatypes.SEASON + '.%s.banner',
        'seasonposter': mediatypes.SEASON + '.%s.poster',
        'showbackground-season': mediatypes.SEASON + '.%s.fanart'
    }

    def _get_images(self, data):
        result = {}
        for arttype, artlist in data.iteritems():
            if arttype not in self.artmap:
                continue
            for image in artlist:
                generaltype = self.artmap[arttype]
                isseasonimage = arttype in ('seasonthumb', 'seasonbanner', 'seasonposter')
                seasonnum = self._get_seasonnum(image, data['name'], not isseasonimage)
                if isseasonimage:
                    generaltype = generaltype % seasonnum
                if generaltype == 'poster' and not _get_imagelanguage(arttype, image):
                    generaltype = 'keyart'
                if generaltype not in result:
                    result[generaltype] = []
                url = urllib.quote(image['url'], safe="%/:=&?~#+!$,;'@()*[]")
                resultimage = self.build_image(url, arttype, image, 3.0)
                if arttype == 'showbackground' and seasonnum is not None:
                    resultimage['hasseason'] = True
                    if seasonnum >= 0:
                        resultimage['title'] = 'Season {0}'.format(seasonnum if seasonnum else 'specials')
                    seasonfanarttype = 'season.{0}.fanart'.format(seasonnum)
                    if seasonfanarttype not in result:
                        result[seasonfanarttype] = []
                    result[seasonfanarttype].append(resultimage)
                result[generaltype].append(resultimage)
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
        'movieposter': 'poster',
        'movieposter-alt': 'keyart'
    }

    disctitles = {'dvd': 'DVD', '3d': '3D', 'bluray': 'Blu-ray'}

    def _get_images(self, data):
        result = {}
        for arttype, artlist in data.iteritems():
            if arttype not in self.artmap:
                continue
            for image in artlist:
                generaltype = self.artmap[arttype]
                if generaltype == 'poster' and not _get_imagelanguage(arttype, image):
                    generaltype = 'keyart'
                if artlist and generaltype not in result:
                    result[generaltype] = []
                url = urllib.quote(image['url'], safe="%/:=&?~#+!$,;'@()*[]")
                resultimage = self.build_image(url, arttype, image)
                if arttype == 'moviedisc':
                    display = self.disctitles.get(image['disc_type']) or image['disc_type']
                    resultimage['subtype'] = SortedDisplay(image['disc_type'], display)
                result[generaltype].append(resultimage)
        return result

    def provides(self, types):
        return any(x in types for x in self.artmap.values())

class FanartTVMovieSetProvider(FanartTVMovieProvider):
    mediatype = mediatypes.MOVIESET

class FanartTVMusicVideoProvider(FanartTVAbstractProvider):
    mediatype = mediatypes.MUSICVIDEO

    api_section = 'music'
    artmap = {
        'artistthumb': 'artistthumb',
        'artistbackground': 'fanart',
        'albumcover': 'poster',
        'cdart': 'discart',
        'musiclogo': 'clearlogo',
        'hdmusiclogo': 'clearlogo',
        'musicbanner': 'banner'
    }

    def _get_images(self, data, albumid):
        def poofit(arttype, artlist, resultmap):
            generaltype = self.artmap.get(arttype)
            if not generaltype:
                return
            if artlist and generaltype not in resultmap:
                resultmap[generaltype] = []
            for image in artlist:
                url = urllib.quote(image['url'], safe="%/:=&?~#+!$,;'@()*[]")
                resultmap[generaltype].append(self.build_image(url, arttype, image))

        result = {}
        for arttype, artlist in data.iteritems():
            if arttype != 'albums':
                poofit(arttype, artlist, result)
            else:
                if not albumid:
                    continue
                for album_arttype, album_artlist in artlist.get(albumid, {}):
                    poofit(album_arttype, album_artlist, result)
        return result

    def provides(self, types):
        return any(x in types for x in self.artmap.values())

class FanartTVAlbumProvider(FanartTVMovieProvider):
    mediatype = mediatypes.ALBUM
    api_section = 'music/albums'
    artmap = {
        'albumcover': 'thumb',
        'cdart': 'discart'
    }

class FanartTVArtistProvider(FanartTVMovieProvider):
    mediatype = mediatypes.ARTIST
    api_section = 'music'
    artmap = {
        'artistthumb': 'thumb',
        'artistbackground': 'fanart',
        'musiclogo': 'clearlogo',
        'hdmusiclogo': 'clearlogo',
        'musicbanner': 'banner'
    }

def get_mediaid(uniqueids, mediatype):
    if mediatype == mediatypes.MUSICVIDEO:
        return (uniqueids.get('mbartist'), uniqueids.get('mbgroup'))
    if mediatype == mediatypes.ALBUM:
        return uniqueids.get('mbgroup')
    if mediatype == mediatypes.ARTIST:
        return uniqueids.get('mbartist')
    sources = ('tmdb', 'imdb', 'unknown') if mediatype == mediatypes.MOVIE else \
        ('tmdb', 'unknown') if mediatype == mediatypes.MOVIESET else ('tvdb', 'unknown')
    for source in sources:
        if source in uniqueids:
            return uniqueids[source]

def _get_imagesize(arttype):
    if arttype in ('hdtvlogo', 'hdclearart', 'hdmovielogo', 'hdmovieclearart', 'hdmusiclogo'):
        return SortedDisplay(800, 'HD')
    elif arttype in ('clearlogo', 'clearart', 'movielogo', 'movieart', 'musiclogo'):
        return SortedDisplay(400, 'SD')
    elif arttype in ('tvbanner', 'seasonbanner', 'moviebanner', 'musicbanner'):
        return SortedDisplay(1000, '1000x185')
    elif arttype in ('showbackground', 'moviebackground', 'artistbackground'):
        return SortedDisplay(1920, '1920x1080')
    elif arttype in ('tvposter', 'seasonposter', 'movieposter'):
        return SortedDisplay(1426, '1000x1426')
    elif arttype in ('tvthumb', 'seasonthumb'):
        return SortedDisplay(500, '500x281 or 1000x562')
    elif arttype == 'characterart':
        return SortedDisplay(512, '512x512')
    elif arttype == 'moviethumb':
        return SortedDisplay(1000, '1000x562')
    elif arttype in ('moviedisc', 'cdart', 'artistthumb', 'albumcover'):
        return SortedDisplay(1000, '1000x1000')
    return SortedDisplay(0, '')

def _get_imagelanguage(arttype, image):
    if 'lang' not in image or arttype in ('showbackground', 'characterart', 'moviebackground', 'artistbackground'):
        return None
    if arttype in ('clearlogo', 'hdtvlogo', 'seasonposter', 'hdclearart', 'clearart', 'tvthumb', 'seasonthumb',
            'tvbanner', 'seasonbanner', 'movielogo', 'hdmovielogo', 'hdmovieclearart', 'movieart', 'moviebanner',
            'moviethumb', 'moviedisc'):
        return image['lang'] if image['lang'] not in ('', '00') else 'en'
    # tvposter and movieposter may or may not have a title and thus need a language
    return image['lang'] if image['lang'] not in ('', '00') else None
