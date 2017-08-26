import StorageServer
import sys
import xbmc
from abc import ABCMeta, abstractmethod
from requests import codes
from requests.exceptions import HTTPError, Timeout, ConnectionError
from requests.packages import urllib3

from lib.libs.addonsettings import settings
from lib.libs.pykodi import log
from lib.libs.utils import SortedDisplay

urllib3.disable_warnings()

languages = ()

cache = StorageServer.StorageServer('script.artwork.beef', 72)
monitor = xbmc.Monitor()

# Result dict of lists, keyed on art type
# {'url': URL, 'language': ISO alpha-2 code, 'rating': SortedDisplay, 'size': SortedDisplay, 'provider': self.name, 'preview': preview URL}
# 'title': optional image title
# 'subtype': optional image subtype, like disc dvd/bluray/3d, SortedDisplay
# language should be None if there is no title on the image

class AbstractProvider(object):
    __metaclass__ = ABCMeta

    name = SortedDisplay(0, '')
    mediatype = None

    def __init__(self, session):
        self.session = session
        self.getter = Getter(session, self.login)

    def set_accepted_contenttype(self, contenttype):
        self.getter.set_accepted_contenttype(contenttype)

    def doget(self, url, params=None, headers=None):
        return self.getter.get(url, params, headers)

    def log(self, message, level=xbmc.LOGDEBUG):
        log(message, level, tag='%s.%s' % (self.name.sort, self.mediatype))

    def login(self):
        return False

    @abstractmethod
    def get_images(self, mediaid, types=None):
        pass

class Getter(object):
    retryable_errors = (codes['bad_gateway'], codes['internal_server_error'], 520)
    def __init__(self, session, login=lambda: False):
        self.session = session
        self.login = login
        self.contenttype = None
        self.retryon_servererror = False

    def set_accepted_contenttype(self, contenttype):
        self.session.headers['Accept'] = contenttype
        self.contenttype = contenttype

    def get(self, url, params=None, headers=None):
        result = self._inget(url, params, headers)
        if result is None:
            return
        errcount = 0
        while self.retryon_servererror and result.status_code in self.retryable_errors:
            message = 'HTTP error ' + str(result.status_code)
            if errcount > 2:
                raise ProviderError, (message, sys.exc_info()[1]), sys.exc_info()[2]
            log('HTTP 5xx error, retrying in 2s: ' + message)
            errcount += 1
            if monitor.waitForAbort(2):
                return
            result = self._inget(url, params, headers)
        if result.status_code == codes['unauthorized']:
            if self.login():
                result = self._inget(url, params, headers)
                if result is None:
                    return
        errcount = 0
        while result.status_code == codes['too_many_requests']:
            if errcount > 2:
                raise ProviderError, "Too many requests", sys.exc_info()[2]
            errcount += 1
            try:
                wait = int(result.headers.get('Retry-After')) + 1
            except ValueError:
                wait = 10
            if monitor.waitForAbort(wait):
                return
            result = self._inget(url, params, headers)
            if result is None:
                return

        if result.status_code == codes['not_found']:
            return
        try:
            result.raise_for_status()
        except HTTPError:
            raise ProviderError, ('HTTP error ' + str(result.status_code), sys.exc_info()[1]), sys.exc_info()[2]
        if self.contenttype and not result.headers['Content-Type'].startswith(self.contenttype):
            raise ProviderError, "Provider returned unexected content", sys.exc_info()[2]
        return result

    def _inget(self, url, params=None, headers=None, timeout=15):
        finalheaders = {'User-Agent': settings.useragent}
        if headers:
            finalheaders.update(headers)
        try:
            return self.session.get(url, params=params, headers=finalheaders, timeout=timeout)
        except (Timeout, ConnectionError):
            try:
                return self.session.get(url, params=params, headers=finalheaders, timeout=timeout)
            except (Timeout, ConnectionError) as ex:
                raise ProviderError, ("Cannot contact provider", ex), sys.exc_info()[2]

class ProviderError(Exception):
    def __init__(self, message, cause=None):
        super(ProviderError, self).__init__(message)
        self.cause = cause
