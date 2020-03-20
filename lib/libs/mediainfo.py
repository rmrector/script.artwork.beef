import os
import re
import xbmc
import xbmcvfs
from functools import wraps

from lib.libs import mediatypes, pykodi, quickjson, utils
from lib.libs.addonsettings import settings
from lib.libs.mediatypes import _split_arttype as split_arttype
from lib.libs.pykodi import log, unquoteimage, unquotearchive, localize as L

CANT_FIND_MOVIESET = 32032
CANT_FIND_MUSICVIDEO = 32033

# get_mediatype_id must evaluate these in order
idmap = (('episodeid', mediatypes.EPISODE),
    ('seasonid', mediatypes.SEASON),
    ('tvshowid', mediatypes.TVSHOW),
    ('movieid', mediatypes.MOVIE),
    ('setid', mediatypes.MOVIESET),
    ('musicvideoid', mediatypes.MUSICVIDEO),
    ('songid', mediatypes.SONG),
    ('albumid', mediatypes.ALBUM),
    ('artistid', mediatypes.ARTIST))

class MediaItem(object):
    def __init__(self, jsondata):
        self.label = jsondata['label']
        self.file = unquotearchive(jsondata.get('file'))
        self.premiered = jsondata.get('premiered')
        self.sourcemedia = _get_sourcemedia(self.file)
        self.mediatype, self.dbid = get_mediatype_id(jsondata)
        self.skip_artwork = []

        self.art = get_own_artwork(jsondata)
        self.uniqueids = _get_uniqueids(jsondata, self.mediatype)
        if self.mediatype in (mediatypes.EPISODE, mediatypes.SEASON):
            self.tvshowid = jsondata['tvshowid']
            self.showtitle = jsondata['showtitle']
            self.season = jsondata['season']
            self.label = self.showtitle + ' - ' + self.label
        if self.mediatype == mediatypes.EPISODE:
            self.episode = jsondata['episode']
        elif self.mediatype == mediatypes.TVSHOW:
            self.season = jsondata['season']
        elif self.mediatype == mediatypes.MOVIESET:
            self.movies = jsondata.get('movies', [])
            if self.movies:
                add_movieset_movies(self)
            if mediatypes.central_directories[mediatypes.MOVIESET]:
                self.file = mediatypes.central_directories[mediatypes.MOVIESET] \
                    + utils.path_component(self.label) + '.ext'
        elif self.mediatype == mediatypes.MUSICVIDEO:
            self.label = build_music_label(jsondata)
        elif self.mediatype in mediatypes.audiotypes:
            if self.mediatype in (mediatypes.ALBUM, mediatypes.SONG):
                self.albumid = jsondata['albumid']
                self.label = build_music_label(jsondata)
            self.artistid = None if self.mediatype == mediatypes.ARTIST \
                else jsondata['albumartistid'][0] if jsondata.get('albumartistid') \
                else jsondata['artistid'][0] if jsondata.get('artistid') \
                else None
            self.artist = jsondata['label'] if self.mediatype == mediatypes.ARTIST \
                else jsondata['albumartist'][0] if jsondata.get('albumartist') \
                else jsondata['artist'][0] if jsondata.get('artist') \
                else None
            self.album = jsondata['label'] if self.mediatype == mediatypes.ALBUM \
                else jsondata['album'] if self.mediatype == mediatypes.SONG \
                else None
            if self.mediatype == mediatypes.ALBUM:
                self.discfolders = {}

        self.seasons = None
        self.availableart = {}
        self.missingart = [] # or build this dynamically?
        self.selectedart = {}
        self.forcedart = {}
        self.updatedart = []
        self.downloadedart = {}
        self.error = None
        self.missingid = False
        self.borked_filename = self.file and '\xef\xbf\xbd' in self.file

def build_music_label(jsondata):
    return jsondata['artist'][0] + ' - ' + jsondata['title'] if jsondata.get('artist') else jsondata['title']

