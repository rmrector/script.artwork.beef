from itertools import chain

from lib.libs import mediatypes, pykodi
from lib.libs.pykodi import get_kodi_version, json, log

# [0] method part
typemap = {mediatypes.MOVIE: ('Movie',),
    mediatypes.MOVIESET: ('MovieSet',),
    mediatypes.TVSHOW: ('TVShow',),
    mediatypes.EPISODE: ('Episode',),
    mediatypes.SEASON: ('Season',)}

tvshow_properties = ['art', 'imdbnumber', 'season', 'file', 'premiered', 'uniqueid']
more_tvshow_properties = tvshow_properties + ['plot', 'year']
movie_properties = ['art', 'imdbnumber', 'file', 'premiered', 'uniqueid']
movieset_properties = ['art']
episode_properties = ['art', 'uniqueid', 'tvshowid', 'season', 'file', 'showtitle']

def _needupgrade(mediatype):
    return mediatype == 'movie' and get_kodi_version() < 17

def _upgradeproperties():
    if get_kodi_version() < 17:
        tvshow_properties.remove('uniqueid')
        more_tvshow_properties.remove('uniqueid')
        movie_properties.remove('premiered')
        movie_properties.remove('uniqueid')
        movie_properties.append('year')

_upgradeproperties()

def _upgradeitem(mediaitem, mediatype):
    if mediatype == 'movie':
        mediaitem['premiered'] = '{0}-01-01'.format(mediaitem['year'])
        del mediaitem['year']

def get_movie_details(movie_id):
    json_request = get_base_json_request('VideoLibrary.GetMovieDetails')
    json_request['params']['movieid'] = movie_id
    json_request['params']['properties'] = movie_properties

    json_result = pykodi.execute_jsonrpc(json_request)

    if check_json_result(json_result, 'moviedetails', json_request):
        movie = json_result['result']['moviedetails']
        if _needupgrade('movie'):
            _upgradeitem(movie, 'movie')
        return movie

def get_movieset_details(movieset_id):
    json_request = get_base_json_request('VideoLibrary.GetMovieSetDetails')
    json_request['params']['setid'] = movieset_id
    json_request['params']['properties'] = movieset_properties
    json_request['params']['movies'] = {'properties': ['art', 'file']}

    json_result = pykodi.execute_jsonrpc(json_request)

    if check_json_result(json_result, 'setdetails', json_request):
        return json_result['result']['setdetails']

def get_tvshow_details(tvshow_id):
    json_request = get_base_json_request('VideoLibrary.GetTVShowDetails')
    json_request['params']['tvshowid'] = tvshow_id
    json_request['params']['properties'] = tvshow_properties

    json_result = pykodi.execute_jsonrpc(json_request)

    if check_json_result(json_result, 'tvshowdetails', json_request):
        return json_result['result']['tvshowdetails']

def get_episode_details(episode_id):
    json_request = get_base_json_request('VideoLibrary.GetEpisodeDetails')
    json_request['params']['episodeid'] = episode_id
    json_request['params']['properties'] = episode_properties

    json_result = pykodi.execute_jsonrpc(json_request)

    if check_json_result(json_result, 'episodedetails', json_request):
        return json_result['result']['episodedetails']

def get_movies():
    json_request = get_base_json_request('VideoLibrary.GetMovies')
    json_request['params']['sort'] = {'method': 'sorttitle', 'order': 'ascending'}
    json_request['params']['properties'] = movie_properties

    json_result = pykodi.execute_jsonrpc(json_request)
    if check_json_result(json_result, 'movies', json_request):
        if _needupgrade('movie'):
            for movie in json_result['result']['movies']:
                _upgradeitem(movie, 'movie')
        return json_result['result']['movies']
    else:
        return []

def get_moviesets():
    json_request = get_base_json_request('VideoLibrary.GetMovieSets')
    json_request['params']['properties'] = movieset_properties
    json_request['params']['sort'] = {'method': 'sorttitle', 'order': 'ascending'}

    json_result = pykodi.execute_jsonrpc(json_request)
    if check_json_result(json_result, 'sets', json_request):
        return json_result['result']['sets']
    else:
        return []

def get_tvshows(moreprops=False, includeprops=True):
    json_request = get_base_json_request('VideoLibrary.GetTVShows')
    if includeprops:
        json_request['params']['properties'] = more_tvshow_properties if moreprops else tvshow_properties
    json_request['params']['sort'] = {'method': 'sorttitle', 'order': 'ascending'}

    json_result = pykodi.execute_jsonrpc(json_request)
    if check_json_result(json_result, 'tvshows', json_request):
        return json_result['result']['tvshows']
    else:
        return []

def get_episodes(tvshow_id=None, limit=None):
    json_request = get_base_json_request('VideoLibrary.GetEpisodes')
    if tvshow_id:
        json_request['params']['tvshowid'] = tvshow_id
    json_request['params']['properties'] = episode_properties
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

def set_details(dbid, mediatype, **details):
    assert mediatype in typemap

    mapped = typemap[mediatype]
    json_request = get_base_json_request('VideoLibrary.Set{0}Details'.format(mapped[0]))
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
