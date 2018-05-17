import re

from lib.libs import pykodi

TVSHOW = 'tvshow'
MOVIE = 'movie'
EPISODE = 'episode'
SEASON = 'season'
MOVIESET = 'set'
MUSICVIDEO = 'musicvideo'
ARTIST = 'artist'
ALBUM = 'album'
SONG = 'song'
audiotypes = (ARTIST, ALBUM, SONG)
require_manualid = (MOVIESET, MUSICVIDEO)

addon = pykodi.get_main_addon()

def get_artinfo(mediatype, arttype):
    mediatype, arttype = hack_mediaarttype(mediatype, arttype)
    return artinfo[mediatype].get(arttype, default_artinfo)

def hack_mediaarttype(mediatype, arttype):
    # Seasons were implemented oddly and need special help
    if arttype.startswith('season.'):
        return SEASON, arttype.rsplit('.', 1)[1]
    else:
        return mediatype, arttype

default_artinfo = {'autolimit': 0, 'multiselect': False}
artinfo = {
    TVSHOW: {
        'poster': {
            'autolimit': 1,
            'multiselect': True
        },
        'fanart': {
            'autolimit': 5,
            'multiselect': True
        },
        'banner': {
            'autolimit': 1,
            'multiselect': False
        },
        'clearlogo': {
            'autolimit': 1,
            'multiselect': False
        },
        'landscape': {
            'autolimit': 1,
            'multiselect': False
        },
        'clearart': {
            'autolimit': 1,
            'multiselect': False
        },
        'characterart': {
            'autolimit': 1,
            'multiselect': True
        }
    },
    MOVIE: {
        'poster': {
            'autolimit': 1,
            'multiselect': True
        },
        'fanart': {
            'autolimit': 5,
            'multiselect': True
        },
        'banner': {
            'autolimit': 1,
            'multiselect': False
        },
        'clearlogo': {
            'autolimit': 1,
            'multiselect': False
        },
        'landscape': {
            'autolimit': 1,
            'multiselect': False
        },
        'clearart': {
            'autolimit': 1,
            'multiselect': False
        },
        'discart': {
            'autolimit': 1,
            'multiselect': False
        }
    },
    MOVIESET: {
        'poster': {
            'autolimit': 1,
            'multiselect': True
        },
        'fanart': {
            'autolimit': 5,
            'multiselect': True
        },
        'banner': {
            'autolimit': 1,
            'multiselect': False
        },
        'clearlogo': {
            'autolimit': 1,
            'multiselect': False
        },
        'landscape': {
            'autolimit': 1,
            'multiselect': False
        },
        'clearart': {
            'autolimit': 1,
            'multiselect': False
        },
        'discart': {
            'autolimit': 1,
            'multiselect': False
        }
    },
    SEASON: {
        'poster': {
            'autolimit': 1,
            'multiselect': False
        },
        'fanart': {
            'autolimit': 1,
            'multiselect': False
        },
        'banner': {
            'autolimit': 1,
            'multiselect': False
        },
        'landscape': {
            'autolimit': 1,
            'multiselect': False
        }
    },
    EPISODE: {
        'fanart': {
            'autolimit': 1,
            'multiselect': False
        }
    },
    MUSICVIDEO: {
        # album
        'poster': { # poster is what Kodi scrapers set and matches other areas of the video library,
                # but it should really be 'cover'
            'autolimit': 1,
            'multiselect': False
        },
        'discart': {
            'autolimit': 1,
            'multiselect': False
        },
        'fanart': { # artist or maybe album
            'autolimit': 3,
            'multiselect': True
        },
        # artist
        'artistthumb': {
            'autolimit': 1,
            'multiselect': False
        },
        'banner': {
            'autolimit': 1,
            'multiselect': False
        },
        'clearlogo': {
            'autolimit': 1,
            'multiselect': False
        },
        'clearart': {
            'autolimit': 1,
            'multiselect': False
        },
        'landscape': {
            'autolimit': 1,
            'multiselect': False
        }
    },
    ARTIST: {
        'thumb': {
            'autolimit': 1,
            'multiselect': False
        },
        'fanart': {
            'autolimit': 3,
            'multiselect': True
        },
        'banner': {
            'autolimit': 1,
            'multiselect': False
        },
        'clearlogo': {
            'autolimit': 1,
            'multiselect': False
        },
        'clearart': {
            'autolimit': 1,
            'multiselect': False
        },
        'landscape': {
            'autolimit': 1,
            'multiselect': False
        }
    },
    ALBUM: {
        'thumb': { # I'd much prefer 'cover', but for now it's thumb just like music video 'poster'
            'autolimit': 1,
            'multiselect': False
        },
        # I can imagine 'fanart' images that can be accurately attributed to an album rather than the artist,
        #  perhaps made from liner notes or press images, but nothing currently available from web services
        'discart': {
            'autolimit': 1,
            'multiselect': False
        },
        'back': {
            'autolimit': 1,
            'multiselect': False
        },
        'spine': {
            'autolimit': 1,
            'multiselect': False
        }
    },
    SONG: {
        'thumb': { # single cover
            'autolimit': 1,
            'multiselect': False
        }
    }
}

