import requests
import xbmc

from devhelper import pykodi
from devhelper.pykodi import log

import mediatypes
from base import AbstractProvider

# TheTVDB has small thumbnails, but I may want to use them
class TheTVDBProvider(AbstractProvider):
    name = 'thetvdb.com'
    mediatype = mediatypes.TVSHOW

    apikey = '***REMOVED***'
    apiurl = 'https://api-beta.thetvdb.com/series/%s/images/query'
    imageurl_base = 'http://thetvdb.com/banners/'

    artmap = {'fanart': 'fanart', 'poster': 'poster', 'season': mediatypes.SEASON + '.%s.poster', 'seasonwide': mediatypes.SEASON + '.%s.banner', 'series': 'banner'}

    def __init__(self):
        super(TheTVDBProvider, self).__init__()
        self.session.headers['Accept'] = 'application/json'

    def log(self, message, level=xbmc.LOGDEBUG):
        log(message, level, tag=self.name)

    def _request_images(self, mediaid, arttype, language):
        get_params = {'params': {'keyType': arttype}, 'headers': {'Accept-Language': language}, 'timeout': 10}
        response = self._get_response(self.apiurl % mediaid, **get_params)
        return response

    def _get_response(self, url, **params):
        response = self.session.get(url, **params)
        if response.status_code == requests.codes.unauthorized:
            self._login()
            response = self.session.get(url, **params)
        return response

    def get_images(self, mediaid):
        # Bah. The new API needs a request for each art type, fanart/poster/season(poster)/seasonwide(banner)/series(banner)
        # And then double it for languages other than English, to grab fallback images in English
        # And TheTVDB has random unrelated languages attached to some fanart, even when the image itself doesn't have any text, so I can never be sure I have a list of all artwork
        self.log("Getting art for '%s'." % mediaid)
        result = {}
        languages = [pykodi.get_language(xbmc.ISO_639_1)]
        if languages[0] != 'en':
            languages.append('en')
        for arttype in self.artmap.keys():
            for language in languages:
                response = self._request_images(mediaid, arttype, language)
                if response.status_code == requests.codes.not_found:
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
                        resultimage['rating'] = (image['ratingsInfo']['average'], '{:.1f}'.format(image['ratingsInfo']['average']))
                    else:
                        resultimage['rating'] = (5, 'Not rated')
                    if arttype in ('series', 'seasonwide'):
                        resultimage['size'] = (758, '758x140')
                    elif arttype == 'season':
                        resultimage['size'] = (680, '680x1000')
                    else:
                        try:
                            resultimage['size'] = (int(image['resolution'].split('x')[0]), image['resolution'])
                        except ValueError:
                            self.log('whoops, ValueError on "%s"' % image['resolution'].split('x')[0])
                            resultimage['size'] = (0, '')
                    result[ntype].append(resultimage)
        return result

    def _login(self):
        loginurl = 'https://api-beta.thetvdb.com/login'
        response = self.session.post(loginurl, json={'apikey': self.apikey}, headers={'Content-Type': 'application/json'}, timeout=5)
        self.session.headers['authorization'] = 'Bearer %s' % response.json()['token']
