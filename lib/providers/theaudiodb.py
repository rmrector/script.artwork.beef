import xbmc

from lib.libs import mediatypes
from lib.libs.pykodi import json, UTF8JSONDecoder
from lib.libs.utils import SortedDisplay
from lib.providers.base import AbstractProvider, AbstractImageProvider, cache

api_key = '***REMOVED***'

class TheAudioDBMusicVideoProvider(AbstractImageProvider):
    name = SortedDisplay('theaudiodb.com', 'TheAudioDB.com')
    mediatype = mediatypes.MUSICVIDEO
    contenttype = 'application/json'

    # i=MB track/album/artist ID
    url_trackinfo = 'http://www.theaudiodb.com/api/v1/json/{0}/track-mb.php'.format(api_key)
    url_albuminfo = 'http://www.theaudiodb.com/api/v1/json/{0}/album-mb.php'.format(api_key)
    url_artistinfo = 'http://www.theaudiodb.com/api/v1/json/{0}/artist-mb.php'.format(api_key)

    artmap = {'strTrackThumb': 'poster', 'strAlbumThumb': 'poster', 'strAlbumCDart': 'cdart',
        'strArtistThumb': 'artistthumb', 'strArtistLogo': 'clearlogo', 'strArtistBanner': 'banner',
        'strArtistFanart': 'fanart', 'strArtistFanart2': 'fanart', 'strArtistFanart3': 'fanart'}

    def get_data(self, url, params):
        result = cache.cacheFunction(self._get_data, url, params)
        return result if result != 'Empty' else None

    def _get_data(self, url, params):
        self.log('uncached', xbmc.LOGINFO)
        response = self.doget(url, params)
        return 'Empty' if response is None else json.loads(response.text, cls=UTF8JSONDecoder)

    def get_images(self, uniqueids, types=None):
        if types is not None and not self.provides(types) or not ('mbid_track' in uniqueids or
                'mbid_album' in uniqueids or 'mbid_artist' in uniqueids):
            return {}

        def smashtype(data, originaltype, images, imagetitle=None):
            if data.get(originaltype):
                _insertart(images, self.artmap[originaltype], self._build_image(data[originaltype],
                    _get_imagesize(originaltype), imagetitle))

        images = {}
        if 'mbid_track' in uniqueids:
            # IDEA: There are also thumbnails here
            data = self.get_data(self.url_trackinfo, {'i': uniqueids['mbid_track']})
            if data and data.get('track'):
                smashtype(data['track'][0], 'strTrackThumb', images, 'track')
        if 'mbid_album' in uniqueids:
            data = self.get_data(self.url_albuminfo, {'i': uniqueids['mbid_album']})
            if data and data.get('album'):
                smashtype(data['album'][0], 'strAlbumThumb', images, 'album')
                smashtype(data['album'][0], 'strAlbumCDart', images)
        if 'mbid_artist' in uniqueids:
            data = self.get_data(self.url_artistinfo, {'i': uniqueids['mbid_artist']})
            if data and data.get('artists'):
                data = data['artists'][0]
                for otype in ('strArtistThumb', 'strArtistLogo', 'strArtistBanner',
                        'strArtistFanart', 'strArtistFanart2', 'strArtistFanart3'):
                    smashtype(data, otype, images)
        return images

    def provides(self, types):
        return any(x in types for x in self.artmap.values())

    def _build_image(self, url, size, title=None):
        result = {'provider': self.name, 'url': url, 'preview': url + '/preview',
            'size': size, 'language': None, 'rating': SortedDisplay(5.1 if title == 'track' else 5.0, '')}
        if title:
            result['title'] = title
        return result

def _get_imagesize(arttype):
    if arttype in ('strTrackThumb', 'strAlbumThumb', 'strArtistThumb'):
        return SortedDisplay(500, '500-800')
    if arttype in ('strAlbumCDart',):
        return SortedDisplay(500, '500 or 1000')
    if arttype in ('strArtistLogo',):
        return SortedDisplay(400, '400x155 or 800x310')
    if arttype in ('strArtistBanner',):
        return SortedDisplay(1000, '1000x185')
    if arttype in ('strArtistFanart', 'strArtistFanart2', 'strArtistFanart3'):
        return SortedDisplay(1280, '1280x720 or 1920x1080')
    return SortedDisplay(0, '')

def _insertart(images, arttype, image):
    if arttype not in images:
        images[arttype] = []
    images[arttype].append(image)

class TheAudioDBSearch(AbstractProvider):
    name = SortedDisplay('theaudiodb.com:search', 'TheAudioDB.com search')
    contenttype = 'application/json'

    # s=[artist], t=[track title]
    url_trackby_artistandtrack = 'http://www.theaudiodb.com/api/v1/json/{0}/searchtrack.php'.format(api_key)

    def get_data(self, url, params=None):
        result = cache.cacheFunction(self._get_data, url, params)
        return result if result != 'Empty' else None

    def _get_data(self, url, params=None):
        self.log('uncached', xbmc.LOGINFO)
        if params is None:
            params = {}
        response = self.doget(url, params=params)
        return 'Empty' if response is None else response.json()

    def search(self, query, mediatype):
        if mediatype != mediatypes.MUSICVIDEO:
            return []
        query = query.split(' - ', 1)
        if len(query) != 2:
            return []
        data = self.get_data(self.url_trackby_artistandtrack, {'s': query[0], 't': query[1]})
        if not data or not data.get('track'):
            return []

        return [{'label': item['strArtist'] + ' - ' + item['strTrack'], 'uniqueids':
            {'mbid_track': item['strMusicBrainzID'], 'mbid_artist': item['strMusicBrainzArtistID'],
            'mbid_album': item['strMusicBrainzAlbumID']}} for item in data['track']]
