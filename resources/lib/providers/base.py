import requests
import xbmc
import xbmcvfs
from abc import ABCMeta, abstractmethod

from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
from cachecontrol.heuristics import BaseHeuristic
from requests.exceptions import Timeout
from devhelper.pykodi import log

from requests.packages import urllib3
urllib3.disable_warnings()

# Result dict of lists, keyed on art type
# {'url': URL, 'language': ISO alpha-2 code, 'rating': tuple; 0=sortable 1=display, 'size': 0=sortable 1=display, 'provider': self.name, 'status': noauto/happy, 'preview': preview URL}
# language should be None if there is no text on the image
# subtype: disc type, BluRay or DVD or whatever.
# - Maybe for fanart it could be 'title' if the title is on the fanart, for posters and maybe banners it could be 'graphical' (or something) if there is no title

class AbstractProvider(object):
    __metaclass__ = ABCMeta

    name = None
    mediatype = None

    monitor = xbmc.Monitor()

    def __init__(self):
        # This would be better in devhelper, maybe
        cachepath = 'special://temp/cachecontrol/'
        if not xbmcvfs.exists(cachepath):
            xbmcvfs.mkdirs(cachepath)
        cachepath = unicode(xbmc.translatePath(cachepath), 'utf-8')
        self.session = CacheControl(requests.Session(), cache=FileCache(cachepath), heuristic=ForceDaysCache(7))

    def doget(self, url, params=None, headers=None):
        result = self._inget(url, params, headers)
        if result == None:
            return
        errcount = 0
        while result.status_code == requests.codes.too_many_requests:
            if errcount > 2:
                self.log('too many requests', xbmc.LOGWARNING)
                return
            errcount += 1
            try:
                wait = int(result.headers.get('Retry-After')) + 1
            except ValueError:
                wait = 10
            if self.monitor.waitForAbort(wait):
                return
            result = self._inget(url, params=params, headers=headers)

        if result == None:
            return
        if result.status_code == requests.codes.not_found:
            return
        return result

    def _inget(self, url, params=None, headers=None, timeout=15):
        try:
            return self.session.get(url, params=params, headers=headers, timeout=timeout)
        except Timeout:
            try:
                return self.session.get(url, params=params, headers=headers, timeout=timeout)
            except Timeout:
                self.log('timeout {0}s x2'.format(timeout), xbmc.LOGWARNING)

    def log(self, message, level=xbmc.LOGDEBUG):
        log(message, level, tag='%s.%s' % (self.name, self.mediatype))

    @abstractmethod
    def get_images(self, mediaid):
        pass

class ForceDaysCache(BaseHeuristic):
    """
    Cache the response for exactly `days` days, overriding other caches
    """
    def __init__(self, days=1):
        self.days = days

    def update_headers(self, response):
        return {'cache-control': 'max-age={0:d}'.format(self.days * 24 * 60 * 60)}

    def warning(self, response):
        return '110 - "If this is not fresh, then it is stale."'


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
            return '110 - "If this is not fresh, then it is stale."'
