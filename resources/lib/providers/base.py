import requests
import sys
import xbmc
import xbmcvfs
from abc import ABCMeta, abstractmethod
from requests.exceptions import HTTPError

from cachecontrol import CacheControl
from cachecontrol.caches import FileCache
from cachecontrol.heuristics import BaseHeuristic
from requests.exceptions import Timeout
from devhelper.pykodi import log

from requests.packages import urllib3
urllib3.disable_warnings()

from sorteddisplaytuple import SortedDisplay

# Result dict of lists, keyed on art type
# {'url': URL, 'language': ISO alpha-2 code, 'rating': (sortable, display), 'size': (sortable, display), 'provider': self.name, 'preview': preview URL}
# language should be None if there is no text on the image
# subtype: disc type, BluRay or DVD or whatever.

class AbstractProvider(object):
    __metaclass__ = ABCMeta

    name = SortedDisplay(0, '')
    mediatype = None

    monitor = xbmc.Monitor()

    def __init__(self):
        self.contenttype = None
        # This would be better in devhelper, maybe
        cachepath = 'special://temp/cachecontrol/'
        if not xbmcvfs.exists(cachepath):
            xbmcvfs.mkdirs(cachepath)
        cachepath = unicode(xbmc.translatePath(cachepath), 'utf-8')
        self.session = CacheControl(requests.Session(), cache=FileCache(cachepath, use_dir_lock=True), heuristic=ForceDaysCache(7))

    def set_contenttype(self, contenttype):
        self.session.headers['Accept'] = contenttype
        self.contenttype = contenttype

    def doget(self, url, params=None, headers=None):
        result = self._inget(url, params, headers)
        if result == None:
            return
        errcount = 0
        if result.status_code == requests.codes.unauthorized:
            if self.login():
                result = self._inget(url, params, headers)
                if result is None:
                    return
        while result.status_code == requests.codes.too_many_requests:
            if errcount > 2:
                raise ProviderError, "Too many requests", sys.exc_info()[2]
            errcount += 1
            try:
                wait = int(result.headers.get('Retry-After')) + 1
            except ValueError:
                wait = 10
            if self.monitor.waitForAbort(wait):
                return
            result = self._inget(url, params, headers)
            if result == None:
                return

        if result.status_code == requests.codes.not_found:
            return
        try:
            result.raise_for_status()
        except HTTPError:
            raise ProviderError, (sys.exc_info()[1].message, sys.exc_info()[1]), sys.exc_info()[2]
        if not result.from_cache and result.status_code < 400:
            self.log('uncached')
        if not result.headers['Content-Type'].startswith(self.contenttype):
            raise ProviderError, "Provider returned unexected content", sys.exc_info()[2]
        return result

    def _inget(self, url, params=None, headers=None, timeout=15):
        try:
            return self.session.get(url, params=params, headers=headers, timeout=timeout)
        except Timeout:
            try:
                return self.session.get(url, params=params, headers=headers, timeout=timeout)
            except Timeout as ex:
                raise ProviderError, ("Provider is not responding", ex), sys.exc_info()[2]

    def log(self, message, level=xbmc.LOGDEBUG):
        log(message, level, tag='%s.%s' % (self.name.sort, self.mediatype))

    def login(self):
        return False

    @abstractmethod
    def get_images(self, mediaid):
        pass

class ForceDaysCache(BaseHeuristic):
    """
    Cache the response for exactly `days` days, overriding other caches
    """
    def __init__(self, days=1):
        self.days = days

    # pylint: disable=unused-argument
    def update_headers(self, response):
        return {'cache-control': 'max-age={0:d}'.format(self.days * 24 * 60 * 60)}

    def warning(self, response):
        return '110 - "If this is not fresh, then it is stale."'


class OneDayCache(BaseHeuristic):
    """
    Cache the response by setting max-age to 1 day, if other caching isn't specified.
    """
    def __init__(self, days=1):
        self.days = days

    def update_headers(self, response):
        headers = {}

        if 'cache-control' not in response.headers or not response.headers['cache-control']:
            headers['cache-control'] = 'max-age={0:d}'.format(self.days * 24 * 60 * 60)
        elif 'max-age' not in response.headers['cache-control'] and 'no-cache' not in response.headers['cache-control'] and 'no-store' not in response.headers['cache-control']:
            headers['cache-control'] = response.headers['cache-control'] + ', max-age={0:d}'.format(self.days * 24 * 60 * 60)
        return headers

    def warning(self, response):
        if 'cache-control' not in response.headers or not response.headers['cache-control'] or 'max-age' not in response.headers['cache-control'] and 'no-cache' not in response.headers['cache-control'] and 'no-store' not in response.headers['cache-control']:
            return '110 - "If this is not fresh, then it is stale."'

class ProviderError(Exception):
    def __init__(self, message, cause=None):
        super(ProviderError, self).__init__(message)
        self.cause = cause
