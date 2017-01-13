import re

from devhelper import pykodi

from lib.libs import quickjson

import mediatypes
from utils import natural_sort

def is_known_mediatype(mediaitem):
    return any(x in mediaitem for x in ('episodeid', 'seasonid', 'tvshowid', 'movieid'))

def get_mediatype_id(mediaitem):
    if 'episodeid' in mediaitem: return mediatypes.EPISODE, mediaitem['episodeid']
    elif 'seasonid' in mediaitem: return mediatypes.SEASON, mediaitem['seasonid']
    elif 'tvshowid' in mediaitem: return mediatypes.TVSHOW, mediaitem['tvshowid']
    elif 'movieid' in mediaitem: return mediatypes.MOVIE, mediaitem['movieid']

def arttype_matches_base(arttype, basetype):
    return re.match(r'{0}\d*$'.format(basetype), arttype)

def iter_urls_for_arttype(art, arttype):
    for exact in sorted(art, key=natural_sort):
        if arttype_matches_base(exact, arttype):
            yield art[exact]

def iter_base_arttypes(art):
    usedtypes = set()
    for arttype in sorted(art.keys(), key=natural_sort):
        basetype = get_basetype(arttype)
        if basetype not in usedtypes:
            yield basetype
            usedtypes.add(basetype)

def iter_renumbered_artlist(urllist, basetype, original_arttypes):
    i = 0
    for url in urllist:
        yield format_arttype(basetype, i), url
        i += 1
    for arttype in sorted(original_arttypes, key=natural_sort):
        type_base, index = split_arttype(arttype)
        if type_base == basetype and index >= i:
            yield arttype, None

def get_basetype(arttype):
    return arttype.rstrip('0123456789')

def split_arttype(arttype):
    indexsearch = re.compile(r'([0-9]+)$').search(arttype)
    return get_basetype(arttype), int(indexsearch.group(1)) if indexsearch else 0

def format_arttype(basetype, index):
    return "{0}{1}".format(basetype, index if index else '')

def renumber_all_artwork(art):
    result = {}
    for basetype in iter_base_arttypes(art):
        urllist = [art[key] for key in sorted(art.keys(), key=natural_sort) if arttype_matches_base(key, basetype)]
        result.update(iter_renumbered_artlist(urllist, basetype, art.keys()))
    return result

def get_artwork_updates(originalart, newart):
    return dict((arttype, url) for arttype, url in newart.iteritems() if url != originalart.get(arttype))


def prepare_mediaitem(mediaitem):
    mediaitem['mediatype'], mediaitem['dbid'] = get_mediatype_id(mediaitem)

    mediaitem['art'] = dict((arttype.lower(), pykodi.unquoteimage(url)) for \
        arttype, url in mediaitem['art'].iteritems() if '.' not in arttype and not url.startswith('image://video'))


def update_art_in_library(mediatype, dbid, updatedart):
    if updatedart:
        if mediatype == mediatypes.TVSHOW:
            quickjson.set_tvshow_details(dbid, art=updatedart)
        elif mediatype == mediatypes.SEASON:
            quickjson.set_season_details(dbid, art=updatedart)
        elif mediatype == mediatypes.EPISODE:
            quickjson.set_episode_details(dbid, art=updatedart)
        elif mediatype == mediatypes.MOVIE:
            quickjson.set_movie_details(dbid, art=updatedart)
