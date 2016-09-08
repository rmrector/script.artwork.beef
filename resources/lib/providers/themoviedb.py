from abc import ABCMeta

import mediatypes
from base import AbstractProvider
from utils import SortedDisplay

class TheMovieDBAbstractProvider(AbstractProvider):
    # pylint: disable=W0223
    __metaclass__ = ABCMeta

    name = SortedDisplay('themoviedb.org', 'The Movie Database')
    cfgurl = 'http://api.themoviedb.org/3/configuration'
    apikey = '***REMOVED***'
    _baseurl = None

    def __init__(self):
        super(TheMovieDBAbstractProvider, self).__init__()
        self.set_contenttype('application/json')

    @property
    def baseurl(self):
        if not self._baseurl:
            response = self.doget(self.cfgurl, params={'api_key': self.apikey})
            if response is None:
                return
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

    def get_data(self, url):
        response = self.doget(url, params={'api_key': self.apikey})
        if response is None:
            return
        return response.json()

class TheMovieDBProvider(TheMovieDBAbstractProvider):
    mediatype = mediatypes.MOVIE

    apiurl = 'http://api.themoviedb.org/3/movie/%s/images'
    artmap = {'backdrops': 'fanart', 'posters': 'poster'}

    def get_images(self, mediaid, types=None):
        if types and not self.provides(types):
            return {}
        if not self.baseurl:
            return {}
        data = self.get_data(self.apiurl % mediaid)
        if data is None:
            return {}
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
                if arttype == 'backdrops':
                    resultimage['language'] = image['iso_639_1'] if image['iso_639_1'] != 'xx' else None
                else:
                    resultimage['language'] = image['iso_639_1']
                resultimage['rating'] = self._get_rating(image)
                sortsize = image['width' if arttype != 'posters' else 'height']
                resultimage['size'] = SortedDisplay(sortsize, '{0}x{1}'.format(image['width'], image['height']))
                result[generaltype].append(resultimage)
        return result

    def provides(self, types):
        return any(x in types for x in self.artmap.values())

class TheMovieDBEpisodeProvider(TheMovieDBAbstractProvider):
    mediatype = mediatypes.EPISODE

    tvdbidsearch_url = 'http://api.themoviedb.org/3/find/%s?external_source=tvdb_id'
    apiurl = 'http://api.themoviedb.org/3/tv/%s/season/%s/episode/%s/images'
    artmap = {'stills': 'fanart'}

    def __init__(self):
        super(TheMovieDBEpisodeProvider, self).__init__()
        self.session.headers['Accept'] = 'application/json'

    def get_images(self, mediaid, types=None):
        if not self.baseurl:
            return {}
        data = self.get_data(self.tvdbidsearch_url % mediaid)
        if data is None or not data['tv_episode_results']:
            return {}
        data = data['tv_episode_results'][0]
        data = self.get_data(self.apiurl % (data['show_id'], data['season_number'], data['episode_number']))
        if data is None:
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
