import StorageServer
import sys
import xbmc
from abc import ABCMeta, abstractmethod
from requests.exceptions import Timeout, ConnectionError, RequestException
from requests.packages import urllib3

from lib.libs.addonsettings import settings
from lib.libs.pykodi import log, localize as L
from lib.libs.utils import SortedDisplay
from lib.libs.webhelper import Getter

CANT_CONTACT_PROVIDER = 32034
HTTP_ERROR = 32035

urllib3.disable_warnings()

languages = ()

cache = StorageServer.StorageServer('script.artwork.beef', 72)
monitor = xbmc.Monitor()

# Result of `get_images` is dict of lists, keyed on art type
# {'url': URL, 'language': ISO alpha-2 code, 'rating': SortedDisplay, 'size': SortedDisplay, 'provider': self.name, 'preview': preview URL}
# 'title': optional image title
# 'subtype': optional image subtype, like disc dvd/bluray/3d, SortedDisplay
# language should be None if there is no title on the image

class AbstractProvider(object):
    __metaclass__ = ABCMeta

    name = SortedDisplay(0, '')
    mediatype = None
    contenttype = None

    def __init__(self):
        self.getter = Getter(self.contenttype, self.login)
        self.getter.session.headers['User-Agent'] = settings.useragent

    def doget(self, url, **kwargs):
        try:
            return self.getter(url, **kwargs)
        except (Timeout, ConnectionError) as ex:
            raise ProviderError, (L(CANT_CONTACT_PROVIDER), ex), sys.exc_info()[2]
        except RequestException as ex:
            message = ex.response.reason if hasattr(ex, 'response') else \
                ex.message if hasattr(ex, 'message') else type(ex).__name__
            raise ProviderError, (L(HTTP_ERROR).format(message), ex), sys.exc_info()[2]

    def log(self, message, level=xbmc.LOGDEBUG):
        if self.mediatype:
            log(message, level, tag='%s:%s' % (self.name.sort, self.mediatype))
        else:
            log(message, level, tag='%s' % self.name.sort)

    def login(self):
        return False

def build_key_error(provider):
    info = settings.get_apikey_config(provider)
    message = "Invalid project API key: key added in add-on settings is invalid" if not info['builtin'] else \
        "Invalid project API key: built-in key is invalid" if info['apikey'] else \
        "Invalid project API key: installed incorrectly and the built-in key is missing"

    return ProviderError(message)

class AbstractImageProvider(AbstractProvider):
    @abstractmethod
    def get_images(self, uniqueids, types=None):
        pass

class ProviderError(Exception):
    def __init__(self, message, cause=None):
        super(ProviderError, self).__init__(message)
        self.cause = cause
