import re
import xbmc

from lib.libs import mediatypes, pykodi, quickjson
from lib.libs.addonsettings import settings
from lib.libs.pykodi import log, unquoteimage, localize as L
from lib.libs.utils import natural_sort, get_pathsep, iter_possible_cleannames

CANT_FIND_MOVIESET = 32032
CANT_FIND_MUSICVIDEO = 32033

# get_mediatype_id must evaluate these in order, as episodes have tvshowid
idmap = (('episodeid', mediatypes.EPISODE),
    ('seasonid', mediatypes.SEASON),
    ('tvshowid', mediatypes.TVSHOW),
    ('movieid', mediatypes.MOVIE),
    ('setid', mediatypes.MOVIESET),
    ('musicvideoid', mediatypes.MUSICVIDEO))

class MediaItem(object):
    def __init__(self, jsondata):
        self.label = jsondata['label']
        self.file = jsondata.get('file')
        self.premiered = jsondata.get('premiered')
        self.sourcemedia = _get_sourcemedia(self.file)
        self.mediatype, self.dbid = get_mediatype_id(jsondata)
        self.skip_artwork = []

        self.art = get_own_artwork(jsondata)
        self.uniqueids = _get_uniqueids(jsondata, self.mediatype)
        if self.mediatype == mediatypes.EPISODE:
            self.tvshowid = jsondata['tvshowid']
            self.showtitle = jsondata['showtitle']
            self.season = jsondata['season']
            self.episode = jsondata['episode']
        elif self.mediatype == mediatypes.TVSHOW:
            self.season = jsondata['season']
        elif self.mediatype == mediatypes.MOVIESET:
            self.movies = jsondata.get('movies', [])
            if settings.setartwork_fromcentral and settings.setartwork_dir:
                # TODO: What about finding artwork in both setartwork_dir and parent dir?
                #  parent dir currently overrides setartwork_dir if it is found
                self.file = settings.setartwork_dir + self.label + '.ext'
        elif self.mediatype == mediatypes.MUSICVIDEO:
            self.label = jsondata['artist'][0] + ' - ' + jsondata['title']

        self.seasons = None
        self.availableart = {}
        self.missingart = [] # or build this dynamically?
        self.selectedart = {}
        self.forcedart = {}
        self.updatedart = []
        self.error = None

def is_known_mediatype(jsondata):
    return any(x[0] in jsondata for x in idmap)

def get_mediatype_id(jsondata):
    return next((value, jsondata[key]) for key, value in idmap if key in jsondata)

def get_own_artwork(jsondata):
    return dict((arttype.lower(), unquoteimage(url)) for arttype, url
        in jsondata['art'].iteritems() if '.' not in arttype)

def has_generated_thumbnail(jsondata):
    return jsondata['art'].get('thumb', '').startswith('image://video@')

def arttype_matches_base(arttype, basetype):
    return re.match(r'{0}\d*$'.format(basetype), arttype)

def iter_urls_for_arttype(art, arttype):
    for exact in sorted(art, key=natural_sort):
        if arttype_matches_base(exact, arttype):
            yield art[exact]

def iter_base_arttypes(artkeys):
    usedtypes = set()
    for arttype in sorted(artkeys, key=natural_sort):
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

def iter_missing_arttypes(mediaitem, existingarttypes):
    for arttype, artinfo in mediatypes.artinfo[mediaitem.mediatype].iteritems():
        if arttype in mediaitem.skip_artwork or not artinfo['autolimit']:
            continue
        elif artinfo['autolimit'] == 1:
            if arttype not in existingarttypes:
                yield arttype
        else:
            artcount = sum(1 for art in existingarttypes if arttype_matches_base(art, arttype))
            if artcount < artinfo['autolimit']:
                yield arttype

    if mediaitem.mediatype == mediatypes.TVSHOW:
        seasonartinfo = mediatypes.artinfo.get(mediatypes.SEASON)
        for season in mediaitem.seasons.iteritems():
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
    for basetype in iter_base_arttypes(art.keys()):
        urllist = [art[key] for key in sorted(art.keys(), key=natural_sort) if arttype_matches_base(key, basetype)]
        result.update(iter_renumbered_artlist(urllist, basetype, art.keys()))
    return result

def update_art_in_library(mediatype, dbid, updatedart):
    if updatedart:
        quickjson.set_item_details(dbid, mediatype, art=updatedart)

