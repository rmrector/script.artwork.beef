import re
import urllib
from abc import ABCMeta

from lib.libs import mediatypes
from lib.libs.addonsettings import settings
from lib.libs.utils import SortedDisplay, get_movie_path_list

class VideoFileAbstractProvider(object):
    __metaclass__ = ABCMeta
    name = SortedDisplay('video:thumb', 'video file')

    def build_video_thumbnail(self, path):
        url = build_video_thumbnail_path(path)
        return {'url': url, 'rating': SortedDisplay(0, ''), 'language': 'xx', 'title': "Video thumbnail",
            'provider': self.name, 'size': SortedDisplay(0, ''), 'preview': url}

def build_video_thumbnail_path(videofile):
    if videofile.startswith('image://'):
        return videofile
    # Kodi goes lowercase and doesn't encode some chars
    result = 'image://video@{0}/'.format(urllib.quote(videofile, '()!'))
    result = re.sub(r'%[0-9A-F]{2}', lambda mo: mo.group().lower(), result)
    return result

class VideoFileMovieProvider(VideoFileAbstractProvider):
    mediatype = mediatypes.MOVIE

    def get_exact_images(self, path):
        if not settings.generate_movie_thumb:
            return {}
        paths = get_movie_path_list(path)
        if paths[0].endswith('.iso'):
            return {}
        return {'thumb': self.build_video_thumbnail(paths[0])}

class VideoFileEpisodeProvider(VideoFileAbstractProvider):
    mediatype = mediatypes.EPISODE

    def get_exact_images(self, path):
        if not settings.generate_episode_thumb or path.endswith('.iso'):
            return {}
        return {'thumb': self.build_video_thumbnail(path)}
