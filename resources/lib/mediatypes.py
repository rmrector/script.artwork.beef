from devhelper import pykodi

TVSHOW = 'tvshow'
MOVIE = 'movie'
EPISODE = 'episode'
SEASON = 'season'

DEFAULT_FANART_LIMIT = 5

addon = pykodi.get_main_addon()

artinfo = {
    TVSHOW: {
        'poster': {
            'localizeid': 32128,
            'autolimit': 1,
            'multiselect': False
		},
        'fanart': {
	        'localizeid': 32121,
	        'autolimit': DEFAULT_FANART_LIMIT,
	        'multiselect': True
		},
        'banner': {
	        'localizeid': 32123,
	        'autolimit': 1,
	        'multiselect': False
		},
		'clearlogo': {
	        'localizeid': 32126,
	        'autolimit': 1,
	        'multiselect': False
		},
		'landscape': {
	        'localizeid': 32130,
	        'autolimit': 1,
	        'multiselect': False
	    },
		'clearart': {
	        'localizeid': 32125,
	        'autolimit': 1,
	        'multiselect': False
	    },
	    'characterart': {
	        'localizeid': 32127,
	        'autolimit': 1,
	        'multiselect': False
	    }
    },
    MOVIE: {
		'poster': {
            'localizeid': 32128,
            'autolimit': 1,
            'multiselect': False
		},
		'fanart': {
	        'localizeid': 32121,
	        'autolimit': DEFAULT_FANART_LIMIT,
	        'multiselect': True
		},
		'banner': {
	        'localizeid': 32123,
	        'autolimit': 1,
	        'multiselect': False
		},
		'clearlogo': {
	        'localizeid': 32126,
	        'autolimit': 1,
	        'multiselect': False
		},
		'landscape': {
	        'localizeid': 32130,
	        'autolimit': 1,
	        'multiselect': False
	    },
		'clearart': {
	        'localizeid': 32125,
	        'autolimit': 1,
	        'multiselect': False
	    },
	    'discart': {
	        'localizeid': 32132,
	        'autolimit': 1,
	        'multiselect': False
	    }
	},
    SEASON: {
		'poster': {
            'localizeid': 32128,
            'autolimit': 1,
            'multiselect': False
		},
		# I want season fanart! From press shots or whatever released for/during a season. New characters added, old characters removed, season specific sets or object. Anthology series like 'True Detective' and 'American Horror Story' will have fanart that is nearly always specific to a season.
		# 'fanart': {
        #     'localizeid': 32121,
        #     'autolimit': MULTIPLE_IMAGE_LIMIT,
        #     'multiselect': True
		# },
		'banner': {
	        'localizeid': 32123,
	        'autolimit': 1,
	        'multiselect': False
		},
        'landscape': {
	        'localizeid': 32130,
	        'autolimit': 1,
	        'multiselect': False
		}
    },
    EPISODE: {
        'fanart': {
	        'localizeid': 32121,
	        'autolimit': 1, # Only considered by individual episode or series, not full library
	        'multiselect': False
		}
    }
}

def update_settings():
    try:
        limit = int(addon.get_setting('fanart_limit'))
    except ValueError:
        limit = DEFAULT_FANART_LIMIT
        addon.set_setting('fanart_limit', DEFAULT_FANART_LIMIT)
    artinfo[TVSHOW]['fanart']['autolimit'] = limit
    artinfo[MOVIE]['fanart']['autolimit'] = limit

update_settings()