def is_known_mediatype(jsondata):
    return any(x[0] in jsondata for x in idmap)

def get_mediatype_id(jsondata):
    return next((value, jsondata[key]) for key, value in idmap if key in jsondata)

def get_own_artwork(jsondata):
    return dict((arttype.lower(), unquoteimage(url)) for arttype, url
        in jsondata['art'].iteritems() if '.' not in arttype)

def has_generated_thumbnail(jsondata):
    return jsondata['art'].get('thumb', '').startswith(pykodi.thumbnailimages)

def has_art_todownload(artmap, mediatype):
    return next((True for arttype, url in artmap.items()
        if url and url.startswith('http') and mediatypes.downloadartwork(mediatype, arttype)), False)

def arttype_matches_base(arttype, basetype):
    return re.match(r'{0}\d*$'.format(basetype), arttype)

def iter_urls_for_arttype(art, arttype):
    for exact in sorted(art, key=utils.natural_sort):
        if arttype_matches_base(exact, arttype):
            yield art[exact]

def iter_base_arttypes(artkeys):
    usedtypes = set()
    for arttype in sorted(artkeys, key=utils.natural_sort):
        basetype = get_basetype(arttype)
        if basetype not in usedtypes:
            yield basetype
            usedtypes.add(basetype)

def fill_multiart(original_art, basetype, artchanges=((), ())):
    result = dict(original_art)
    if artchanges[1]:
        result.update((atype, None) for atype, url in result.items()
            if url in artchanges[1] and arttype_matches_base(atype, basetype))
    canmove = lambda atype, url: arttype_matches_base(atype, basetype) and url and url.startswith(pykodi.remoteimages)
    toadd = [url for atype, url in result.items() if canmove(atype, url)]
    toadd.extend(artchanges[0])
    result.update((atype, None) for atype, url in result.items() if canmove(atype, url))
    if toadd:
        have = [split_arttype(atype)[1] for atype, url in result.items()
            if url and arttype_matches_base(atype, basetype)]
        idx = -1
        while toadd:
            idx += 1
            if idx in have:
                continue
            result[basetype + (str(idx) if idx else '')] = toadd.pop(0)
    return result

def item_has_generated_thumbnail(mediaitem):
    return mediaitem.art.get('thumb', '').startswith(pykodi.thumbnailimages)

def iter_missing_arttypes(mediaitem, existingart):
    fromtypes = [key for key, url in existingart.iteritems() if url]
    for arttype, artinfo in mediatypes.artinfo[mediaitem.mediatype].iteritems():
        if arttype in mediaitem.skip_artwork or not artinfo['autolimit']:
            continue
        elif artinfo['autolimit'] == 1:
            if arttype not in fromtypes:
                yield arttype
        else:
            if _has_localart(arttype, existingart, fromtypes):
                continue # Can't easily tell if existing art matches new URLs, so don't add new on updates
            artcount = sum(1 for art in fromtypes if arttype_matches_base(art, arttype))
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
                    if arttype not in fromtypes:
                        yield arttype
                else:
                    artcount = sum(1 for art in fromtypes if arttype_matches_base(art, arttype))
                    if artcount < artinfo['autolimit']:
                        yield arttype

    for arttype in mediatypes.othertypes[mediaitem.mediatype]:
        if arttype not in mediaitem.skip_artwork and arttype not in fromtypes:
            yield arttype

def _has_localart(arttype, existingart, fromtypes):
    for art in fromtypes:
        if not arttype_matches_base(art, arttype):
            continue
        if art in existingart and not existingart[art].startswith(pykodi.notimagefiles):
            return True
    return False

def keep_arttype(mediatype, arttype, arturl):
    mediatype, arttype = mediatypes.hack_mediaarttype(mediatype, arttype)
    if arttype == 'thumb' and mediatypes.generatethumb(mediatype) \
            and arturl.startswith(pykodi.thumbnailimages):
        return True
    return arttype in mediatypes.iter_every_arttype(mediatype)

