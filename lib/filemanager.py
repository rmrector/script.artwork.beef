import os
import re
import threading
import urllib
import xbmcvfs
from contextlib import closing
from requests.exceptions import HTTPError, Timeout, ConnectionError, RequestException

from lib.libs import mediainfo as info, mediatypes, pykodi, quickjson, utils
from lib.libs.addonsettings import settings
from lib.libs.pykodi import localize as L, notlocalimages
from lib.libs.webhelper import Getter

CANT_CONTACT_PROVIDER = 32034
HTTP_ERROR = 32035
CANT_WRITE_TO_FILE = 32037

FILEERROR_LIMIT = 3

TEMP_DIR = 'special://temp/recycledartwork/'

typemap = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/gif': 'gif'}
# REVIEW: there may be other protocols that just can't be written to
#  xbmcvfs.mkdirs only supports local drives, SMB, and NFS
blacklisted_protocols = ('plugin', 'http')

class FileManager(object):
    def __init__(self):
        self.getter = Getter()
        self.getter.session.headers['User-Agent'] = settings.useragent
        self.size = 0
        self.alreadycached = None
        self.fileerror_count = 0
        self._build_imagecachebase()

    def _build_imagecachebase(self):
        result = pykodi.execute_jsonrpc({"jsonrpc": "2.0", "id": 1, "method": "Settings.GetSettings",
            "params": {"filter": {"category": "control", "section": "services"}}})
        port = 80
        username = ''
        password = ''
        secure = False
        server_enabled = True
        if result.get('result', {}).get('settings'):
            for setting in result['result']['settings']:
                if setting['id'] == 'services.webserver' and not setting['value']:
                    server_enabled = False
                    break
                if setting['id'] == 'services.webserverusername':
                    username = setting['value']
                elif setting['id'] == 'services.webserverport':
                    port = setting['value']
                elif setting['id'] == 'services.webserverpassword':
                    password = setting['value']
                elif setting['id'] == 'services.webserverssl' and setting['value']:
                    secure = True
            username = '{0}:{1}@'.format(username, password) if username and password else ''
        else:
            server_enabled = False
        if server_enabled:
            self.imagecachebase = 'https' if secure else 'http'
            self.imagecachebase += '://{0}localhost:{1}/image/'.format(username, port)
        else:
            self.imagecachebase = None

    def downloadfor(self, mediaitem, allartwork=True):
        if self.fileerror_count >= FILEERROR_LIMIT:
            return False, ''
        if allartwork:
            nowart = dict(mediaitem.art)
            nowart.update(mediaitem.selectedart)
        else:
            nowart = dict(mediaitem.selectedart)
        for arttype in list(nowart):
            if not nowart[arttype] or not nowart[arttype].startswith('http') or \
                    not mediatypes.downloadartwork(mediaitem.mediatype, arttype):
                del nowart[arttype]
        if not nowart or not info.can_saveartwork(mediaitem):
            return False, ''
        services_hit = False
        error = ''
        for arttype, url in nowart.iteritems():
            result, err = self.doget(url)
            if err:
                error = err
                continue
            if not result:
                # 404 URL dead, wipe it so we can add another one later
                mediaitem.downloadedart[arttype] = None
                continue
            self.size += int(result.headers.get('content-length', 0))
            services_hit = True
            contenttype = result.headers.get('content-type')
            if contenttype in typemap:
                ext = typemap[contenttype]
            else:
                if not re.search(r'\.\w*$', url):
                    continue
                ext = url.rsplit('.', 1)[1]
            full_basefilepath = info.build_artwork_basepath(mediaitem, arttype, True)
            if not full_basefilepath:
                continue
            full_basefilepath += '.' + ext
            if xbmcvfs.exists(full_basefilepath) and settings.recycle_removed:
                recyclefile(full_basefilepath)
            else:
                folder = os.path.dirname(full_basefilepath)
                if not xbmcvfs.exists(folder) and not xbmcvfs.mkdirs(folder):
                    self.fileerror_count += 1
                    raise FileError(L(CANT_WRITE_TO_FILE).format(full_basefilepath))
            # For now this just downloads the whole thing in memory, then saves it to file.
            #  Maybe chunking it will be better when GIFs are handled
            file_ = xbmcvfs.File(full_basefilepath, 'wb')
            with closing(file_):
                if not file_.write(result.content):
                    self.fileerror_count += 1
                    raise FileError(L(CANT_WRITE_TO_FILE).format(full_basefilepath))
                self.fileerror_count = 0
            mediaitem.downloadedart[arttype] = full_basefilepath
        return services_hit, error

    def doget(self, url, **kwargs):
        try:
            return self.getter(url, **kwargs), None
        except (Timeout, ConnectionError) as ex:
            return None, L(CANT_CONTACT_PROVIDER)
        except HTTPError as ex:
            message = ex.response.reason if ex.response else type(ex).__name__
            return None, L(HTTP_ERROR).format(message)
        except RequestException as ex:
            return None, L(HTTP_ERROR).format(type(ex).__name__)

    def remove_deselected_files(self, mediaitem):
        for arttype, newimage in mediaitem.selectedart.iteritems():
            if newimage is not None:
                continue
            oldimage = mediaitem.forcedart.get(arttype)
            if not oldimage:
                continue
            old_url = oldimage['url'] if isinstance(oldimage, dict) else oldimage[0]['url']
            if not old_url or old_url.startswith(notlocalimages) \
            or old_url in mediaitem.selectedart.itervalues():
                continue
            if settings.recycle_removed:
                recyclefile(old_url)
            xbmcvfs.delete(old_url)

    def cachefor(self, artmap, multiplethreads=True):
        if not self.imagecachebase:
            return 0
        if self.alreadycached is None:
            self.alreadycached = [pykodi.unquoteimage(texture['url']) for texture in quickjson.get_textures()
                if not pykodi.unquoteimage(texture['url']).startswith('http')]
        count = [0]
        def worker(path):
            try:
                res, _ = self.doget(self.imagecachebase + urllib.quote(pykodi.quoteimage(path), ''), stream=True)
                if res:
                    res.iter_content(chunk_size=1024)
                    res.close()
                    count[0] += 1
            except HTTPError:
                pass # caching error, possibly with decoding the original image
            except ConnectionError:
                pass # Kodi is closing
        threads = []
        for path in artmap.itervalues():
            if path.startswith(('http', 'image')) or path in self.alreadycached:
                continue
            if multiplethreads:
                t = threading.Thread(target=worker, args=(path,))
                threads.append(t)
                t.start()
            else:
                worker(path)
        for t in threads:
            t.join()
        return count[0]

def recyclefile(filename):
    firstdir = os.path.basename(os.path.dirname(filename))
    directory = TEMP_DIR
    pathsep = utils.get_pathsep(directory)
    if firstdir in ('extrafanart', 'extrathumbs'):
        directory += os.path.basename(os.path.dirname(os.path.dirname(filename))) + pathsep
    directory += firstdir
    if not xbmcvfs.exists(directory):
        xbmcvfs.mkdirs(directory)
    recycled_filename = directory + pathsep + os.path.basename(filename)
    if not xbmcvfs.copy(filename, recycled_filename):
        raise FileError(L(CANT_WRITE_TO_FILE).format(recycled_filename))

class FileError(Exception):
    def __init__(self, message, cause=None):
        super(FileError, self).__init__()
        self.cause = cause
        self.message = message
