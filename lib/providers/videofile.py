import re
import urllib
from abc import ABCMeta

from lib.libs import mediatypes
from lib.libs.addonsettings import settings
from lib.libs.pykodi import localize as L
from lib.libs.utils import SortedDisplay, get_movie_path_list

VIDEO_FILE = 32004
VIDEO_FILE_THUMB = 32005

class VideoFileAbstractProvider(object):
    __metaclass__ = ABCMeta
    name = SortedDisplay('video:thumb', VIDEO_FILE)

    def build_video_thumbnail(self, path):
        url = build_video_thumbnail_path(path)
        return {'url': url, 'rating': SortedDisplay(0, ''), 'language': 'xx', 'title': L(VIDEO_FILE_THUMB),
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

    def get_exact_images(self, mediaitem):
        if not mediatypes.generatethumb(mediaitem.mediatype):
            return {}
        path = get_movie_path_list(mediaitem.file)[0]
        if path.endswith('.iso'):
            return {}
        return {'thumb': self.build_video_thumbnail(path)}

class VideoFileEpisodeProvider(VideoFileAbstractProvider):
    mediatype = mediatypes.EPISODE

    def get_exact_images(self, mediaitem):
        path = mediaitem.file
        if not mediatypes.generatethumb(mediaitem.mediatype) or path.endswith('.iso'):
            return {}
        return {'thumb': self.build_video_thumbnail(path)}

class VideoFileMusicVideoProvider(VideoFileEpisodeProvider):
    mediatype = mediatypes.MUSICVIDEO
