import os
import re
import threading
import urllib
try:
    import urllib.parse as urlparse
except ImportError: # py2
    import urlparse
import xbmc
import xbmcvfs
from contextlib import closing

from lib import cleaner
from lib.libs import mediainfo as info, mediatypes, pykodi, quickjson, utils
from lib.libs.addonsettings import settings
from lib.libs.pykodi import localize as L, log
from lib.libs.webhelper import Getter, GetterError

CANT_CONTACT_PROVIDER = 32034
HTTP_ERROR = 32035
CANT_WRITE_TO_FILE = 32037
REMOTE_CONTROL_REQUIRED = 32039

FILEERROR_LIMIT = 3
PROVIDERERROR_LIMIT = 3

TEMP_DIR = 'special://temp/recycledartwork/'

typemap = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/gif': 'gif'}

# REVIEW: Deleting replaced artwork. If [movie base name]-fanart.jpg exists and AB is
#  configured for fanart.jpg, downloading a new artwork will save to the short name but
#  leave the long name, and the next scan will pick up the long name.
#  ditto scanning 'logo.png' at first and saving new 'clearlogo.png', but clearlogo will be picked
#  first by the next scan so that's not such a big deal.

class FileManager(object):
    def __init__(self, debug=False, bigcache=False):
        self.getter = Getter()
        self.getter.session.headers['User-Agent'] = settings.useragent
        self.size = 0
        self.fileerror_count = 0
        self.provider_errors = {}
        self.debug = debug
        self.alreadycached = None if not bigcache else []
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
            protocol = 'https' if secure else 'http'
            self.imagecachebase = '{0}://{1}localhost:{2}/image/'.format(protocol, username, port)
        else:
            self.imagecachebase = None
            log(L(REMOTE_CONTROL_REQUIRED), xbmc.LOGWARNING)

    def downloadfor(self, mediaitem, allartwork=True):
        if self.fileerror_count >= FILEERROR_LIMIT:
            return False, ''
        if not info.can_saveartwork(mediaitem):
            return False, ''
        to_download = get_downloadable_art(mediaitem, allartwork)
        if not to_download:
            return False, ''
        services_hit = False
        error = ''
        localfiles = get_local_art(mediaitem, allartwork)
        for arttype, url in to_download.items():
            hostname = urlparse.urlparse(url).netloc
            if self.provider_errors.get(hostname, 0) >= PROVIDERERROR_LIMIT:
                continue
            full_basefilepath = info.build_artwork_basepath(mediaitem, arttype)
            if not full_basefilepath:
                continue
            if self.debug:
                mediaitem.downloadedart[arttype] = full_basefilepath + '.ext'
                continue
            result, err = self.doget(url)
            if err:
                error = err
                self.provider_errors[hostname] = self.provider_errors.get(hostname, 0) + 1
                continue
            if not result:
                # 404 URL dead, wipe it so we can add another one later
                mediaitem.downloadedart[arttype] = None
                continue
            self.size += int(result.headers.get('content-length', 0))
            services_hit = True
            ext = get_file_extension(result.headers.get('content-type'), url)
            if not ext:
                log("Can't determine extension for '{0}'\nfor image type '{1}'".format(url, arttype))
                continue
            full_basefilepath += '.' + ext
            if xbmcvfs.exists(full_basefilepath):
                if extrafanart_name_used(full_basefilepath, localfiles):
                    # REVIEW: can this happen in any other circumstance?
                    full_basefilepath = get_next_filename(full_basefilepath, localfiles)
                    localfiles.append(full_basefilepath)
                if xbmcvfs.exists(full_basefilepath) and settings.recycle_removed:
                    recyclefile(full_basefilepath)
            else:
                folder = os.path.dirname(full_basefilepath)
                if not xbmcvfs.exists(folder):
                    xbmcvfs.mkdirs(folder)
            # For now this just downloads the whole thing in memory, then saves it to file.
            #  Maybe chunking it will be better when GIFs are handled
            file_ = xbmcvfs.File(full_basefilepath, 'wb')
            with closing(file_):
                if not file_.write(result.content):
                    self.fileerror_count += 1
                    raise FileError(L(CANT_WRITE_TO_FILE).format(full_basefilepath))
                self.fileerror_count = 0
            mediaitem.downloadedart[arttype] = full_basefilepath
            log("downloaded '{0}'\nto image file '{1}'".format(url, full_basefilepath))
        return services_hit, error

    def doget(self, url, **kwargs):
        try:
            result = self.getter(url, **kwargs)
            if not result and url.startswith('http://'):
                # Try https, the browser "that totally shows this image" probably is, even if no redirect
                result, err = self.doget('https://' + url[7:])
                if err or not result:
                    result = None
            return result, None
        except GetterError as ex:
            message = L(CANT_CONTACT_PROVIDER) if ex.connection_error else L(HTTP_ERROR).format(ex.message)
            return None, message

    def remove_deselected_files(self, mediaitem, assignedart=False):
        if self.debug:
            return
        for arttype, newimage in mediaitem.selectedart.iteritems():
            if newimage is not None:
                continue
            if assignedart:
                oldimage = mediaitem.art.get(arttype)
            else:
                oldimage = mediaitem.forcedart.get(arttype)
            if not oldimage:
                continue
            old_url = oldimage['url'] if isinstance(oldimage, dict) else \
                oldimage if isinstance(oldimage, basestring) else oldimage[0]['url']
            if not old_url or old_url.startswith(pykodi.notimagefiles) \
            or old_url in mediaitem.selectedart.values() or not xbmcvfs.exists(old_url):
                continue
            if settings.recycle_removed:
                recyclefile(old_url)
            xbmcvfs.delete(old_url)

    def set_bigcache(self):
        if self.alreadycached is None:
            self.alreadycached = []

    def cachefor(self, artmap, multiplethreads=False):
        if not self.imagecachebase or self.debug:
            return 0
        urls = [url for url in artmap.values() if url and not url.startswith(('http', 'image'))]
        if not urls:
            return 0
        if self.alreadycached is not None:
            if not self.alreadycached:
                self.alreadycached = [pykodi.unquoteimage(texture['url']) for texture in quickjson.get_textures()
                    if not pykodi.unquoteimage(texture['url']).startswith(('http', 'image'))]
            alreadycached = self.alreadycached
        else:
            alreadycached = [pykodi.unquoteimage(texture['url']) for texture in quickjson.get_textures(urls)]
        count = [0]
        def worker(path):
            try:
                res, _ = self.doget(self.imagecachebase + urllib.quote(pykodi.quoteimage(path), ''), stream=True)
                if res:
                    res.iter_content(chunk_size=1024)
                    res.close()
                    count[0] += 1
            except GetterError:
                pass
        threads = []
        for path in urls:
            if path in alreadycached:
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

