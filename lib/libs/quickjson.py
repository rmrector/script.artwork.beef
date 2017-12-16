from itertools import chain

from lib.libs import mediatypes, pykodi
from lib.libs.pykodi import get_kodi_version, json, log

# [0] method part, [1] list: properties, [2] dict: extra params
typemap = {mediatypes.MOVIE: ('Movie', ['art', 'imdbnumber', 'file', 'premiered', 'uniqueid'], None),
    mediatypes.MOVIESET: ('MovieSet', ['art'], {'movies': {'properties': ['art', 'file']}}),
    mediatypes.TVSHOW: ('TVShow', ['art', 'imdbnumber', 'season', 'file', 'premiered', 'uniqueid'], None),
    mediatypes.EPISODE: ('Episode', ['art', 'uniqueid', 'tvshowid', 'season', 'episode', 'file', 'showtitle'], None),
    mediatypes.SEASON: ('Season', ['season', 'art'], None),
    mediatypes.MUSICVIDEO: ('MusicVideo', ['art', 'file', 'title', 'artist'], None),
    mediatypes.ARTIST: ('Artist', ['art', 'musicbrainzartistid'], None),
    mediatypes.ALBUM: ('Album', ['art', 'musicbrainzreleasegroupid'], None),
    mediatypes.SONG: ('Song', ['art', 'musicbrainztrackid'], None)}

def _needupgrade(mediatype):
    return mediatype in (mediatypes.MOVIE, mediatypes.TVSHOW) and get_kodi_version() < 17

def _upgradeproperties():
    if get_kodi_version() < 17:
        typemap[mediatypes.TVSHOW][1].remove('uniqueid')
        typemap[mediatypes.MOVIE][1].remove('premiered')
        typemap[mediatypes.MOVIE][1].remove('uniqueid')
        typemap[mediatypes.MOVIE][1].append('year')

_upgradeproperties()

def _upgradeitem(mediaitem, mediatype):
    if mediatype == mediatypes.MOVIE:
        mediaitem['premiered'] = '{0}-01-01'.format(mediaitem['year'])
        del mediaitem['year']
    if mediatype in (mediatypes.MOVIE, mediatypes.TVSHOW) and 'uniqueid' not in mediaitem:
        if mediaitem.get('imdbnumber'):
            mediaitem['uniqueid'] = {'unknown': mediaitem['imdbnumber']}
        else:
            mediaitem['uniqueid'] = {}

def get_item_details(dbid, mediatype):
    assert mediatype in typemap

    mapped = typemap[mediatype]
    basestr = 'VideoLibrary.Get{0}Details' if mediatype not in mediatypes.audiotypes else 'AudioLibrary.Get{0}Details'
    json_request = get_base_json_request(basestr.format(mapped[0]))
    json_request['params'][mediatype + 'id'] = dbid
    json_request['params']['properties'] = mapped[1]
    if mapped[2]:
        json_request['params'].update(mapped[2])
    json_result = pykodi.execute_jsonrpc(json_request)

    result_key = mediatype + 'details'
    if check_json_result(json_result, result_key, json_request):
        result = json_result['result'][result_key]
        if _needupgrade(mediatype):
            _upgradeitem(result, mediatype)
        return result

def get_item_list(mediatype, extraparams=None):
    assert mediatype in typemap

    mapped = typemap[mediatype]
    basestr = 'VideoLibrary.Get{0}s' if mediatype not in mediatypes.audiotypes else 'AudioLibrary.Get{0}s'
    json_request = get_base_json_request(basestr.format(mapped[0]))
    json_request['params']['sort'] = {'method': 'sorttitle', 'order': 'ascending'}
    json_request['params']['properties'] = mapped[1]
    if extraparams:
        json_request['params'].update(extraparams)
    json_result = pykodi.execute_jsonrpc(json_request)

    result_key = mediatype + 's'
    if check_json_result(json_result, result_key, json_request):
        result = json_result['result'][result_key]
        if _needupgrade(mediatype):
            for movie in result:
                _upgradeitem(movie, mediatype)
        return result
    else:
        return []

def get_albums(dbid=None):
    if dbid is None:
        return get_item_list(mediatypes.ALBUM)
    return get_item_list(mediatypes.ALBUM, {'filter': {'artistid': dbid}})

