import requests
import xbmc

from devhelper import pykodi

import mediatypes
from base import AbstractProvider
from sorteddisplaytuple import SortedDisplay

# TheTVDB has small thumbnails, but I may want to use them
class TheTVDBProvider(AbstractProvider):
    name = 'thetvdb.com'
    mediatype = mediatypes.TVSHOW

    apikey = '8357F01B3F8F1393'
    apiurl = 'https://api-beta.thetvdb.com/series/%s/images/query'
    imageurl_base = 'http://thetvdb.com/banners/'

    artmap = {'fanart': 'fanart', 'poster': 'poster', 'season': mediatypes.SEASON + '.%s.poster', 'seasonwide': mediatypes.SEASON + '.%s.banner', 'series': 'banner'}

    def __init__(self):
        super(TheTVDBProvider, self).__init__()
        self.session.headers['Accept'] = 'application/json'

    def _get_response(self, mediaid, arttype, language):
        getparams = {'params': {'keyType': arttype}, 'headers': {'Accept-Language': language}}
        response = self.doget(self.apiurl % mediaid, **getparams)
        if response == None:
            return
        if response.status_code == requests.codes.unauthorized:
            self._login()
            response = self.doget(self.apiurl % mediaid, **getparams)
        return response

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
                response = self._get_response(mediaid, arttype, language)
                if response == None:
                    continue
                response.raise_for_status()

                generaltype = self.artmap[arttype]
                data = response.json()
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
                    resultimage['language'] = language
                    if image['ratingsInfo']['average']:
                        resultimage['rating'] = SortedDisplay(image['ratingsInfo']['average'], '{0:.1f} stars'.format(image['ratingsInfo']['average']))
                    else:
                        resultimage['rating'] = SortedDisplay(5, 'Not rated')
                    if arttype in ('series', 'seasonwide'):
                        resultimage['size'] = SortedDisplay(758, '758x140')
                    elif arttype == 'season':
                        resultimage['size'] = SortedDisplay(680, '680x1000')
                    else:
                        try:
                            resultimage['size'] = SortedDisplay(int(image['resolution'].split('x')[0]), image['resolution'])
                        except ValueError:
                            self.log('whoops, ValueError on "%s"' % image['resolution'].split('x')[0])
                            resultimage['size'] = SortedDisplay(0, image['resolution'])
                    result[ntype].append(resultimage)
        return result

    def _login(self):
        loginurl = 'https://api-beta.thetvdb.com/login'
        response = self.session.post(loginurl, json={'apikey': self.apikey}, headers={'Content-Type': 'application/json'}, timeout=15)
        self.session.headers['authorization'] = 'Bearer %s' % response.json()['token']
