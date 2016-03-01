import sys
import xbmc

from devhelper import pykodi

import mediatypes
from base import AbstractProvider
from providers import ProviderError
from sorteddisplaytuple import SortedDisplay

class TheTVDBProvider(AbstractProvider):
    name = SortedDisplay('thetvdb.com', 'TheTVDB.com')
    mediatype = mediatypes.TVSHOW

    apikey = '***REMOVED***'
    apiurl = 'https://api-beta.thetvdb.com/series/%s/images/query'
    imageurl_base = 'http://thetvdb.com/banners/'

    artmap = {'fanart': 'fanart', 'poster': 'poster', 'season': mediatypes.SEASON + '.%s.poster', 'seasonwide': mediatypes.SEASON + '.%s.banner', 'series': 'banner'}

    def __init__(self):
        super(TheTVDBProvider, self).__init__()
        self.set_contenttype('application/json')

    def get_data(self, mediaid, arttype, language):
        getparams = {'params': {'keyType': arttype}, 'headers': {'Accept-Language': language}}
        response = self.doget(self.apiurl % mediaid, **getparams)
        if response is None:
            return
        return response.json()

    def get_images(self, mediaid):
        # Bah. The new API needs a request for each art type, fanart/poster/season(poster)/seasonwide(banner)/series(banner)
        # And then double it for languages other than English, to grab fallback images in English
        # And TheTVDB has random unrelated languages attached to some fanart, even when the image itself doesn't have any text, so I can never be sure I have a list of all artwork
        result = {}
        languages = [pykodi.get_language(xbmc.ISO_639_1)]
        if languages[0] != 'en':
            languages.append('en')
        for arttype in self.artmap.keys():
            for language in languages:
                generaltype = self.artmap[arttype]
                data = self.get_data(mediaid, arttype, language)
                if data is None:
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
        loginurl = 'https://api-beta.thetvdb.com/login'
        response = self.session.post(loginurl, json={'apikey': self.apikey}, headers={'Content-Type': 'application/json'}, timeout=15)
        if not response or response.headers['Content-Type'] != 'application/json':
            raise ProviderError, "Provider returned unexected content", sys.exc_info()[2]
        self.session.headers['authorization'] = 'Bearer %s' % response.json()['token']
        return True

def shouldset_imagelanguage(image):
    if image['keyType'] == 'series':
        return image['subKey'] != 'blank'
    elif image['keyType'] == 'fanart':
        return image['subKey'] == 'text'
    return True
