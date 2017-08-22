import re
import sys
import xbmc
from math import pi, sin

from lib.providers import base
from lib.providers.base import AbstractProvider, cache
from lib.libs import mediatypes
from lib.libs.pykodi import json, UTF8JSONDecoder
from lib.providers import ProviderError
from lib.libs.utils import SortedDisplay

# designed for version 2.1.0 of TheTVDB API
class TheTVDBProvider(AbstractProvider):
    name = SortedDisplay('thetvdb.com', 'TheTVDB.com')
    mediatype = mediatypes.TVSHOW

    apikey = '8357F01B3F8F1393'
    apiurl = 'https://api.thetvdb.com/series/%s/images/query'
    loginurl = 'https://api.thetvdb.com/login'
    imageurl_base = 'https://thetvdb.com/banners/'

    artmap = {'fanart': 'fanart', 'poster': 'poster', 'season': mediatypes.SEASON + '.%s.poster',
        'seasonwide': mediatypes.SEASON + '.%s.banner', 'series': 'banner'}

    def __init__(self, *args):
        super(TheTVDBProvider, self).__init__(*args)
        self.set_accepted_contenttype('application/json')

    def get_data(self, mediaid, arttype, language):
        result = cache.cacheFunction(self._get_data, mediaid, arttype, language)
        return result if result != 'Empty' else None

    def _get_data(self, mediaid, arttype, language):
        self.log('uncached', xbmc.LOGINFO)
        getparams = {'params': {'keyType': arttype}, 'headers': {'Accept-Language': language}}
        response = self.doget(self.apiurl % mediaid, **getparams)
        return 'Empty' if response is None else json.loads(response.text, cls=UTF8JSONDecoder)

    def _get_rating(self, image):
        if image['ratingsInfo']['count']:
            info = image['ratingsInfo']
            rating = info['average']
            if info['count'] < 5:
                # Reweigh ratings, decrease difference from 5
                rating = 5 + (rating - 5) * sin(info['count'] / pi)
            return SortedDisplay(rating, '{0:.1f} stars'.format(info['average']))
        else:
            return SortedDisplay(5, 'Not rated')

    def get_images(self, mediaid, types=None):
        if types is not None and not self.provides(types):
            return {}
        result = {}
        languages = base.languages
        # Useful fanart can be hidden by the language filter, try a few of the most frequently used
        flanguages = ['en', 'de', 'fr', 'es', 'ru']
        flanguages.extend(lang for lang in languages if lang not in flanguages)
        for arttype in self.artmap:
            if types and not typematches(self.artmap[arttype], types):
                continue
            for language in languages if arttype != 'fanart' else flanguages:
                generaltype = self.artmap[arttype]
                data = self.get_data(mediaid, arttype, language)
                if not data:
                    continue
                isseason = arttype.startswith('season')
                if not isseason:
                    if generaltype not in result:
                        result[generaltype] = []
                for image in data['data']:
                    ntype = generaltype
                    if isseason:
                        ntype = ntype % image['subKey']
                        if ntype not in result:
                            result[ntype] = []
                    resultimage = {'provider': self.name}
                    resultimage['url'] = self.imageurl_base + image['fileName']
                    resultimage['preview'] = self.imageurl_base + image['thumbnail']
                    resultimage['language'] = language if shouldset_imagelanguage(image) else None
                    resultimage['rating'] = self._get_rating(image)
                    if arttype in ('series', 'seasonwide'):
                        resultimage['size'] = SortedDisplay(758, '758x140')
                    elif arttype == 'season':
                        resultimage['size'] = SortedDisplay(1000, '680x1000')
                    else:
                        try:
                            sortsize = int(image['resolution'].split('x')[0 if arttype != 'poster' else 1])
                        except ValueError:
                            self.log('whoops, ValueError on "%s"' % image['resolution'])
                            sortsize = 0
                        resultimage['size'] = SortedDisplay(sortsize, image['resolution'])
                    result[ntype].append(resultimage)
        return result

    def login(self):
        response = self.session.post(self.loginurl, json={'apikey': self.apikey},
            headers={'Content-Type': 'application/json', 'User-Agent': base.useragent}, timeout=15)
        if not response or not response.headers['Content-Type'].startswith('application/json'):
            raise ProviderError, "Provider returned unexected content", sys.exc_info()[2]
        self.session.headers['authorization'] = 'Bearer %s' % response.json()['token']
        return True

    def provides(self, types):
        types = set(x if not x.startswith('season.') else re.sub(r'[\d]', '%s', x) for x in types)
        return any(x in types for x in self.artmap.itervalues())

def shouldset_imagelanguage(image):
    if image['keyType'] == 'series':
        return image['subKey'] != 'blank'
    elif image['keyType'] == 'fanart':
        return image['subKey'] == 'text'
    return True

def typematches(arttype, types):
    return any(x for x in types if arttype == (x if not x.startswith('season.') else re.sub(r'[\d]', '%s', x)))
