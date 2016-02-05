from abc import ABCMeta

import mediatypes
from base import AbstractProvider
from sorteddisplaytuple import SortedDisplay

# TODO: I can get good sized thumbnails from tmdb with 'w780' instead of 'original' in the URL

class TheMovieDBAbstractProvider(AbstractProvider):
    # pylint: disable=W0223
    __metaclass__ = ABCMeta

    name = 'themoviedb.org'
    cfgurl = 'http://api.themoviedb.org/3/configuration'
    apikey = '5a0727308f37da772002755d6c073aee'
    _baseurl = None

    def __init__(self):
        super(TheMovieDBAbstractProvider, self).__init__()
        self.session.headers['Accept'] = 'application/json'

    @property
    def baseurl(self):
        if not self._baseurl:
            response = self.doget(self.cfgurl, params={'api_key': self.apikey})
            if response != None:
                response.raise_for_status()
                self._baseurl = response.json()['images']['base_url']
        return self._baseurl

    def _get_rating(self, image):
        if image['vote_count']:
            # Reweigh ratings, as themoviedb weighs each single rating very lowly
            rating = image['vote_average']
            rating = 5 + (rating - 5) * 3
            return SortedDisplay(rating, '{0:.1f} stars'.format(image['vote_average']))
        else:
            return SortedDisplay(5, 'Not rated')

class TheMovieDBProvider(TheMovieDBAbstractProvider):
    mediatype = mediatypes.MOVIE

    apiurl = 'http://api.themoviedb.org/3/movie/%s/images'
    artmap = {'backdrops': 'fanart', 'posters': 'poster'}

    def get_images(self, mediaid):
        response = self.doget(self.apiurl % mediaid, params={'api_key': self.apikey})
        if response == None:
            return {}
        response.raise_for_status()
        if not self.baseurl:
            return {}
        data = response.json()
        result = {}
        for arttype, artlist in data.iteritems():
            generaltype = self.artmap.get(arttype)
            if not generaltype:
                continue
            if artlist and generaltype not in result:
                result[generaltype] = []
            previewbit = 'w300' if arttype == 'backdrops' else 'w342'
            for image in artlist:
                resultimage = {'url': self.baseurl + 'original' + image['file_path'], 'provider': self.name}
                resultimage['preview'] = self.baseurl + previewbit + image['file_path']
                resultimage['language'] = image['iso_639_1']
                resultimage['rating'] = self._get_rating(image)
                resultimage['size'] = SortedDisplay(image['width'], '%sx%s' % (image['width'], image['height']))
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

    def get_images(self, mediaid):
        response = self.doget(self.tvdbidsearch_url % mediaid, params={'api_key': self.apikey})
        if response == None:
            return {}
        response.raise_for_status()
        data = response.json()
        if not data['tv_episode_results']:
            return {}
        data = data['tv_episode_results'][0]
        response = self.doget(self.apiurl % (data['show_id'], data['season_number'], data['episode_number']), params={'api_key': self.apikey})
        if response == None:
            return {}
        response.raise_for_status()
        data = response.json()
        if not self.baseurl:
            return {}
        result = {}
        for arttype, artlist in data.iteritems():
            generaltype = self.artmap.get(arttype)
            if not generaltype:
                continue
            if artlist and generaltype not in result:
                result[generaltype] = []
            for image in artlist:
                resultimage = {'url': self.baseurl + 'original' + image['file_path'], 'provider': self.name}
                resultimage['preview'] = self.baseurl + 'w300' + image['file_path']
                resultimage['language'] = image['iso_639_1']
                resultimage['rating'] = self._get_rating(image)
                resultimage['size'] = SortedDisplay(image['width'], '%sx%s' % (image['width'], image['height']))
                result[generaltype].append(resultimage)
        return result
