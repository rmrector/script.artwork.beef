import requests
import StorageServer
import sys
import xbmc
from abc import ABCMeta, abstractmethod
from requests import codes
from requests.exceptions import HTTPError, Timeout

from devhelper.pykodi import log

from requests.packages import urllib3
urllib3.disable_warnings()

import providers
from utils import SortedDisplay

cache = StorageServer.StorageServer('script.artwork.beef', 72)

# Result dict of lists, keyed on art type
# {'url': URL, 'language': ISO alpha-2 code, 'rating': SortedDisplay, 'size': SortedDisplay, 'provider': self.name, 'preview': preview URL}
# 'title': optional image title
# 'subtype': optional image subtype, like disc dvd/bluray/3d, SortedDisplay
# language should be None if there is no title on the image

class AbstractProvider(object):
    __metaclass__ = ABCMeta

    name = SortedDisplay(0, '')
    mediatype = None

    monitor = xbmc.Monitor()

    def __init__(self):
        self.contenttype = None
        self.session = requests.Session()

    def set_accepted_contenttype(self, contenttype):
        self.session.headers['Accept'] = contenttype
        self.contenttype = contenttype

    def doget(self, url, params=None, headers=None):
        result = self._inget(url, params, headers)
        if result == None:
            return
        errcount = 0
        if result.status_code == codes.unauthorized:
            if self.login():
                result = self._inget(url, params, headers)
                if result is None:
                    return
        while result.status_code == codes.too_many_requests:
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

        if result.status_code == codes.not_found:
            return
        try:
            result.raise_for_status()
        except HTTPError:
            raise ProviderError, (sys.exc_info()[1].message, sys.exc_info()[1]), sys.exc_info()[2]
        if not result.headers['Content-Type'].startswith(self.contenttype):
            raise ProviderError, "Provider returned unexected content", sys.exc_info()[2]
        return result

    def _inget(self, url, params=None, headers=None, timeout=15):
        finalheaders = {'User-Agent': providers.useragent}
        if headers:
            finalheaders.update(headers)
        try:
            return self.session.get(url, params=params, headers=finalheaders, timeout=timeout)
        except Timeout:
            try:
                return self.session.get(url, params=params, headers=finalheaders, timeout=timeout)
            except Timeout as ex:
                raise ProviderError, ("Provider is not responding", ex), sys.exc_info()[2]

    def log(self, message, level=xbmc.LOGDEBUG):
        log(message, level, tag='%s.%s' % (self.name.sort, self.mediatype))

    def login(self):
        return False

    @abstractmethod
    def get_images(self, mediaid, types=None):
        pass

class ProviderError(Exception):
    def __init__(self, message, cause=None):
        super(ProviderError, self).__init__(message)
        self.cause = cause