def get_basetype(arttype):
    return arttype.rstrip('0123456789')

def format_arttype(basetype, index):
    return "{0}{1}".format(basetype, index if index else '')

def update_art_in_library(mediatype, dbid, updatedart):
    if updatedart:
        quickjson.set_item_details(dbid, mediatype, art=updatedart)

def remove_local_from_texturecache(urls, include_generated=False):
    exclude = pykodi.remoteimages if include_generated else pykodi.notimagefiles
    for url in urls:
        if url and not url.startswith(exclude):
            quickjson.remove_texture_byurl(url)

def add_additional_iteminfo(mediaitem, processed, search=None):
    '''Get more data from the Kodi library, processed items, and look up web service IDs.'''
    if search and mediaitem.mediatype in search:
        search = search[mediaitem.mediatype]
    if mediaitem.mediatype == mediatypes.TVSHOW:
        # TODO: Split seasons out to separate items
        if not mediaitem.seasons:
            mediaitem.seasons, seasonart = _get_seasons_artwork(quickjson.get_seasons(mediaitem.dbid))
            mediaitem.art.update(seasonart)
        if search and settings.default_tvidsource == 'tmdb' and 'tvdb' not in mediaitem.uniqueids:
            # TODO: Set to the Kodi library if found
            resultids = search.get_more_uniqueids(mediaitem.uniqueids, mediaitem.mediatype)
            if 'tvdb' in resultids:
                mediaitem.uniqueids['tvdb'] = resultids['tvdb']
    elif mediaitem.mediatype == mediatypes.SEASON:
        tvshow = quickjson.get_item_details(mediaitem.tvshowid, mediatypes.TVSHOW)
        mediaitem.file = tvshow['file']
    elif mediaitem.mediatype == mediatypes.EPISODE:
        if settings.default_tvidsource == 'tmdb':
            # TheMovieDB scraper sets episode IDs that can't be used in the API, but seriesID/season/episode works
            uniqueids = quickjson.get_item_details(mediaitem.tvshowid, mediatypes.TVSHOW)['uniqueid']
            uniqueid = uniqueids.get('tmdb', uniqueids.get('unknown'))
            if uniqueid:
                mediaitem.uniqueids['tmdbse'] = '{0}/{1}/{2}'.format(uniqueid, mediaitem.season, mediaitem.episode)
    elif mediaitem.mediatype == mediatypes.MOVIESET:
        if not mediaitem.uniqueids.get('tmdb'):
            uniqueid = processed.get_data(mediaitem.dbid, mediaitem.mediatype, mediaitem.label)
            if search and not uniqueid and not mediatypes.only_filesystem(mediaitem.mediatype):
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
        if settings.setartwork_fromparent and not mediaitem.file:
            _identify_parent_movieset(mediaitem)
    elif mediaitem.mediatype == mediatypes.MUSICVIDEO:
        if not mediaitem.uniqueids.get('mbtrack') or not mediaitem.uniqueids.get('mbgroup') \
                or not mediaitem.uniqueids.get('mbartist'):
            newdata = processed.get_data(mediaitem.dbid, mediaitem.mediatype, mediaitem.label)
            if newdata:
                mb_t, mb_al, mb_ar = newdata.split('/')
                mediaitem.uniqueids = {'mbtrack': mb_t, 'mbgroup': mb_al, 'mbartist': mb_ar}
            elif search and not mediatypes.only_filesystem(mediaitem.mediatype):
                results = search.search(mediaitem.label, mediatypes.MUSICVIDEO)
                uq = results and results[0].get('uniqueids')
                if uq and uq.get('mbtrack') and uq.get('mbgroup') and uq.get('mbartist'):
                    mediaitem.uniqueids = uq
                    processed.set_data(mediaitem.dbid, mediatypes.MUSICVIDEO, mediaitem.label,
                        uq['mbtrack'] + '/' + uq['mbgroup'] + '/' + uq['mbartist'])
                else:
                    processed.set_data(mediaitem.dbid, mediatypes.MUSICVIDEO, mediaitem.label, None)
                    mediaitem.error = L(CANT_FIND_MUSICVIDEO)
                    log("Could not find music video '{0}' on TheAudioDB".format(mediaitem.label), xbmc.LOGNOTICE)
    elif mediaitem.mediatype == mediatypes.ALBUM:
        folders = _identify_album_folders(mediaitem)
        if folders:
            mediaitem.file, mediaitem.discfolders = folders

