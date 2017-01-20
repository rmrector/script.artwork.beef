from devhelper import pykodi
from devhelper.pykodi import log
from devhelper.quickjson import get_base_json_request, check_json_result

import mediatypes

# [0] method part
typemap = {mediatypes.MOVIE: ('Movie',),
    mediatypes.MOVIESET: ('MovieSet',),
    mediatypes.TVSHOW: ('TVShow',),
    mediatypes.EPISODE: ('Episode',),
    mediatypes.SEASON: ('Season',)}
tvshow_properties = ['art', 'imdbnumber', 'season', 'file']
more_tvshow_properties = ['art', 'imdbnumber', 'season', 'file', 'plot', 'year']
movie_properties = ['art', 'imdbnumber', 'file']
movieset_properties = ['art']
episode_properties = ['art', 'uniqueid', 'tvshowid', 'season', 'file']

def get_movie_details(movie_id):
    json_request = get_base_json_request('VideoLibrary.GetMovieDetails')
    json_request['params']['movieid'] = movie_id
    json_request['params']['properties'] = movie_properties

    json_result = pykodi.execute_jsonrpc(json_request)

    if check_json_result(json_result, 'moviedetails', json_request):
        return json_result['result']['moviedetails']

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
    json_request['params']['properties'] = movie_properties
    json_request['params']['sort'] = {'method': 'sorttitle', 'order': 'ascending'}

    json_result = pykodi.execute_jsonrpc(json_request)
    if check_json_result(json_result, 'movies', json_request):
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

def get_tvshows(moreprops=False):
    json_request = get_base_json_request('VideoLibrary.GetTVShows')
    json_request['params']['properties'] = more_tvshow_properties if moreprops else tvshow_properties
    json_request['params']['sort'] = {'method': 'sorttitle', 'order': 'ascending'}

    json_result = pykodi.execute_jsonrpc(json_request)
    if check_json_result(json_result, 'tvshows', json_request):
        return json_result['result']['tvshows']
    else:
        return []

def get_episodes(tvshow_id=None):
    json_request = get_base_json_request('VideoLibrary.GetEpisodes')
    if tvshow_id:
        json_request['params']['tvshowid'] = tvshow_id
    json_request['params']['properties'] = episode_properties
    json_request['params']['sort'] = {'method': 'dateadded', 'order': 'ascending'}

    json_result = pykodi.execute_jsonrpc(json_request)
    if check_json_result(json_result, 'episodes', json_request):
        return json_result['result']['episodes']
    else:
        return []

def get_seasons(tvshow_id=-1):
    json_request = get_base_json_request('VideoLibrary.GetSeasons')
    if tvshow_id != -1:
        json_request['params']['tvshowid'] = tvshow_id
    json_request['params']['properties'] = ['season', 'art']

    json_result = pykodi.execute_jsonrpc(json_request)

    if check_json_result(json_result, 'seasons', json_request):
        return json_result['result']['seasons']
    else:
        return []

def set_tvshow_details(tvshow_id, **tvshow_details):
    json_request = get_base_json_request('VideoLibrary.SetTVShowDetails')
    json_request['params'] = tvshow_details
    json_request['params']['tvshowid'] = tvshow_id

    json_result = pykodi.execute_jsonrpc(json_request)
    if not check_json_result(json_result, 'OK', json_request):
        log(json_result)

def set_season_details(season_id, **season_details):
    json_request = get_base_json_request('VideoLibrary.SetSeasonDetails')
    json_request['params'] = season_details
    json_request['params']['seasonid'] = season_id

    json_result = pykodi.execute_jsonrpc(json_request)
    if not check_json_result(json_result, 'OK', json_request):
        log(json_result)

def set_episode_details(episode_id, **episode_details):
    json_request = get_base_json_request('VideoLibrary.SetEpisodeDetails')
    json_request['params'] = episode_details
    json_request['params']['episodeid'] = episode_id

    json_result = pykodi.execute_jsonrpc(json_request)
    if not check_json_result(json_result, 'OK', json_request):
        log(json_result)

def set_movie_details(movie_id, **movie_details):
    json_request = get_base_json_request('VideoLibrary.SetMovieDetails')
    json_request['params'] = movie_details
    json_request['params']['movieid'] = movie_id

    json_result = pykodi.execute_jsonrpc(json_request)
    if not check_json_result(json_result, 'OK', json_request):
        log(json_result)

def set_movieset_details(set_id, **movieset_details):
    json_request = get_base_json_request('VideoLibrary.SetMovieSetDetails')
    json_request['params'] = movieset_details
    json_request['params']['setid'] = set_id

    json_result = pykodi.execute_jsonrpc(json_request)
    if not check_json_result(json_result, 'OK', json_request):
        log(json_result)
