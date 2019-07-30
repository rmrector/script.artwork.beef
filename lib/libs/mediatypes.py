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

PREFERRED_SOURCE_SHARED = {'0': None, '1': 'fanart.tv'}
PREFERRED_SOURCE_MEDIA = {'tvshows': ('thetvdb.com', (TVSHOW, SEASON, EPISODE)),
    'movies': ('themoviedb.org', (MOVIE, MOVIESET)),
    'music': ('theaudiodb.com', audiotypes),
    'musicvideos': ('theaudiodb.com', (MUSICVIDEO,))}

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

default_artinfo = {'autolimit': 0, 'multiselect': False, 'download': False}
artinfo = {
    TVSHOW: {
        'poster': {
            'autolimit': 1,
            'multiselect': False,
            'limit_setting': True,
            'download': False
        },
        'keyart': {
            'autolimit': 0,
            'multiselect': False,
            'limit_setting': True,
            'download': False
        },
        'fanart': {
            'autolimit': 5,
            'multiselect': True,
            'limit_setting': True,
            'download': False
        },
        'banner': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'clearlogo': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'landscape': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'clearart': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'characterart': {
            'autolimit': 1,
            'multiselect': False,
            'limit_setting': True,
            'download': False
        }
    },
    MOVIE: {
        'poster': {
            'autolimit': 1,
            'multiselect': False,
            'limit_setting': True,
            'download': False
        },
        'keyart': {
            'autolimit': 0,
            'multiselect': False,
            'limit_setting': True,
            'download': False
        },
        'fanart': {
            'autolimit': 5,
            'multiselect': True,
            'limit_setting': True,
            'download': False
        },
        'banner': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'clearlogo': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'landscape': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'clearart': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'discart': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'characterart': {
            'autolimit': 1,
            'multiselect': False,
            'limit_setting': True,
            'download': False
        },
        'animatedposter': {
            'autolimit': 0,
            'multiselect': False,
            'download': True
        },
        'animatedkeyart': {
            'autolimit': 0,
            'multiselect': False,
            'download': True
        },
        'animatedfanart': {
            'autolimit': 0,
            'multiselect': True,
            'limit_setting': True,
            'download': True
        }
    },
    MOVIESET: {
        'poster': {
            'autolimit': 1,
            'multiselect': False,
            'limit_setting': True,
            'download': False
        },
        'keyart': {
            'autolimit': 0,
            'multiselect': False,
            'limit_setting': True,
            'download': False
        },
        'fanart': {
            'autolimit': 5,
            'multiselect': True,
            'limit_setting': True,
            'download': False
        },
        'banner': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'clearlogo': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'landscape': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'clearart': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'discart': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        }
    },
    SEASON: {
        'poster': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'fanart': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'banner': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'landscape': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        }
    },
    EPISODE: {
        'fanart': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        }
    },
    MUSICVIDEO: {
        # album
        'poster': { # poster is what Kodi scrapers set and matches other areas of the video library,
                # but it should really be 'cover'
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'discart': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'fanart': { # artist or maybe album
            'autolimit': 3,
            'multiselect': True,
            'limit_setting': True,
            'download': False
        },
        # artist
        'artistthumb': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'banner': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'clearlogo': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'clearart': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'landscape': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        }
    },
    ARTIST: {
        'thumb': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'fanart': {
            'autolimit': 3,
            'multiselect': True,
            'limit_setting': True,
            'download': False
        },
        'banner': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'clearlogo': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'clearart': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'landscape': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        }
    },
    ALBUM: {
        'thumb': { # I'd much prefer 'cover', but for now it's thumb just like music video 'poster'
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        # I can imagine 'fanart' images that can be accurately attributed to an album rather than the artist,
        #  perhaps made from liner notes or press images, but nothing currently available from web services
        'discart': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'back': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        },
        'spine': {
            'autolimit': 1,
            'multiselect': False,
            'download': False
        }
    },
    SONG: {
        'thumb': { # single cover
            'autolimit': 1,
            'multiselect': False,
            'download': False
        }
    }
}

central_directories = {MOVIESET: False}
togenerate = dict((mediatype, False) for mediatype in artinfo)
preferred = dict((mediatype, None) for mediatype in artinfo)
onlyfs = dict((mediatype, False) for mediatype in artinfo)
othertypes = dict((mediatype, []) for mediatype in artinfo)
download_arttypes = dict((mediatype, []) for mediatype in artinfo)
arttype_settingskeys = [m[0] + '.' + art[0] + ('_limit' if art[1].get('limit_setting') else '')
    for m in artinfo.items() for art in m[1].items()]

def disabled(mediatype):
    return not any(iter_every_arttype(mediatype)) and not generatethumb(mediatype) and \
        not downloadanyartwork(mediatype)

def iter_every_arttype(mediatype):
    for arttype, info in artinfo[mediatype].items():
        if not info['autolimit']:
            continue
        yield arttype
        if info['autolimit'] > 1:
            for num in range(1, info['autolimit']):
                yield arttype + str(num)

    for arttype in othertypes[mediatype]:
        yield arttype

def downloadartwork(mediatype, arttype):
    mediatype, arttype = hack_mediaarttype(mediatype, arttype)
    arttype, _ = _split_arttype(arttype)
    if arttype in download_arttypes.get(mediatype, ()):
        return True
    info = get_artinfo(mediatype, arttype)
    return info['download']

def downloadanyartwork(mediatype):
    if download_arttypes.get(mediatype):
        return True
    info = artinfo.get(mediatype)
    if not info:
        return False
    return any(x for x in info.values() if x['download'])

