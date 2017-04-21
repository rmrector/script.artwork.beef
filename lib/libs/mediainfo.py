import re

from lib.libs import mediatypes
from lib.libs.utils import natural_sort
from lib.libs.pykodi import unquoteimage
from lib.libs import quickjson

# get_mediatype_id must evaluate these in order, as episodes have tvshowid
idmap = (('episodeid', mediatypes.EPISODE),
    ('seasonid', mediatypes.SEASON),
    ('tvshowid', mediatypes.TVSHOW),
    ('movieid', mediatypes.MOVIE),
    ('setid', mediatypes.MOVIESET))

def is_known_mediatype(mediaitem):
    return any(x[0] in mediaitem for x in idmap)

def get_mediatype_id(mediaitem):
    return next((value, mediaitem[key]) for key, value in idmap if key in mediaitem)

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

def iter_missing_arttypes(mediatype, seasons, existingarttypes):
    fullartinfo = mediatypes.artinfo[mediatype]
    for arttype, artinfo in fullartinfo.iteritems():
        if not artinfo['autolimit']:
            continue
        elif artinfo['autolimit'] == 1:
            if arttype not in existingarttypes:
                yield arttype
        else:
            artcount = sum(1 for art in existingarttypes if arttype_matches_base(art, arttype))
            if artcount < artinfo['autolimit']:
                yield arttype

    if mediatype == mediatypes.TVSHOW:
        seasonartinfo = mediatypes.artinfo.get(mediatypes.SEASON)
        for season in seasons.iteritems():
            for arttype, artinfo in seasonartinfo.iteritems():
                arttype = '%s.%s.%s' % (mediatypes.SEASON, season[0], arttype)
                if not artinfo['autolimit']:
                    continue
                elif artinfo['autolimit'] == 1:
                    if arttype not in existingarttypes:
                        yield arttype
                else:
                    artcount = sum(1 for art in existingarttypes if arttype_matches_base(art, arttype))
                    if artcount < artinfo['autolimit']:
                        yield arttype

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

    mediaitem['art'] = dict((arttype.lower(), unquoteimage(url)) for
        arttype, url in mediaitem['art'].iteritems() if '.' not in arttype)


def update_art_in_library(mediatype, dbid, updatedart):
    if updatedart:
        quickjson.set_details(dbid, mediatype, art=updatedart)

def get_media_source(mediapath):
    if not mediapath:
        return 'unknown'
    mediapath = mediapath.lower()
    if re.search(r'\b3d\b', mediapath):
        return '3d'
    if re.search(r'blu-?ray|b[rd]-?rip', mediapath) or mediapath.endswith('.bdmv'):
        return 'bluray'
    if re.search(r'\bdvd', mediapath) or mediapath.endswith('.ifo'):
        return 'dvd'
    return 'unknown'
