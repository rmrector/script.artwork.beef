import xbmc

from lib.libs import pykodi

addon = pykodi.get_main_addon()

DEFAULT_IMAGESIZE = '1920x1080'
AVAILABLE_IMAGESIZES = {'1920x1080': (1920, 1080, 700), '1280x720': (1280, 720, 520)}

PROGRESS_DISPLAY_FULLPROGRESS = '0'
PROGRESS_DISPLAY_WARNINGSERRORS = '1'
PROGRESS_DISPLAY_NONE = '2' # Only add-on crashes

class Settings(object):
    def __init__(self):
        self.addon_path = addon.path
        self.datapath = addon.datapath
        self._autoadd_episodes = ()
        self.update_settings()
        self.update_useragent()

    def update_useragent(self):
        beefversion = pykodi.get_main_addon().version
        if pykodi.get_kodi_version() < 17:
            from lib.libs import quickjson
            props = quickjson.get_application_properties(['name', 'version'])
            appversion = '{0}.{1}'.format(props['version']['major'], props['version']['minor'])
            self.useragent = 'ArtworkBeef/{0} {1}/{2}'.format(beefversion, props['name'], appversion)
            return
        self.useragent = 'ArtworkBeef/{0} '.format(beefversion) + xbmc.getUserAgent()

    def update_settings(self):
        self._autoadd_episodes = addon.get_setting('autoaddepisodes_list') if addon.get_setting('episode.fanart') else ()
        self.enableservice = addon.get_setting('enableservice')
        self.enableservice_music = addon.get_setting('enableservice_music')
        self.enable_olditem_updates = addon.get_setting('enable_olditem_updates')
        self.generate_episode_thumb = addon.get_setting('episode.thumb_generate')
        self.generate_movie_thumb = addon.get_setting('movie.thumb_generate')
        self.generate_musicvideo_thumb = addon.get_setting('musicvideo.thumb_generate')
        self.only_filesystem = addon.get_setting('only_filesystem')
        self.titlefree_fanart = addon.get_setting('titlefree_fanart')
        self.titlefree_poster = addon.get_setting('titlefree_poster')
        self.setartwork_fromparent = addon.get_setting('setartwork_fromparent')
        self.identify_alternatives = addon.get_setting('identify_alternatives')
        self.report_peritem = addon.get_setting('report_peritem')
        self.fanarttv_clientkey = addon.get_setting('fanarttv_key')
        self.default_tvidsource = addon.get_setting('default_tvidsource')
        self.prefer_tmdbartwork = addon.get_setting('prefer_tmdbartwork')
        self.progressdisplay = addon.get_setting('progress_display')
        self.final_notification = addon.get_setting('final_notification')
        self.save_extrafanart = addon.get_setting('save_extrafanart')
        self.save_extrafanart_mvids = addon.get_setting('save_extrafanart_mvids')
        self.remove_deselected_files = addon.get_setting('remove_deselected_files')
        self.recycle_removed = addon.get_setting('recycle_removed')
        self.savewith_basefilename = addon.get_setting('savewith_basefilename')
        self.savewith_basefilename_mvids = addon.get_setting('savewith_basefilename_mvids')
        self.albumartwithmediafiles = addon.get_setting('albumartwithmediafiles')
        self.cache_local_video_artwork = addon.get_setting('cache_local_video_artwork')
        self.cache_local_music_artwork = addon.get_setting('cache_local_music_artwork')

        self.language_override = addon.get_setting('language_override')
        if self.language_override == 'None':
            self.language_override = None

        try:
            self.minimum_rating = int(addon.get_setting('minimum_rating'))
        except ValueError:
            self.minimum_rating = 5
            addon.set_setting('minimum_rating', "5")

        sizesetting = addon.get_setting('preferredsize')
        if sizesetting in AVAILABLE_IMAGESIZES:
            self.preferredsize = AVAILABLE_IMAGESIZES[sizesetting][0:2]
            self.minimum_size = AVAILABLE_IMAGESIZES[sizesetting][2]
        else:
            self.preferredsize = AVAILABLE_IMAGESIZES[DEFAULT_IMAGESIZE][0:2]
            self.minimum_size = AVAILABLE_IMAGESIZES[DEFAULT_IMAGESIZE][2]
            addon.set_setting('preferredsize', DEFAULT_IMAGESIZE)

    @property
    def autoadd_episodes(self):
        return self._autoadd_episodes

    @autoadd_episodes.setter
    def autoadd_episodes(self, value):
        self._autoadd_episodes = value
        addon.set_setting('autoaddepisodes_list', value)

settings = Settings()