def add_movieset_movies(mediaitem):
    if not mediaitem.movies:
        mediaitem.movies = quickjson.get_item_details(mediaitem.dbid, mediatypes.MOVIESET)['movies']
    for movie in mediaitem.movies:
        movie['art'] = get_own_artwork(movie)

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
    # Remove artwork Kodi automatically sets from a movie
    add_movieset_movies(mediaitem)
    if any(movie['art'] == mediaitem.art for movie in mediaitem.movies):
        mediaitem.art = {}

def _identify_parent_movieset(mediaitem):
    # Identify set folder among movie parent dirs
    add_movieset_movies(mediaitem)
    for cleanlabel in utils.iter_possible_cleannames(mediaitem.label):
        for movie in mediaitem.movies:
            pathsep = utils.get_pathsep(movie['file'])
            setmatch = pathsep + cleanlabel + pathsep
            if setmatch in movie['file']:
                result = movie['file'].split(setmatch)[0] + setmatch
                mediaitem.file = result
                return

def _identify_album_folders(mediaitem):
    songs = get_cached_songs(mediaitem.albumid)
    folders = set(os.path.dirname(song['file']) for song in songs)
    if len(folders) == 1: # all songs only in one folder
        folder = folders.pop()
        if not _shared_albumfolder(folder):
            return folder + utils.get_pathsep(folder), {}
    elif len(folders) > 1: # split to multiple folders
        discs = {}
        for folder in folders:
            if _shared_albumfolder(folder):
                return
            discnum = next(s['disc'] for s in songs if os.path.dirname(s['file']) == folder)
            if discnum:
                discs[discnum] = folder + utils.get_pathsep(folder)
        commonpath = os.path.dirname(os.path.commonprefix(folders))
        if commonpath:
            commonpath += utils.get_pathsep(commonpath)
        if commonpath or discs:
            return commonpath, discs

def _shared_albumfolder(folder):
    songs = get_cached_songs_bypath(folder + utils.get_pathsep(folder))
    albums = set(song['albumid'] for song in songs)
    return len(albums) > 1

def _get_uniqueids(jsondata, mediatype):
    uniqueids = {}
    for uid in jsondata.get('uniqueid', {}):
        if jsondata['uniqueid'][uid]:
            uniqueids[uid] = jsondata['uniqueid'][uid]
    if '/' in uniqueids.get('tvdb', ''):
        # PlexKodiConnect sets these
        uniqueids['tvdbse'] = uniqueids['tvdb']
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
    if jsondata.get('musicbrainzartistid'):
        uniqueids['mbartist'] = jsondata['musicbrainzartistid'][0]
    elif jsondata.get('musicbrainzalbumartistid'):
        uniqueids['mbartist'] = jsondata['musicbrainzalbumartistid'][0]
    if jsondata.get('musicbrainzalbumid'):
        uniqueids['mbalbum'] = jsondata['musicbrainzalbumid']
    if jsondata.get('musicbrainzreleasegroupid'):
        uniqueids['mbgroup'] = jsondata['musicbrainzreleasegroupid']
    if jsondata.get('musicbrainztrackid'):
        uniqueids['mbtrack'] = jsondata['musicbrainztrackid']
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