def add_additional_iteminfo(mediaitem, processed, search):
    '''Get more data from the Kodi library, processed items, and look up web service IDs.'''
    if mediaitem.mediatype in search:
        search = search[mediaitem.mediatype]
    if mediaitem.mediatype == mediatypes.TVSHOW:
        # TODO: Split seasons out to separate items
        if not mediaitem.seasons:
            mediaitem.seasons, seasonart = _get_seasons_artwork(quickjson.get_seasons(mediaitem.dbid))
            mediaitem.art.update(seasonart)
        if settings.default_tvidsource == 'tmdb' and 'tvdb' not in mediaitem.uniqueids:
            # TODO: Set to the Kodi library if found
            resultids = search.get_more_uniqueids(mediaitem.uniqueids, mediaitem.mediatype)
            if 'tvdb' in resultids:
                mediaitem.uniqueids['tvdb'] = resultids['tvdb']
    elif mediaitem.mediatype == mediatypes.EPISODE:
        if settings.default_tvidsource == 'tmdb':
            # TheMovieDB scraper sets episode IDs that can't be used in the API, but seriesID/season/episode works
            tvshowids = quickjson.get_item_details(mediaitem.tvshowid, mediatypes.TVSHOW)['uniqueid']
            tvshowid = tvshowids.get('tmdb', tvshowids.get('unknown'))
            if tvshowid:
                mediaitem.uniqueids['tmdb_se'] = '{0}/{1}/{2}'.format(tvshowid, mediaitem.season, mediaitem.episode)
    elif mediaitem.mediatype == mediatypes.MOVIESET:
        if not mediaitem.uniqueids.get('tmdb'):
            uniqueid = processed.get_data(mediaitem.dbid, mediaitem.mediatype, mediaitem.label)
            if not uniqueid and not settings.only_filesystem:
                searchresults = search.search(mediaitem.label, mediaitem.mediatype)
                if searchresults:
                    for result in searchresults:
                        if result['label'] == mediaitem.label:
                            uniqueid = result['uniqueids']['tmdb']
                            break
                    uniqueid = searchresults[0]['uniqueids']['tmdb']
                if uniqueid:
                    processed.set_data(mediaitem.dbid, mediatypes.MOVIESET, mediaitem.label, uniqueid)
                else:
                    processed.set_data(mediaitem.dbid, mediatypes.MOVIESET, mediaitem.label, None)
                    mediaitem.error = L(CANT_FIND_MOVIESET)
                    log("Could not find set '{0}' on TheMovieDB".format(mediaitem.label), xbmc.LOGNOTICE)

            mediaitem.uniqueids['tmdb'] = uniqueid
        if not processed.exists(mediaitem.dbid, mediaitem.mediatype, mediaitem.label):
            _remove_set_movieposters(mediaitem)
        if settings.setartwork_fromparent:
            _identify_parent_movieset(mediaitem)
    elif mediaitem.mediatype == mediatypes.MUSICVIDEO:
        if not mediaitem.uniqueids.get('mbid_track') or not mediaitem.uniqueids.get('mbid_album') \
                or not mediaitem.uniqueids.get('mbid_artist'):
            newdata = processed.get_data(mediaitem.dbid, mediaitem.mediatype, mediaitem.label)
            if newdata:
                mb_t, mb_al, mb_ar = newdata.split('/')
                mediaitem.uniqueids = {'mbid_track': mb_t, 'mbid_album': mb_al, 'mbid_artist': mb_ar}
            elif not settings.only_filesystem:
                results = search.search(mediaitem.label, mediatypes.MUSICVIDEO)
                if results and results[0].get('uniqueids'):
                    mediaitem.uniqueids = uq = results[0]['uniqueids']
                    processed.set_data(mediaitem.dbid, mediatypes.MUSICVIDEO, mediaitem.label,
                        uq['mbid_track'] + '/' + uq['mbid_album'] + '/' + uq['mbid_artist'])
                else:
                    processed.set_data(mediaitem.dbid, mediatypes.MUSICVIDEO, mediaitem.label, None)
                    mediaitem.error = L(CANT_FIND_MUSICVIDEO)
                    log("Could not find music video '{0}' on TheAudioDB".format(mediaitem.label), xbmc.LOGNOTICE)

def _get_seasons_artwork(seasons):
    resultseasons = {}
    resultart = {}
    for season in seasons:
        resultseasons[season['season']] = season['seasonid']
        for arttype, url in season['art'].iteritems():
            arttype = arttype.lower()
            if not arttype.startswith(('tvshow.', 'season.')):
                resultart['%s.%s.%s' % (mediatypes.SEASON, season['season'], arttype)] = pykodi.unquoteimage(url)
    return resultseasons, resultart

def _remove_set_movieposters(mediaitem):
    # Remove poster/fanart Kodi automatically sets from a movie
    if not set(key for key in mediaitem.art).difference(('poster', 'fanart')):
        if 'poster' in mediaitem.art:
            del mediaitem.art['poster']
        if 'fanart' in mediaitem.art:
            del mediaitem.art['fanart']

def _identify_parent_movieset(mediaitem):
    # Identify set folder among movie parent dirs
    if not mediaitem.movies:
        mediaitem.movies = quickjson.get_item_details(mediaitem.dbid, mediatypes.MOVIESET)['movies']
    for cleanlabel in iter_possible_cleannames(mediaitem.label):
        for movie in mediaitem.movies:
            pathsep = get_pathsep(movie['file'])
            setmatch = pathsep + cleanlabel + pathsep
            if setmatch in movie['file']:
                result = movie['file'].split(setmatch)[0] + setmatch
                mediaitem.file = result if not mediaitem.file else (result, mediaitem.file)
                return

def _get_uniqueids(jsondata, mediatype):
    uniqueids = jsondata.get('uniqueid', {})
    if '/' in uniqueids.get('tvdb', ''):
        # PlexKodiConnect sets these
        uniqueids['tvdb_se'] = uniqueids['tvdb']
        del uniqueids['tvdb']
    if 'unknown' in uniqueids:
        uniqueid = uniqueids['unknown']
        if uniqueid.startswith('tt') and 'imdb' not in uniqueids:
            # TODO: If changed, set it in Kodi's library
            uniqueids['imdb'] = uniqueid
            del uniqueids['unknown']
        elif mediatype in (mediatypes.TVSHOW, mediatypes.EPISODE) and settings.default_tvidsource not in uniqueids:
            # but maybe not this guy
            uniqueids[settings.default_tvidsource] = uniqueid
            del uniqueids['unknown']

    return uniqueids

def _get_sourcemedia(mediapath):
    if not mediapath:
        return 'unknown'
    mediapath = mediapath.lower()
    if re.search(r'\b3d\b', mediapath):
        return '3d'
    # TODO: UHD?
    if re.search(r'blu-?ray|b[rd]-?rip', mediapath) or mediapath.endswith('.bdmv'):
        return 'bluray'
    if re.search(r'\bdvd', mediapath) or mediapath.endswith('.ifo'):
        return 'dvd'
    return 'unknown'
