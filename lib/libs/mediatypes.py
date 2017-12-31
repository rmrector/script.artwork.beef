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
            'multiselect': False
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
            'multiselect': False
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
            'multiselect': False
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
arttype_settingskeys = [m[0] + '.' + art[0] + ('_limit' if art[1]['multiselect'] else '')
    for m in artinfo.iteritems() for art in m[1].iteritems()]

def update_settings():
    for settingid in arttype_settingskeys:
        splitsetting = re.split(r'\.|_', settingid)
        try:
            artinfo[splitsetting[0]][splitsetting[1]]['autolimit'] = _get_autolimit_from_setting(settingid)
        except ValueError:
            addon.set_setting(settingid, artinfo[splitsetting[0]][splitsetting[1]]['autolimit'])
    oldset_enabled = addon.get_setting('setartwork_fromcentral')
    if oldset_enabled != '':
        addon.set_setting('centraldir.set_enabled', oldset_enabled)
        addon.set_setting('setartwork_fromcentral', '')
        if oldset_enabled:
            addon.set_setting('centraldir.set_dir', addon.get_setting('setartwork_dir'))
            addon.set_setting('setartwork_dir', '')
    for mediatype in central_directories:
        central_directories[mediatype] = addon.get_setting('centraldir.{0}_enabled'.format(mediatype))
        if central_directories[mediatype]:
            central_directories[mediatype] = addon.get_setting('centraldir.{0}_dir'.format(mediatype))

def _get_autolimit_from_setting(settingid):
    result = addon.get_setting(settingid)
    if settingid.endswith('_limit'):
        return int(result)
    return 1 if result else 0

update_settings()