# REVIEW: there may be other protocols that just can't be written to
#  xbmcvfs.mkdirs only supports local drives, SMB, and NFS
blacklisted_protocols = ('plugin', 'http')
# whitelist startswith would be something like ['smb://', 'nfs://', '/', r'[A-Z]:\\']

def can_saveartwork(mediaitem):
    if not (settings.albumartwithmediafiles and mediaitem.file \
            and mediaitem.mediatype in (mediatypes.ALBUM, mediatypes.SONG)):
        if find_central_infodir(mediaitem):
            return True
    if not mediaitem.file:
        return False
    path = utils.get_movie_path_list(mediaitem.file)[0] \
        if mediaitem.mediatype == mediatypes.MOVIE else mediaitem.file
    if path.startswith(blacklisted_protocols) or mediaitem.borked_filename:
        return False
    return True

def build_artwork_basepath(mediaitem, arttype):
    if settings.albumartwithmediafiles and mediaitem.file \
            and mediaitem.mediatype in (mediatypes.ALBUM, mediatypes.SONG):
        path = os.path.splitext(mediaitem.file)[0]
    else:
        path = find_central_infodir(mediaitem)
    if not path:
        if not mediaitem.file:
            return ''
        path = utils.get_movie_path_list(mediaitem.file)[0] \
            if mediaitem.mediatype == mediatypes.MOVIE else mediaitem.file
        if path.startswith(blacklisted_protocols):
            return ''
        path = os.path.splitext(path)[0]

    sep = utils.get_pathsep(path)
    path, basename = os.path.split(path)
    path += sep
    use_basefilename = mediaitem.mediatype in (mediatypes.EPISODE, mediatypes.SONG) \
        or mediaitem.mediatype == mediatypes.MOVIE and settings.savewith_basefilename \
        or mediaitem.mediatype == mediatypes.MUSICVIDEO and settings.savewith_basefilename_mvids \
        or mediaitem.mediatype == mediatypes.MOVIESET and basename and not settings.setartwork_subdirs
    if settings.identify_alternatives and _saveextrafanart(mediaitem.mediatype, arttype):
        path += 'extrafanart' + sep
    elif use_basefilename:
        path += basename + '-'
    def snum(num):
        return '-specials' if num == 0 else '-all' if num == -1 else '{0:02d}'.format(num)
    if mediaitem.mediatype == mediatypes.SEASON:
        path += 'season{0}-{1}'.format(snum(mediaitem.season), arttype)
    elif arttype.startswith('season.'):
        _, num, sarttype = arttype.split('.')
        path += 'season{0}-{1}'.format(snum(int(num)), sarttype)
    else:
        path += arttype
    return path

def _saveextrafanart(mediatype, arttype):
    if not arttype_matches_base(arttype, 'fanart') or not split_arttype(arttype)[1]:
        return False
    if not mediatypes.downloadartwork(mediatype, 'fanart1'):
        return False
    return settings.save_extrafanart and mediatype in (mediatypes.MOVIE, mediatypes.TVSHOW) \
        or settings.save_extrafanart_mvids and mediatype == mediatypes.MUSICVIDEO

