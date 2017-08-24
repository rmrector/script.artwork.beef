from lib.libs import pykodi

addon = pykodi.get_main_addon()

DEFAULT_IMAGESIZE = '1920x1080'
AVAILABLE_IMAGESIZES = {'1920x1080': (1920, 1080, 700), '1280x720': (1280, 720, 520)}

class Settings(object):
    def __init__(self):
        self.addon_path = addon.path
        self.update_settings()

    def update_settings(self):
        self._autoadd_episodes = addon.get_setting('autoaddepisodes_list') if addon.get_setting('episode.fanart') else ()
        self.enableservice = addon.get_setting('enableservice')
        self.enable_olditem_updates = addon.get_setting('enable_olditem_updates')
        self.generate_episode_thumb = addon.get_setting('episode.thumb_generate')
        self.generate_movie_thumb = addon.get_setting('move.thumb_generate')
        self.only_filesystem = addon.get_setting('only_filesystem')
        self.titlefree_fanart = addon.get_setting('titlefree_fanart')
        self.setartwork_fromcentral = addon.get_setting('setartwork_fromcentral')
        self.setartwork_dir = addon.get_setting('setartwork_dir')
        self.setartwork_fromparent = addon.get_setting('setartwork_fromparent')
        self.hqpreview = addon.get_setting('highquality_preview')
        self.save_additional_arttypes = addon.get_setting('save_additional_arttypes')
        self.identify_alternatives = addon.get_setting('identify_alternatives')
        self.fanarttv_clientkey = addon.get_setting('fanarttv_key')

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
