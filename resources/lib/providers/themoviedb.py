import requests
import xbmc

from abc import ABCMeta

from devhelper.pykodi import log

import mediatypes
import providers
from base import AbstractProvider
from sorteddisplaytuple import SortedDisplay

# TODO: I can get good sized thumbnails from tmdb with 'w780' instead of 'original' in the URL
# TODO: Reweigh ratings, as this does the exact opposite of thetvdb, and weighs each single rating very lowly, images rarely hit 6 stars, nor go lower than 4.7

class TheMovieDBAbstractProvider(AbstractProvider):
    # pylint: disable=W0223
    __metaclass__ = ABCMeta

    name = 'themoviedb.org'
    cfgurl = 'http://api.themoviedb.org/3/configuration'
    apikey = '5a0727308f37da772002755d6c073aee'

    def __init__(self):
        super(TheMovieDBAbstractProvider, self).__init__()
        self.session.headers['Accept'] = 'application/json'

    def _get_base_url(self):
        response = self.session.get(self.cfgurl, params={'api_key': self.apikey}, timeout=5)
        return response.json()['images']['base_url']

    def _get_rating(self, image):
        if image['vote_count']:
            # Reweigh ratings, as themoviedb does the exact opposite of thetvdb, and weighs each single rating very lowly, images rarely hit 6 stars, nor go lower than 4.7
            rating = image['vote_average']
            rating = 5 + (rating - 5) * 3
            return SortedDisplay(rating, '{0:.1f} stars'.format(image['vote_average']))
        else:
            return SortedDisplay(5, 'Not rated')

class TheMovieDBProvider(TheMovieDBAbstractProvider):
    mediatype = mediatypes.MOVIE

    apiurl = 'http://api.themoviedb.org/3/movie/%s/images'
    artmap = {'backdrops': 'fanart', 'posters': 'poster'}

    def log(self, message, level=xbmc.LOGDEBUG):
        log(message, level, tag=self.name)

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
                resultimage['language'] = image['iso_639_1']
                resultimage['rating'] = self._get_rating(image)
                resultimage['size'] = SortedDisplay(image['width'], '%sx%s' % (image['width'], image['height']))
                if arttype == 'poster' and image['aspect_ratio'] > 0.685 or image['aspect_ratio'] < 0.66:
                    resultimage['status'] = providers.GOOFY_IMAGE
                result[generaltype].append(resultimage)
        return result

class TheMovieDBEpisodeProvider(TheMovieDBAbstractProvider):
    mediatype = mediatypes.EPISODE

    tvdbidsearch_url = 'http://api.themoviedb.org/3/find/%s?external_source=tvdb_id'
    apiurl = 'http://api.themoviedb.org/3/tv/%s/season/%s/episode/%s/images'
    artmap = {'stills': 'fanart'}

    def __init__(self):
        super(TheMovieDBEpisodeProvider, self).__init__()
        self.session.headers['Accept'] = 'application/json'

    def log(self, message, level=xbmc.LOGDEBUG):
        log(message, level, tag=self.name + '.episode')

    def get_images(self, mediaid):
        self.log("Getting art for '%s'." % mediaid)
        response = self.session.get(self.tvdbidsearch_url % mediaid, params={'api_key': self.apikey}, timeout=5)
        if response.status_code == requests.codes.not_found:
            return {}
        response.raise_for_status()
        data = response.json()
        if not data['tv_episode_results']:
            return {}
        data = data['tv_episode_results'][0]
        response = self.session.get(self.apiurl % (data['show_id'], data['season_number'], data['episode_number']), params={'api_key': self.apikey}, timeout=5)
        if response.status_code == requests.codes.not_found:
            return {}
        response.raise_for_status()
        data = response.json()
        base_url = self._get_base_url()
        result = {}
        for arttype, artlist in data.iteritems():
            generaltype = self.artmap.get(arttype)
            if not generaltype:
                continue
            if artlist and generaltype not in result:
                result[generaltype] = []
            for image in artlist:
                resultimage = {'url': base_url + 'original' + image['file_path'], 'provider': self.name}
                resultimage['language'] = image['iso_639_1']
                resultimage['rating'] = self._get_rating(image)
                resultimage['size'] = SortedDisplay(image['width'], '%sx%s' % (image['width'], image['height']))
                result[generaltype].append(resultimage)
        return result
