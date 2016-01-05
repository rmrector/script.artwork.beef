import requests
import xbmc

from devhelper.pykodi import log

import mediatypes
from base import AbstractProvider

# I can get good sized thumbnails from tmdb with 'w780' instead of 'original' in the URL
class TheMovieDbProvider(AbstractProvider):
    name = 'themoviedb.org'
    mediatype = mediatypes.MOVIE

    apikey = '5a0727308f37da772002755d6c073aee'
    cfgurl = 'http://api.themoviedb.org/3/configuration'
    apiurl = 'http://api.themoviedb.org/3/movie/%s/images'
    artmap = {'backdrops': 'fanart', 'poster': 'poster'}

    def log(self, message, level=xbmc.LOGDEBUG):
        log(message, level, tag=self.name)

    def _get_base_url(self):
        response = self.session.get(self.cfgurl, params={'api_key': self.apikey}, timeout=5)
        self.log(response.json()['images'])
        return response.json()['images']['base_url']

    def get_images(self, mediaid):
        self.log("Getting art for '%s'." % mediaid)
        response = self.session.get(self.apiurl % mediaid, params={'api_key': self.apikey}, timeout=5)
        if response.status_code == requests.codes.not_found:
            return {}
        response.raise_for_status()
        base_url = self._get_base_url()
        data = response.json()
        result = {}
        for arttype, artlist in data.iteritems():
            generaltype = self.artmap.get(arttype)
            if not generaltype:
                continue
            if artlist and generaltype not in result:
                result[generaltype] = []
            for image in artlist:
                resultimage = {'url': base_url + 'original' + image['file_path'], 'provider': self.name}
                resultimage['language'] = image['iso_639_1'] if image['iso_639_1'] != 'xx' else None
                if image['vote_count']:
                    resultimage['rating'] = (image['vote_average'], '{:1f}'.format(image['vote_average']))
                else:
                    resultimage['rating'] = (5, 'Not rated')
                resultimage['size'] = (image['width'], '%sx%s' % (image['width'], image['height']))
                result[generaltype].append(resultimage)
        return result