def get_songs(mediatype=None, dbid=None):
    if mediatype is None or dbid is None:
        return get_item_list(mediatypes.SONG)
    return get_item_list(mediatypes.SONG, {'filter': {mediatype + 'id': dbid}})

def get_tvshows(moreprops=False, includeprops=True):
    json_request = get_base_json_request('VideoLibrary.GetTVShows')
    if includeprops:
        json_request['params']['properties'] = typemap[mediatypes.TVSHOW][1] + ['year', 'plot'] \
            if moreprops else typemap[mediatypes.TVSHOW][1]
    json_request['params']['sort'] = {'method': 'sorttitle', 'order': 'ascending'}

    json_result = pykodi.execute_jsonrpc(json_request)
    if check_json_result(json_result, 'tvshows', json_request):
        result = json_result['result']['tvshows']
        if _needupgrade(mediatypes.TVSHOW):
            for tvshow in result:
                _upgradeitem(tvshow, mediatypes.TVSHOW)
        return result
    else:
        return []

def get_episodes(tvshow_id=None, limit=None):
    json_request = get_base_json_request('VideoLibrary.GetEpisodes')
    if tvshow_id:
        json_request['params']['tvshowid'] = tvshow_id
    json_request['params']['properties'] = typemap[mediatypes.EPISODE][1]
    json_request['params']['sort'] = {'method': 'dateadded', 'order': 'descending'}
    if limit:
        json_request['params']['limits'] = {'end': limit}

    json_result = pykodi.execute_jsonrpc(json_request)
    if check_json_result(json_result, 'episodes', json_request):
        return json_result['result']['episodes']
    else:
        return []

def get_seasons(tvshow_id=-1):
    if tvshow_id == -1 and pykodi.get_kodi_version() < 17:
        return _get_all_seasons_jarvis()
    else:
        return _inner_get_seasons(tvshow_id)

def _inner_get_seasons(tvshow_id=-1):
    json_request = get_base_json_request('VideoLibrary.GetSeasons')
    if tvshow_id != -1:
        json_request['params']['tvshowid'] = tvshow_id
    json_request['params']['properties'] = ['season', 'art']

    json_result = pykodi.execute_jsonrpc(json_request)

    if check_json_result(json_result, 'seasons', json_request):
        return json_result['result']['seasons']
    else:
        return []

def _get_all_seasons_jarvis():
    # DEPRECATED: Jarvis won't give me all seasons in one request, gotta do it the long way
    result = list(chain.from_iterable(_inner_get_seasons(tvshow['tvshowid']) for tvshow in get_tvshows(False, False)))
    return result

def set_item_details(dbid, mediatype, **details):
    assert mediatype in typemap

    mapped = typemap[mediatype]
    basestr = 'VideoLibrary.Set{0}Details' if mediatype not in mediatypes.audiotypes else 'AudioLibrary.Set{0}Details'
    json_request = get_base_json_request(basestr.format(mapped[0]))
    json_request['params'] = details
    json_request['params'][mediatype + 'id'] = dbid

    json_result = pykodi.execute_jsonrpc(json_request)
    if not check_json_result(json_result, 'OK', json_request):
        log(json_result)

def get_base_json_request(method):
    return {'jsonrpc': '2.0', 'method': method, 'params': {}, 'id': 1}

def get_application_properties(properties):
    json_request = get_base_json_request('Application.GetProperties')
    json_request['params']['properties'] = properties
    json_result = pykodi.execute_jsonrpc(json_request)
    if check_json_result(json_result, None, json_request):
        return json_result['result']

def check_json_result(json_result, result_key, json_request):
    if 'error' in json_result:
        raise JSONException(json_request, json_result)

    return 'result' in json_result and (not result_key or result_key in json_result['result'])

class JSONException(Exception):
    def __init__(self, json_request, json_result):
        self.json_request = json_request
        self.json_result = json_result

        message = "There was an error with a JSON-RPC request.\nRequest: "
        message += json.dumps(json_request, cls=pykodi.UTF8PrettyJSONEncoder)
        message += "\nResult: "
        message += json.dumps(json_result, cls=pykodi.UTF8PrettyJSONEncoder)

        super(JSONException, self).__init__(message)
