import re

from lib.libs import pykodi

TVSHOW = 'tvshow'
MOVIE = 'movie'
EPISODE = 'episode'
SEASON = 'season'
MOVIESET = 'set'

settings = ('tvshow.poster', 'tvshow.fanart_limit', 'tvshow.banner', 'tvshow.clearlogo', 'tvshow.landscape',
    'tvshow.clearart', 'tvshow.characterart_limit', 'season.poster', 'season.banner', 'season.landscape',
    'episode.fanart', 'movie.poster', 'movie.fanart_limit', 'movie.banner', 'movie.clearlogo', 'movie.landscape',
    'movie.clearart', 'movie.discart', 'set.poster', 'set.fanart_limit', 'set.banner', 'set.clearlogo',
    'set.landscape', 'set.clearart', 'set.discart')

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
    }
}

def update_settings():
    for settingid in settings:
        splitsetting = re.split(r'\.|_', settingid)
        try:
            artinfo[splitsetting[0]][splitsetting[1]]['autolimit'] = _get_autolimit_from_setting(settingid)
        except ValueError:
            addon.set_setting(settingid, artinfo[splitsetting[0]][splitsetting[1]]['autolimit'])

def _get_autolimit_from_setting(settingid):
    result = addon.get_setting(settingid)
    if settingid.endswith('_limit'):
        return int(result)
    return 1 if result else 0

update_settings()
