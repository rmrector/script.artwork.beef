import re

from devhelper import pykodi

import mediatypes
import quickjson
from utils import natural_sort

# get_mediatype_id must evaluate these in order, as episodes have tvshowid
idmap = (('episodeid', mediatypes.EPISODE),
    ('seasonid', mediatypes.SEASON),
    ('tvshowid', mediatypes.TVSHOW),
    ('movieid', mediatypes.MOVIE),
    ('setid', mediatypes.MOVIESET))
idkeys = [x[0] for x in idmap]

typemap = {mediatypes.EPISODE: quickjson.set_episode_details,
    mediatypes.SEASON: quickjson.set_season_details,
    mediatypes.TVSHOW: quickjson.set_tvshow_details,
    mediatypes.MOVIE: quickjson.set_movie_details,
    mediatypes.MOVIESET: quickjson.set_movieset_details}

def is_known_mediatype(mediaitem):
    return any(x in mediaitem for x in idkeys)

def get_mediatype_id(mediaitem):
    return next(((value, mediaitem[key]) for key, value in idmap if key in mediaitem))

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

    mediaitem['art'] = dict((arttype.lower(), pykodi.unquoteimage(url)) for
        arttype, url in mediaitem['art'].iteritems() if '.' not in arttype and not url.startswith('image://video'))


def update_art_in_library(mediatype, dbid, updatedart):
    if updatedart:
        if mediatype in typemap:
            typemap[mediatype](dbid, art=updatedart)
