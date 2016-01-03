import requests
import xbmc
import xbmcvfs

from abc import ABCMeta, abstractmethod
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
from cachecontrol.heuristics import OneDayCache

# Result dict of lists, keyed on art type
# {'url': URL, 'language': ISO alpha-2 code, 'rating': tuple; 0=sortable 1=display, 'size': 0=sortable 1=display, 'provider': self.name}
# IDEA: add 'noauto', for Fanart.tv's goofy aspect ratio posters, and frequent dupes in backgrounds

class AbstractProvider(object):
    __metaclass__ = ABCMeta

    name = None
    mediatype = None

    def __init__(self):
        # This would be better in devhelper, maybe
        cachepath = 'special://temp/requests/'
        if not xbmcvfs.exists(cachepath):
            xbmcvfs.mkdirs(cachepath)
        cachepath = unicode(xbmc.translatePath(cachepath), 'utf-8')
        self.session = CacheControl(requests.Session(), cache=FileCache(cachepath, forever=True), heuristic=OneDayCache())

    @abstractmethod
    def get_images(self, media_id):
        pass
