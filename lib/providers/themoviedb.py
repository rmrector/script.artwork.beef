import xbmc
from abc import ABCMeta


from lib.providers.base import AbstractProvider, cache, Getter
from lib.libs import mediatypes
from lib.libs.pykodi import json, log, UTF8JSONDecoder
from lib.libs.utils import SortedDisplay

apikey = '5a0727308f37da772002755d6c073aee'
cfgurl = 'https://api.themoviedb.org/3/configuration'

class TheMovieDBAbstractProvider(AbstractProvider):
    __metaclass__ = ABCMeta

    name = SortedDisplay('themoviedb.org', 'The Movie Database')
    _baseurl = None
    artmap = None

    def __init__(self, *args):
        super(TheMovieDBAbstractProvider, self).__init__(*args)
        self.set_accepted_contenttype('application/json')

    @property
    def baseurl(self):
        if not self._baseurl:
            response = self.doget(cfgurl, params={'api_key': apikey})
            if response is None:
                return
            self._baseurl = response.json()['images']['secure_base_url']
        return self._baseurl

    def _get_rating(self, image):
        if image['vote_count']:
            # Reweigh ratings, increase difference from 5
            rating = image['vote_average']
            rating = 5 + (rating - 5) * 2
            return SortedDisplay(rating, '{0:.1f} stars'.format(image['vote_average']))
        else:
            return SortedDisplay(5, 'Not rated')

    def get_data(self, url):
        result = cache.cacheFunction(self._get_data, url)
        return result if result != 'Empty' else None

    def _get_data(self, url):
        self.log('uncached', xbmc.LOGINFO)
        response = self.doget(url, params={'api_key': apikey})
        return 'Empty' if response is None else json.loads(response.text, cls=UTF8JSONDecoder)

    def process_data(self, data):
        result = {}
        for arttype, artlist in data.iteritems():
            generaltype = self.artmap.get(arttype)
            if not generaltype:
                continue
            if artlist and generaltype not in result:
                result[generaltype] = []
            previewbit = 'w300' if arttype in ('backdrops', 'stills') else 'w342'
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

class TheMovieDBMovieProvider(TheMovieDBAbstractProvider):
    mediatype = mediatypes.MOVIE

    apiurl = 'https://api.themoviedb.org/3/movie/%s/images'
    artmap = {'backdrops': 'fanart', 'posters': 'poster'}

    def get_images(self, mediaid, types=None):
        if types and not self.provides(types):
            return {}
        if not self.baseurl:
            return {}
        data = self.get_data(self.apiurl % mediaid)
        if not data:
            return {}

        return self.process_data(data)

    def provides(self, types):
        return any(x in types for x in self.artmap.values())

class TheMovieDBEpisodeProvider(TheMovieDBAbstractProvider):
    mediatype = mediatypes.EPISODE

    tvdbidsearch_url = 'https://api.themoviedb.org/3/find/%s?external_source=tvdb_id'
    apiurl = 'https://api.themoviedb.org/3/tv/%s/season/%s/episode/%s/images'
    artmap = {'stills': 'fanart'}

    def get_images(self, mediaid, types=None):
        if not self.baseurl:
            return {}
        data = self.get_data(self.tvdbidsearch_url % mediaid)
        if not data or not data['tv_episode_results']:
            return {}
        data = data['tv_episode_results'][0]
        data = self.get_data(self.apiurl % (data['show_id'], data['season_number'], data['episode_number']))
        if not data:
            return {}

        return self.process_data(data)

class TheMovieDBMovieSetProvider(TheMovieDBAbstractProvider):
    mediatype = mediatypes.MOVIESET

    apiurl = 'https://api.themoviedb.org/3/collection/%s/images'
    artmap = {'backdrops': 'fanart', 'posters': 'poster'}

    def get_images(self, mediaid, types=None):
        # mediaid = TMDB ID
        if types and not self.provides(types):
            return {}
        if not self.baseurl:
            return {}
        data = self.get_data(self.apiurl % mediaid)
        if not data:
            return {}

        return self.process_data(data)

    def provides(self, types):
        return any(x in types for x in self.artmap.values())

class TheMovieDBSearch(object):
    searchurl = 'https://api.themoviedb.org/3/search/{0}'
    typemap = {mediatypes.MOVIESET: 'collection'}
    _baseurl = None

    def __init__(self, session):
        self.getter = Getter(session)
        self.getter.set_accepted_contenttype('application/json')

    def log(self, message, level=xbmc.LOGDEBUG):
        log(message, level, 'themoviedb.org:search')

    @property
    def baseurl(self):
        if not self._baseurl:
            response = self.getter.get(cfgurl, params={'api_key': apikey})
            if response is None:
                return
            self._baseurl = response.json()['images']['base_url']
        return self._baseurl

    def get_data(self, url, params=None):
        result = cache.cacheFunction(self._get_data, url, params)
        return result if result != 'Empty' else None

    def _get_data(self, url, params=None):
        self.log('uncached', xbmc.LOGINFO)
        if params is None:
            params = {'api_key': apikey}
        else:
            params = dict(params, api_key=apikey)
        response = self.getter.get(url, params=params)
        return 'Empty' if response is None else response.json()

    def search(self, query, mediatype):
        if mediatype not in self.typemap:
            return []
        if not self.baseurl:
            return []
        url = self.searchurl.format(self.typemap[mediatype])
        data = self.get_data(url, {'query': query})
        if not data or 'results' not in data:
            return []

        return [{'label': item['name'], 'id': item['id']} for item in data['results']]
