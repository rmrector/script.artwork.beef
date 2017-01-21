import re

import pykodi

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
            artinfo[splitsetting[0]][splitsetting[1]]['autolimit'] = get_autolimit(settingid)
        except ValueError:
            addon.set_setting(settingid, artinfo[splitsetting[0]][splitsetting[1]]['autolimit'])

def get_autolimit(settingid):
    result = addon.get_setting(settingid)
    if settingid.endswith('_limit'):
        return int(result)
    return 1 if result else 0

update_settings()