central_directories = {MOVIESET: False}
todownload = dict((mediatype, False) for mediatype in artinfo)
togenerate = dict((mediatype, False) for mediatype in artinfo)
othertypes = dict((mediatype, []) for mediatype in artinfo)
arttype_settingskeys = [m[0] + '.' + art[0] + ('_limit' if art[1]['multiselect'] else '')
    for m in artinfo.iteritems() for art in m[1].iteritems()]

def disabled(mediatype):
    return not any(iter_every_arttype(mediatype))

def iter_every_arttype(mediatype):
    for arttype, info in artinfo[mediatype].items():
        if not info['autolimit']:
            continue
        yield arttype
        if info['autolimit'] > 1:
            for num in xrange(1, info['autolimit']):
                yield arttype + str(num)

    for arttype in othertypes[mediatype]:
        yield arttype

def downloadartwork(mediatype):
    return todownload.get(mediatype, False)

def generatethumb(mediatype):
    return togenerate.get(mediatype, False)

def update_settings():
    for settingid in arttype_settingskeys:
        splitsetting = re.split(r'\.|_', settingid)
        thistype = artinfo[splitsetting[0]][splitsetting[1]]
        try:
            thistype['autolimit'], thistype['multiselect'] = _get_autolimit_from_setting(settingid)
        except ValueError:
            addon.set_setting(settingid, thistype['autolimit'])
            addon.set_setting(settingid, thistype['multiselect'])
    for mediatype in artinfo:
        todownload[mediatype] = addon.get_setting(mediatype + '.downloadartwork')
        othertypes[mediatype] = [t.strip() for t in addon.get_setting(mediatype + '.othertypes').split(',')]
    for mediatype in ('tvshow', 'episode', 'movie', 'set', 'musicvideo'):
        # DEPRECATED: 2018-03-10
        if addon.get_setting(mediatype + '.downloadartwork') == 'False':
            addon.set_setting(mediatype + '.downloadartwork', False)
    olddownload_enabled = addon.get_setting('download_artwork')
    if olddownload_enabled != '':
        # DEPRECATED: 2018-02-23
        olddownload_enabled = bool(olddownload_enabled)
        addon.set_setting('tvshow.downloadartwork', olddownload_enabled)
        addon.set_setting('episode.downloadartwork', olddownload_enabled)
        addon.set_setting('movie.downloadartwork', olddownload_enabled)
        addon.set_setting('set.downloadartwork', olddownload_enabled)
        addon.set_setting('musicvideo.downloadartwork', olddownload_enabled)
        addon.set_setting('download_artwork', '')
    for mediatype in (MOVIESET,):
        central_directories[mediatype] = addon.get_setting('centraldir.{0}_enabled'.format(mediatype))
        if central_directories[mediatype]:
            central_directories[mediatype] = addon.get_setting('centraldir.{0}_dir'.format(mediatype))
    for mediatype in (EPISODE, MOVIE, MUSICVIDEO):
        togenerate[mediatype] = addon.get_setting('{0}.thumb_generate'.format(mediatype))

def _get_autolimit_from_setting(settingid):
    result = addon.get_setting(settingid)
    if settingid.endswith('_limit'):
        result = int(result)
        return result, result > 1
    return (1 if result else 0), False

update_settings()
