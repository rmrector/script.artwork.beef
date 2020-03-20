import xbmc

from lib.libs import iso639, mediatypes
from lib.libs.addonsettings import settings
from lib.libs.pykodi import json, UTF8JSONDecoder
from lib.libs.utils import SortedDisplay
from lib.providers.base import AbstractImageProvider, ProviderError, cache

class KyraDBMovieProvider(AbstractImageProvider):
    name = SortedDisplay('kyradb.com', 'KyraDB.com')
    contenttype = 'application/json'
    mediatype = mediatypes.MOVIE

    apiurl = 'https://www.kyradb.com/api10/movie/{0}/images/{1}'
    animatedtypes = ('animatedposter', 'animatedkeyart', 'animatedfanart')
    provtypes = animatedtypes + ('characterart',)

    def provides(self, types):
        return any(x in self.provtypes for x in types)

    def get_images(self, uniqueids, types=None):
        if not settings.get_apienabled('kyradb'):
            return {}
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
        if not data:
            return {}
        baseposter = data['base_url_posters']
        basefanart = data['base_url_backgrounds']
        result = {}
        for poster in data['posters']:
            newposter = {
                'url': baseposter + '/' + poster['name'],
                'language': get_language(poster.get('language', None)),
                'rating': SortedDisplay(poster['likes'], '{0} likes'.format(poster['likes'])),
                'size': SortedDisplay(poster['height'], poster['resolution']),
                'provider': self.name,
                'preview': baseposter + '/' + poster['name']}

            arttype = 'animatedposter' if newposter['language'] else 'animatedkeyart'
            if arttype not in result:
                result[arttype] = []
            result[arttype].append(newposter)
        for fanart in data['backgrounds']:
            if 'animatedfanart' not in result:
                result['animatedfanart'] = []
            result['animatedfanart'].append({
                'url': basefanart + '/' + fanart['name'],
                'language': None,
                'rating': SortedDisplay(fanart['likes'], '{0} likes'.format(fanart['likes'])),
                'size': SortedDisplay(fanart['height'], fanart['resolution']),
                'provider': self.name,
                'preview': basefanart + '/' + fanart['name']})

        return result

    def _get_characterart(self, mediaid):
        data = self.get_data(mediaid, 'characterart')
        if not data:
            return {}
        baseurl = data['base_url_character_art']
        result = []
        for characterart in data['character_art']:
            result.append({
                'url': baseurl + '/' + characterart['name'],
                'language': None,
                'rating': SortedDisplay(characterart['likes'], '{0} likes'.format(characterart['likes'])),
                'size': SortedDisplay(characterart['height'], characterart['resolution']),
                'provider': self.name,
                'preview': baseurl + '/' + characterart['name']})

        return result

    def get_data(self, mediaid, urltype):
        result = cache.cacheFunction(self._get_data, mediaid, urltype)
        return result if result != 'Empty' else None

    def _get_data(self, mediaid, urltype):
        if not settings.kyradb_user_apikey or not settings.kyradb_userkey:
            raise ProviderError("KyraDB API key and User key is required for artwork from KyraDB: "
                + str(self.provtypes))
        headers = {'Apikey': settings.kyradb_user_apikey, 'Userkey': settings.kyradb_userkey}
        self.log('uncached', xbmc.LOGINFO)
        response = self.doget(self.apiurl.format(mediaid, urltype), headers=headers)
        result = json.loads(response.text, cls=UTF8JSONDecoder) if response is not None else None
        if result and result.get('error'):
            if result['error'] != 4:
                # 4: "No results"
                raise ProviderError(result['message'])
            result = None
        return 'Empty' if result is None else result

def get_mediaid(uniqueids):
    if 'tmdb' in uniqueids:
        return 'tmdbid/' + uniqueids['tmdb']
    if 'imdb' in uniqueids:
        return 'imdbid/' + uniqueids['imdb']
    return None

def get_language(kdb_language):
    if not kdb_language or kdb_language == 'unknown':
        return None
    try:
        return iso639.to_iso639_1(kdb_language)
    except iso639.NonExistentLanguageError:
        return 'xx'