def find_central_infodir(mediaitem):
    fromtv = mediaitem.mediatype in (mediatypes.SEASON, mediatypes.EPISODE)
    fromartist = mediaitem.mediatype in mediatypes.audiotypes
    fromalbum = mediaitem.mediatype in (mediatypes.ALBUM, mediatypes.SONG)
    cdtype = mediatypes.TVSHOW if fromtv else mediatypes.ARTIST if fromartist else mediaitem.mediatype
    basedir = mediatypes.central_directories.get(cdtype)
    if not basedir:
        return None
    slug1 = _get_uniqueslug(mediaitem, mediatypes.ARTIST) if fromartist else None
    slug2 = _get_uniqueslug(mediaitem, mediatypes.ALBUM) if fromalbum else None
    title1 = mediaitem.showtitle if fromtv \
        else mediaitem.artist if fromartist else mediaitem.label
    title2 = mediaitem.album if fromalbum \
        else mediaitem.label if mediaitem.mediatype == mediatypes.EPISODE \
        else None
    title3 = mediaitem.label if mediaitem.mediatype == mediatypes.SONG else None
    sep = utils.get_pathsep(basedir)
    mediayear = mediaitem.year if mediaitem.mediatype == mediatypes.MOVIE else None

    single_dir = mediaitem.mediatype == mediatypes.MOVIESET and not settings.setartwork_subdirs
    thisdir = _find_existing(basedir, title1, slug1, mediayear, single_dir)
    if not thisdir:
        if mediaitem.mediatype == mediatypes.MOVIE:
            title1 = '{0} ({1})'.format(mediaitem.label, mediaitem.year)
        thisdir = utils.build_cleanest_name(title1, slug1)
    result = basedir + thisdir
    if not single_dir:
        result += sep
    if not title2:
        return result
    usefiles = mediaitem.mediatype == mediatypes.EPISODE
    thisdir = _find_existing(result, title2, slug2, files=usefiles)
    if not thisdir:
        thisdir = utils.build_cleanest_name(title2, slug2)
    result += thisdir
    if not usefiles:
        result += sep
    if not title3:
        return result
    final = _find_existing(result, title3, files=True)
    if not final:
        final = utils.build_cleanest_name(title3)
    result += final
    return result

def _find_existing(basedir, name, uniqueslug=None, mediayear=None, files=False):
    for item in get_cached_listdir(basedir)[1 if files else 0]:
        cleantitle, diryear = xbmc.getCleanMovieTitle(item) if mediayear else (item, '')
        if diryear and int(diryear) != mediayear:
            continue
        if files:
            item = item.rsplit('-', 1)[0]
        for title in utils.iter_possible_cleannames(name, uniqueslug):
            if title in (cleantitle, item):
                return item
    return None

def _get_uniqueslug(mediaitem, slug_mediatype):
    if slug_mediatype == mediatypes.ARTIST and mediaitem.artist is not None:
        if len(get_cached_artists(mediaitem.artist)) > 1:
            return mediaitem.uniqueids.get('mbartist', '')[:4]
    elif slug_mediatype == mediatypes.ALBUM and mediaitem.artistid is not None:
        foundone = False
        for album in get_cached_albums(mediaitem.artist, mediaitem.artistid):
            if album['label'] != mediaitem.album:
                continue
            if foundone:
                return mediaitem.uniqueids.get('mbalbum', '')[:4]
            foundone = True
    return None

# TODO: refactor to quickjson.JSONCache maybe

def cacheit(func):
    @wraps(func)
    def wrapper(*args):
        key = (func.__name__,) + args
        if key not in quickcache:
            quickcache[key] = func(*args)
        return quickcache[key]
    return wrapper

@cacheit
def get_cached_listdir(path):
    return xbmcvfs.listdir(path)

@cacheit
def get_cached_artists(artistname):
    return quickjson.get_artists_byname(artistname)

@cacheit
def get_cached_albums(artistname, dbid):
    return quickjson.get_albums(artistname, dbid)

@cacheit
def get_cached_songs(dbid):
    return quickjson.get_songs(mediatypes.ALBUM, dbid)

@cacheit
def get_cached_songs_bypath(path):
    return quickjson.get_songs(songfilter={'field': 'path', 'operator': 'is', 'value': path})

def get_cached_tvshow(dbid):
    tvshows = get_cached_tvshows()
    return next(show for show in tvshows if show['tvshowid'] == dbid)

@cacheit
def get_cached_tvshows():
    return quickjson.get_item_list(mediatypes.TVSHOW)

quickcache = {}
def clear_cache():
    quickcache.clear()