def _split_arttype(arttype):
    basetype = arttype.rstrip('0123456789')
    idx = 0 if basetype == arttype else int(arttype.replace(basetype, ''))
    return basetype, idx

def generatethumb(mediatype):
    return togenerate.get(mediatype, False)

def haspreferred_source(mediatype):
    return bool(preferred.get(mediatype))

def ispreferred_source(mediatype, provider):
    return provider == preferred.get(mediatype, '')

def only_filesystem(mediatype):
    return onlyfs.get(mediatype, False)

def update_settings():
    always_multiple_selection = addon.get_setting('always_multiple_selection')
    if not always_multiple_selection:
        _set_allmulti(False)
    for settingid in arttype_settingskeys:
        splitsetting = settingid.split('.')
        thistype = artinfo[splitsetting[0]][splitsetting[1].split('_')[0]]
        try:
            thistype['autolimit'], thistype['multiselect'] = _get_autolimit_from_setting(settingid)
        except ValueError:
            addon.set_setting(settingid, thistype['autolimit'])
            addon.set_setting(settingid, thistype['multiselect'])
    if always_multiple_selection:
        _set_allmulti(True)
    for mediatype in artinfo:
        olddownload = addon.get_setting(mediatype + '.downloadartwork')
        if olddownload != '':
            # DEPRECATED: 2018-05-19
            if olddownload:
                addon.set_setting(mediatype + '.download_arttypes', ', '.join(artinfo[mediatype]))
                if mediatype == TVSHOW:
                    addon.set_setting('season.download_arttypes', ', '.join(artinfo['season']))
            addon.set_setting(mediatype + '.downloadartwork', '')
        othertypes[mediatype] = [t.strip() for
            t in addon.get_setting(mediatype + '.othertypes').split(',')]
        if len(othertypes[mediatype]) == 1 and not othertypes[mediatype][0]:
            othertypes[mediatype] = []
        download_arttypes[mediatype] = [t.strip() for
            t in addon.get_setting(mediatype + '.download_arttypes').split(',')]
        if len(download_arttypes[mediatype]) == 1 and not download_arttypes[mediatype][0]:
            download_arttypes[mediatype] = []
        for atype in artinfo[mediatype]:
            dl = atype in download_arttypes[mediatype]
            artinfo[mediatype][atype]['download'] = dl
            if dl:
                del download_arttypes[mediatype][download_arttypes[mediatype].index(atype)]

    for mediatype in (MOVIESET,):
        central_directories[mediatype] = addon.get_setting('centraldir.{0}_enabled'.format(mediatype))
        if central_directories[mediatype]:
            central_directories[mediatype] = addon.get_setting('centraldir.{0}_dir'.format(mediatype))
    for mediatype in (EPISODE, MOVIE, MUSICVIDEO):
        togenerate[mediatype] = addon.get_setting('{0}.thumb_generate'.format(mediatype))

    old_prefer_tmdb = addon.get_setting('prefer_tmdbartwork')
    if old_prefer_tmdb != '':
        # DEPRECATED: 2018-05-25
        if old_prefer_tmdb:
            addon.set_setting('preferredsource_movies', '2')
        addon.set_setting('prefer_tmdbartwork', '')
    old_only_filesystem = addon.get_setting('only_filesystem')
    if old_only_filesystem != '':
        # DEPRECATED: 2018-05-26
        if old_only_filesystem:
            for media in PREFERRED_SOURCE_MEDIA:
                addon.set_setting('onlyfilesystem_' + media, True)
        addon.set_setting('only_filesystem', '')
    for media, config in PREFERRED_SOURCE_MEDIA.items():
        result = addon.get_setting('preferredsource_' + media)
        downloadconfig = addon.get_setting('download_config_' + media)
        if downloadconfig not in ('0', '1', '2'):
            # DEPRECATED: default to '2' for now for upgraders, can go back to '0' later
            downloadconfig = '2'
            addon.set_setting('download_config_' + mediatype, downloadconfig)
        for mediatype in config[1]:
            if result in ('0', '1', '2'):
                preferred[mediatype] = PREFERRED_SOURCE_SHARED[result] if \
                    result in PREFERRED_SOURCE_SHARED else PREFERRED_SOURCE_MEDIA.get(media, (None,))[0]
            else:
                preferred[mediatype] = None
                addon.set_setting('preferredsource_' + media, '0')
            onlyfs[mediatype] = addon.get_setting('onlyfs_' + media)

            if downloadconfig == '0': # None
                download_arttypes[mediatype] = []
                for atype in artinfo[mediatype].values():
                    atype['download'] = False
            elif downloadconfig == '1': # all configured from web and local
                download_arttypes[mediatype] = list(othertypes[mediatype])
                for atype in artinfo[mediatype].values():
                    atype['download'] = atype['autolimit'] > 0
            # Kodi doesn't cache gifs, so always download animated artwork
            for arttype, artconfig in artinfo[mediatype].items():
                if arttype.startswith('animated'):
                    artconfig['download'] = True

def _get_autolimit_from_setting(settingid):
    result = addon.get_setting(settingid)
    if settingid.endswith('_limit'):
        result = int(result)
        return result, result > 1
    return (1 if result else 0), False

def _set_allmulti(always_multi):
    for typeinfo in artinfo.values():
        for arttypeinfo in typeinfo.values():
            arttypeinfo['multiselect'] = always_multi

update_settings()
