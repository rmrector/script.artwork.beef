import re
import xbmc
from math import pi, sin

from lib.providers import base
from lib.providers.base import AbstractImageProvider, build_key_error, cache, ProviderError
from lib.libs import mediatypes
from lib.libs.addonsettings import settings
from lib.libs.pykodi import json, UTF8JSONDecoder
from lib.libs.utils import SortedDisplay

# designed for version 2.1.0 of TheTVDB API
class TheTVDBProvider(AbstractImageProvider):
    name = SortedDisplay('thetvdb.com', 'TheTVDB.com')
    mediatype = mediatypes.TVSHOW
    contenttype = 'application/json'

    apiurl = 'https://api.thetvdb.com/series/%s/images/query'
    loginurl = 'https://api.thetvdb.com/login'
    imageurl_base = 'https://www.thetvdb.com/banners/'

    artmap = {'fanart': 'fanart', 'poster': 'poster', 'season': mediatypes.SEASON + '.%s.poster',
        'seasonwide': mediatypes.SEASON + '.%s.banner', 'series': 'banner'}

    def get_data(self, mediaid, arttype, language):
        result = cache.cacheFunction(self._get_data, mediaid, arttype, language)
        return result if result != 'Empty' else None

    def _get_data(self, mediaid, arttype, language):
        if not settings.get_apikey('tvdb'):
            raise build_key_error('tvdb')
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

    def get_images(self, uniqueids, types=None):
        if not settings.get_apienabled('tvdb'):
            return {}
        if types is not None and not self.provides(types):
            return {}
        mediaid = get_mediaid(uniqueids)
        if not mediaid:
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
                    if not image.get('fileName') or isseason and not image.get('subKey'):
                        continue
                    ntype = generaltype
                    if isseason:
                        ntype = ntype % image['subKey']
                        if ntype not in result:
                            result[ntype] = []
                    resultimage = {'provider': self.name}
                    resultimage['url'] = self.imageurl_base + image['fileName']
                    resultimage['preview'] = self.imageurl_base + (image['thumbnail'] or '_cache/' + image['fileName'])
                    resultimage['language'] = language if shouldset_imagelanguage(image) else None
                    resultimage['rating'] = self._get_rating(image)
                    if arttype in ('series', 'seasonwide'):
                        resultimage['size'] = SortedDisplay(758, '758x140')
                    elif arttype == 'season':
                        resultimage['size'] = SortedDisplay(1000, '680x1000')
                    else:
                        resultimage['size'] = parse_sortsize(image, arttype)
                    result[ntype].append(resultimage)
        return result

    def login(self):
        response = self.getter.session.post(self.loginurl, json={'apikey': settings.get_apikey('tvdb')},
            headers={'Content-Type': 'application/json', 'User-Agent': settings.useragent}, timeout=15)
        if response is not None and response.status_code == 401:
            raise build_key_error('tvdb')
        if not response or not response.headers['Content-Type'].startswith('application/json'):
            raise ProviderError("Provider returned unexected content")
        self.getter.session.headers['authorization'] = 'Bearer %s' % response.json()['token']
        return True

    def provides(self, types):
        types = set(x if not x.startswith('season.') else re.sub(r'[\d]', '%s', x) for x in types)
        return any(x in types for x in self.artmap.values())

def parse_sortsize(image, arttype):
    try:
        sortsize = int(image['resolution'].split('x')[0 if arttype != 'poster' else 1])
    except (ValueError, IndexError):
        sortsize = 0
    return SortedDisplay(sortsize, image['resolution'])

def shouldset_imagelanguage(image):
    if image['keyType'] == 'series':
        return image['subKey'] != 'blank'
    elif image['keyType'] == 'fanart':
        return image['subKey'] == 'text'
    return True

def typematches(arttype, types):
    return any(x for x in types if arttype == (x if not x.startswith('season.') else re.sub(r'[\d]', '%s', x)))

def get_mediaid(uniqueids):
    for source in ('tvdb', 'unknown'):
        if source in uniqueids:
            return uniqueids[source]
