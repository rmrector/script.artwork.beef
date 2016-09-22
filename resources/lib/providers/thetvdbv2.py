import re
import sys
import xbmc

from devhelper import pykodi

import mediatypes
import providers
from base import AbstractProvider, cache
from providers import ProviderError
from utils import SortedDisplay

# designed for version 2.1.0 of TheTVDB API
class TheTVDBProvider(AbstractProvider):
    name = SortedDisplay('thetvdb.com', 'TheTVDB.com')
    mediatype = mediatypes.TVSHOW

    apikey = '***REMOVED***'
    apiurl = 'https://api.thetvdb.com/series/%s/images/query'
    loginurl = 'https://api.thetvdb.com/login'
    imageurl_base = 'http://thetvdb.com/banners/'

    artmap = {'fanart': 'fanart', 'poster': 'poster', 'season': mediatypes.SEASON + '.%s.poster', 'seasonwide': mediatypes.SEASON + '.%s.banner', 'series': 'banner'}

    def __init__(self):
        super(TheTVDBProvider, self).__init__()
        self.set_contenttype('application/json')

    def get_data(self, mediaid, arttype, language):
        return cache.cacheFunction(self._get_data, mediaid, arttype, language)

    def _get_data(self, mediaid, arttype, language):
        self.log('uncached', xbmc.LOGINFO)
        getparams = {'params': {'keyType': arttype}, 'headers': {'Accept-Language': language}}
        response = self.doget(self.apiurl % mediaid, **getparams)
        return 'Empty' if response is None else response.json()

    def get_images(self, mediaid, types=None):
        if types and not self.provides(types):
            return {}
        result = {}
        languages = [pykodi.get_language(xbmc.ISO_639_1)]
        if languages[0] != 'en':
            languages.append('en')
        # Useful fanart can be hidden by the language filter, try a few of the most frequently used
        flanguages = ['en', 'de', 'fr', 'es', 'ru']
        if languages[0] not in flanguages:
            flanguages.append(languages[0])
        for arttype in self.artmap.keys():
            if types and not typematches(self.artmap[arttype], types):
                continue
            for language in languages if arttype != 'fanart' else flanguages:
                generaltype = self.artmap[arttype]
                data = self.get_data(mediaid, arttype, language)
                if data == 'Empty':
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
                    if image['ratingsInfo']['average']:
                        resultimage['rating'] = SortedDisplay(image['ratingsInfo']['average'], '{0:.1f} stars'.format(image['ratingsInfo']['average']))
                    else:
                        resultimage['rating'] = SortedDisplay(5, 'Not rated')
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
        response = self.session.post(self.loginurl, json={'apikey': self.apikey}, headers={'Content-Type': 'application/json', 'User-Agent': providers.useragent}, timeout=15)
        if not response or not response.headers['Content-Type'].startswith('application/json'):
            raise ProviderError, "Provider returned unexected content", sys.exc_info()[2]
        self.session.headers['authorization'] = 'Bearer %s' % response.json()['token']
        return True

    def provides(self, types):
        types = set(x if not x.startswith('season') else re.sub(r'[\d]', '%s', x) for x in types)
        return any(x in types for x in self.artmap.values())

def shouldset_imagelanguage(image):
    if image['keyType'] == 'series':
        return image['subKey'] != 'blank'
    elif image['keyType'] == 'fanart':
        return image['subKey'] == 'text'
    return True

def typematches(arttype, types):
    return any(x for x in types if arttype == (x if not x.startswith('season') else re.sub(r'[\d]', '%s', x)))