def extrafanart_name_used(path, localfiles):
    return utils.parent_dir(path) == 'extrafanart' and path in localfiles

def get_file_extension(contenttype, request_url, re_search=re.compile(r'\.\w*$')):
    if contenttype in typemap:
        return typemap[contenttype]
    if re.search(re_search, request_url):
        return request_url.rsplit('.', 1)[1]

def get_next_filename(full_basefilepath, localfiles):
    nextname = full_basefilepath
    char_int = 97
    while nextname in localfiles:
        name, ext = os.path.splitext(full_basefilepath)
        nextname = name + chr(char_int) + ext
        char_int += 1
    return nextname

def get_downloadable_art(mediaitem, allartwork):
    if allartwork:
        downloadable = dict(mediaitem.art)
        downloadable.update(mediaitem.selectedart)
    else:
        downloadable = dict(mediaitem.selectedart)
    for arttype in list(downloadable):
        if not downloadable[arttype] or not downloadable[arttype].startswith('http') or \
                not mediatypes.downloadartwork(mediaitem.mediatype, arttype):
            del downloadable[arttype]
    return downloadable

def get_local_art(mediaitem, allartwork):
    local = []
    if allartwork:
        arts = mediaitem.art if settings.clean_imageurls else \
            cleaner.clean_artwork(mediaitem) # library URLs not cleaned, but can still help here
        for url in arts.values():
            if url and not url.startswith('http'):
                local.append(url)
    for url in mediaitem.selectedart.values():
        if url and not url.startswith('http'):
            local.append(url)

    return local

def recyclefile(filename):
    firstdir = utils.parent_dir(filename)
    directory = TEMP_DIR
    pathsep = utils.get_pathsep(directory)
    if firstdir in ('extrafanart', 'extrathumbs'):
        directory += utils.parent_dir(os.path.dirname(filename)) + pathsep
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
