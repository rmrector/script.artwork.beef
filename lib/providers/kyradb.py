import xbmc

from lib.libs import mediatypes
from lib.libs.addonsettings import settings
from lib.libs.pykodi import json, UTF8JSONDecoder
from lib.libs.utils import SortedDisplay
from lib.providers.base import AbstractImageProvider, ProviderError, cache, build_key_error

class KyraDBMovieProvider(AbstractImageProvider):
    name = SortedDisplay('kyradb.com', 'KyraDB.com')
    contenttype = 'application/json'
    mediatype = mediatypes.MOVIE

    apiurl = 'https://www.kyradb.com/api10/movie/{0}/images/{1}'
    animatedtypes = ('animatedposter', 'animatedfanart')
    provtypes = animatedtypes + ('characterart',)

    def provides(self, types):
        return any(x in self.provtypes for x in types)

    def get_images(self, uniqueids, types=None):
        mediaid = get_mediaid(uniqueids)
        if not mediaid:
            return {}
        if types is None:
            types = self.provtypes

        result = {}
        if any(x in self.animatedtypes for x in types):
            result.update(self._get_animated_images(mediaid))
        if 'characterart' in types:
            characterart = self._get_characterart(mediaid)
            if characterart:
                result['characterart'] = characterart

        return result

    def _get_animated_images(self, mediaid):
        data = self.get_data(mediaid, 'animated')
        if not data or data.get('error'):
            self.log(data)
            return {}
        baseposter = data['base_url_posters']
        basefanart = data['base_url_backgrounds']
        result = {}
        for poster in data['posters']:
            if 'animatedposter' not in result:
                result['animatedposter'] = []
            result['animatedposter'].append({'url': baseposter + '/' + poster['name'], 'language': 'en',
                'rating': SortedDisplay(poster['date_added'], poster['date_added']),
                'size': SortedDisplay(poster['height'], poster['resolution']), 'provider': self.name,
                'preview': baseposter + '/' + poster['name']})
        for fanart in data['backgrounds']:
            if 'animatedfanart' not in result:
                result['animatedfanart'] = []
            result['animatedfanart'].append({'url': basefanart + '/' + fanart['name'], 'language': None,
                'rating': SortedDisplay(fanart['date_added'], fanart['date_added']),
                'size': SortedDisplay(fanart['height'], fanart['resolution']), 'provider': self.name,
                'preview': basefanart + '/' + fanart['name']})

        return result

    def _get_characterart(self, mediaid):
        data = self.get_data(mediaid, 'characterart')
        if not data or data.get('error'):
            self.log(data)
            return {}
        baseurl = data['base_url_character_art']
        result = []
        for characterart in data['character_art']:
            result.append({'url': baseurl + '/' + characterart['name'], 'language': None,
                'rating': SortedDisplay(characterart['date_added'], characterart['date_added']),
                'size': SortedDisplay(characterart['height'], characterart['resolution']), 'provider': self.name,
                'preview': baseurl + '/' + characterart['name']})

        return result

    def get_data(self, mediaid, urltype):
        result = cache.cacheFunction(self._get_data, mediaid, urltype)
        return result if result != 'Empty' else None

    def _get_data(self, mediaid, urltype):
        apikey = settings.get_apikey('kyradb')
        if not apikey:
            raise build_key_error('kyradb')
        if not settings.kyradb_userkey:
            raise ProviderError("KyraDB User key is required for artwork from KyraDB: "
                + str(self.provtypes))
        headers = {'Apikey': apikey, 'Userkey': settings.kyradb_userkey}
        self.log('uncached', xbmc.LOGINFO)
        response = self.doget(self.apiurl.format(mediaid, urltype), headers=headers)
        return 'Empty' if response is None else json.loads(response.text, cls=UTF8JSONDecoder)

def get_mediaid(uniqueids):
    if 'tmdb' in uniqueids:
        return 'tmdbid/' + uniqueids['tmdb']
    if 'imdb' in uniqueids:
        return 'imdbid/' + uniqueids['imdb']
    return None
