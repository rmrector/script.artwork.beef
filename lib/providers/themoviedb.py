import xbmc
from abc import ABCMeta

from lib.libs import mediatypes
from lib.libs.addonsettings import settings
from lib.libs.pykodi import json, UTF8JSONDecoder
from lib.libs.utils import SortedDisplay
from lib.providers.base import AbstractProvider, AbstractImageProvider, cache, build_key_error

cfgurl = 'https://api.themoviedb.org/3/configuration'

class TheMovieDBAbstractProvider(AbstractImageProvider):
    __metaclass__ = ABCMeta
    contenttype = 'application/json'

    name = SortedDisplay('themoviedb.org', 'The Movie Database')
    _baseurl = None
    artmap = {}

    @property
    def baseurl(self):
        if not self._baseurl:
            apikey = settings.get_apikey('tmdb')
            if not apikey:
                raise build_key_error('tmdb')
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
        apikey = settings.get_apikey('tmdb')
        if not apikey:
            raise build_key_error('tmdb')
        self.log('uncached', xbmc.LOGINFO)
        response = self.doget(url, params={'api_key': apikey})
        return 'Empty' if response is None else json.loads(response.text, cls=UTF8JSONDecoder)

    def login(self):
        raise build_key_error('tmdb')

    def process_data(self, data):
        result = {}
        for arttype, artlist in data.iteritems():
            if arttype not in self.artmap:
                continue
            previewbit = 'w300' if arttype in ('backdrops', 'stills') else 'w342'
            for image in artlist:
                resultimage = {'url': self.baseurl + 'original' + image['file_path'], 'provider': self.name}
                resultimage['preview'] = self.baseurl + previewbit + image['file_path']
                resultimage['language'] = image['iso_639_1'] if image['iso_639_1'] != 'xx' else None
                resultimage['rating'] = self._get_rating(image)
                sortsize = image['width' if arttype != 'posters' else 'height']
                resultimage['size'] = SortedDisplay(sortsize, '{0}x{1}'.format(image['width'], image['height']))
                generaltype = self.artmap[arttype]
                if settings.use_tmdb_keyart and generaltype == 'poster' and not resultimage['language']:
                    generaltype = 'keyart'
                if generaltype not in result:
                    result[generaltype] = []
                result[generaltype].append(resultimage)
        return result

    def provides(self, types):
        return any(x in types for x in self.artmap.values())

class TheMovieDBMovieProvider(TheMovieDBAbstractProvider):
    mediatype = mediatypes.MOVIE

    apiurl = 'https://api.themoviedb.org/3/movie/%s/images'
    artmap = {'backdrops': 'fanart', 'posters': 'poster', 'posters-alt': 'keyart'}

    def get_images(self, uniqueids, types=None):
        if not settings.get_apienabled('tmdb'):
            return {}
        if types is not None and not self.provides(types):
            return {}
        mediaid = get_mediaid(uniqueids)
        if not mediaid:
            return {}
        if not self.baseurl:
            return {}
        data = self.get_data(self.apiurl % mediaid)
        if not data:
            return {}

        return self.process_data(data)

class TheMovieDBEpisodeProvider(TheMovieDBAbstractProvider):
    mediatype = mediatypes.EPISODE

    tvdbidsearch_url = 'https://api.themoviedb.org/3/find/%s?external_source=tvdb_id'
    apiurl = 'https://api.themoviedb.org/3/tv/%s/season/%s/episode/%s/images'
    artmap = {'stills': 'fanart'}

    def get_images(self, uniqueids, types=None):
        if not settings.get_apienabled('tmdb'):
            return {}
        if types is not None and not self.provides(types):
            return {}
        if not self.baseurl:
            return {}
        mediaid = get_mediaid(uniqueids, ('tmdbse', 'tvdb', 'tvdbse', 'unknown'))
        if not mediaid:
            return {}
        if 'tmdbse' in uniqueids:
            splits = mediaid.split('/')
            data = {'show_id': splits[0], 'season_number': splits[1], 'episode_number': splits[2]}
        elif 'tvdbse' in uniqueids and 'tvdb' not in uniqueids:
            splits = mediaid.split('/')
            data = self.get_data(self.tvdbidsearch_url % mediaid)
            if not data or not data['tv_results']:
                return {}
            data = data['tv_results'][0]
            data = {'show_id': data['id'], 'season_number': splits[1], 'episode_number': splits[2]}
        else:
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
    artmap = {'backdrops': 'fanart', 'posters': 'poster', 'posters-alt': 'keyart'}

    def get_images(self, uniqueids, types=None):
        if not settings.get_apienabled('tmdb'):
            return {}
        if types is not None and not self.provides(types):
            return {}
        mediaid = get_mediaid(uniqueids, ('tmdb', 'unknown'))
        if not mediaid:
            return {}
        if not self.baseurl:
            return {}
        data = self.get_data(self.apiurl % mediaid)
        if not data:
            return {}

        return self.process_data(data)

class TheMovieDBSearch(AbstractProvider):
    name = SortedDisplay('themoviedb.org:search', 'The Movie Database search')
    contenttype = 'application/json'

    searchurl = 'https://api.themoviedb.org/3/search/{0}'
    tvexternalidsurl = 'https://api.themoviedb.org/3/tv/{0}/external_ids'
    typemap = {mediatypes.MOVIESET: 'collection'}

    def get_data(self, url, params=None):
        result = cache.cacheFunction(self._get_data, url, params)
        return result if result != 'Empty' else None

    def _get_data(self, url, params=None):
        apikey = settings.get_apikey('tmdb')
        if not apikey:
            raise build_key_error('tmdb')
        self.log('uncached', xbmc.LOGINFO)
        if params is None:
            params = {'api_key': apikey}
        else:
            params = dict(params, api_key=apikey)
        response = self.doget(url, params=params)
        return 'Empty' if response is None else response.json()

    def login(self):
        raise build_key_error('tmdb')

    def search(self, query, mediatype):
        if mediatype not in self.typemap:
            return []
        url = self.searchurl.format(self.typemap[mediatype])
        data = self.get_data(url, {'query': query})
        if not data or 'results' not in data:
            return []

        return [{'label': item['name'], 'uniqueids': {'tmdb': item['id']}} for item in data['results']]

    def get_more_uniqueids(self, uniqueids, mediatype):
        if mediatype != mediatypes.TVSHOW or 'tvdb' in uniqueids:
            return {}
        mediaid = get_mediaid(uniqueids)
        url = self.tvexternalidsurl.format(mediaid)
        data = self.get_data(url)
        return {} if not data or not data.get('tvdb_id') else {'tvdb': data['tvdb_id']}

def get_mediaid(uniqueids, sources=('imdb', 'tmdb', 'unknown')):
    for source in sources:
        if source in uniqueids:
            return uniqueids[source]
