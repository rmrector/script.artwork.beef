import requests
import xbmc
import xbmcvfs

from abc import ABCMeta, abstractmethod
from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
from cachecontrol.heuristics import BaseHeuristic

# Result dict of lists, keyed on art type
# {'url': URL, 'language': ISO alpha-2 code, 'rating': tuple; 0=sortable 1=display, 'size': 0=sortable 1=display, 'provider': self.name}
# TODO: preview
# language should be None if there is no text on the image
# subtype: disc type, BluRay or DVD or whatever.
# - Maybe for fanart it could be 'title' if the title is on the fanart, for posters and maybe banners it could be 'graphical' (or something) if there is no title

class AbstractProvider(object):
    __metaclass__ = ABCMeta

    name = None
    mediatype = None

    def __init__(self):
        # This would be better in devhelper, maybe
        cachepath = 'special://temp/cachecontrol/'
        if not xbmcvfs.exists(cachepath):
            xbmcvfs.mkdirs(cachepath)
        cachepath = unicode(xbmc.translatePath(cachepath), 'utf-8')
        self.session = CacheControl(requests.Session(), cache=FileCache(cachepath, forever=True), heuristic=OneDayCache())

    @abstractmethod
    def get_images(self, mediaid):
        pass

class OneDayCache(BaseHeuristic):
    """
    Cache the response by setting max-age to 1 day, if other caching isn't specified.
    """
    def update_headers(self, response):
        headers = {}

        if 'cache-control' not in response.headers or not response.headers['cache-control']:
            headers['cache-control'] = 'max-age=86400'
        elif 'max-age' not in response.headers['cache-control'] and 'no-cache' not in response.headers['cache-control'] and 'no-store' not in response.headers['cache-control']:
            headers['cache-control'] = response.headers['cache-control'] + ', max-age=86400'
        return headers

    def warning(self, response):
        if 'cache-control' not in response.headers or not response.headers['cache-control'] or 'max-age' not in response.headers['cache-control'] and 'no-cache' not in response.headers['cache-control'] and 'no-store' not in response.headers['cache-control']:
            return '110 - "Response is Stale"'
