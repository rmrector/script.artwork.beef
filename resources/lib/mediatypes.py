import re

from devhelper import pykodi

TVSHOW = 'tvshow'
MOVIE = 'movie'
EPISODE = 'episode'
SEASON = 'season'

settings = ('tvshow.poster', 'tvshow.fanart_limit', 'tvshow.banner', 'tvshow.clearlogo', 'tvshow.landscape', 'tvshow.clearart', 'tvshow.characterart_limit', 'season.poster', 'season.banner', 'season.landscape', 'episode.fanart', 'movie.poster', 'movie.fanart_limit', 'movie.banner', 'movie.clearlogo', 'movie.landscape', 'movie.clearart', 'movie.discart')

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
    SEASON: {
		'poster': {
            'autolimit': 1,
            'multiselect': False
		},
		# I want season fanart! From press shots or whatever released for/during a season. New characters added, old characters removed, season specific sets and objects. Anthology series like 'True Detective' and 'American Horror Story' will have fanart that is nearly always specific to a season.
		# 'fanart': {
        #     'autolimit': MULTIPLE_IMAGE_LIMIT,
        #     'multiselect': True
		# },
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
