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

TEMP_DIR = 'special://temp/recycledartwork/'

typemap = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/gif': 'gif'}
# REVIEW: there may be other protocols that just can't be written to
blacklisted_protocols = ('plugin', 'http')

class FileManager(object):
    def __init__(self):
        self.getter = Getter()
        self.getter.session.headers['User-Agent'] = settings.useragent
        self.size = 0
        self.alreadycached = None
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
        if allartwork:
            nowart = dict(mediaitem.art)
            nowart.update(mediaitem.selectedart)
        else:
            nowart = dict(mediaitem.selectedart)
        for arttype in list(nowart):
            if not info.keep_arttype(mediaitem.mediatype, arttype, nowart[arttype]):
                del nowart[arttype]
        if not info.has_art_todownload(nowart):
            return False, ''
        path = basefile = mediaitem.file if settings.albumartwithmediafiles \
                and mediaitem.mediatype in (mediatypes.ALBUM, mediatypes.SONG) and mediaitem.file \
            else info.find_central_infodir(mediaitem, True)
        if basefile and mediaitem.mediatype in (mediatypes.EPISODE, mediatypes.SONG):
            path = os.path.dirname(basefile) + utils.get_pathsep(basefile)
        if not basefile:
            if not mediaitem.file:
                return False, ''
            path = utils.get_movie_path_list(mediaitem.file)[0] \
                if mediaitem.mediatype == mediatypes.MOVIE else mediaitem.file
            if path.startswith(blacklisted_protocols):
                return False, ''
            basefile = os.path.splitext(path)[0]
            if remove_basename(mediaitem.mediatype):
                path = basefile = os.path.dirname(basefile) + utils.get_pathsep(basefile)
        services_hit = False
        error = None
        def st(num):
            return '-specials' if num == 0 else '-all' if num == -1 else '{0:02d}'.format(num)
        seasonpre = None if mediaitem.mediatype != mediatypes.SEASON else 'season{0}-'.format(st(mediaitem.season))
        if save_extrafanart(mediaitem, nowart):
            extrafanartdir = os.path.dirname(basefile) + utils.get_pathsep(basefile) \
                if mediaitem.mediatype in (mediatypes.MOVIE, mediatypes.MUSICVIDEO) else basefile
            extrafanartdir += 'extrafanart' + utils.get_pathsep(basefile)
            if not xbmcvfs.exists(extrafanartdir):
                xbmcvfs.mkdir(extrafanartdir)
        for arttype, url in nowart.iteritems():
            if not url or not url.startswith('http'):
                continue
            if seasonpre:
                type_for_file = seasonpre + arttype
            elif arttype.startswith('season.'):
                _, num, sarttype = arttype.split('.')
                type_for_file = 'season{0}-{1}'.format(st(int(num)), sarttype)
            else:
                type_for_file = arttype
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
            if save_thisextrafanart(arttype, mediaitem.mediatype):
                filename = extrafanartdir + type_for_file + '.' + ext
            else:
                sep = '' if basefile == path else '-'
                filename = basefile + sep + type_for_file + '.' + ext
            if xbmcvfs.exists(filename) and settings.recycle_removed:
                recyclefile(filename)
            # For now this just downloads the whole thing in memory, then saves it to file.
            #  Maybe chunking it will be better when GIFs are handled
            file_ = xbmcvfs.File(filename, 'wb')
            with closing(file_):
                if not file_.write(result.content):
                    raise FileError(L(CANT_WRITE_TO_FILE).format(filename))
            mediaitem.downloadedart[arttype] = filename
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
    if firstdir in ('extrafanart', 'extrathumbs'):
        directory += os.path.basename(os.path.dirname(os.path.dirname(filename))) + '/'
    directory += firstdir
    if not xbmcvfs.exists(directory):
        xbmcvfs.mkdirs(directory)
    recycled_filename = directory + '/' + os.path.basename(filename)
    if not xbmcvfs.copy(filename, recycled_filename):
        raise FileError(L(CANT_WRITE_TO_FILE).format(recycled_filename))

def save_extrafanart(mediaitem, allart):
    return _saveextra_thistype(mediaitem.mediatype) \
        and any(1 for art in allart if info.arttype_matches_base(art, 'fanart') and info.split_arttype(art)[1] > 0)

def save_thisextrafanart(arttype, mediatype):
    return _saveextra_thistype(mediatype) and info.arttype_matches_base(arttype, 'fanart') and info.split_arttype(arttype)[1] > 0

def _saveextra_thistype(mediatype):
    return settings.save_extrafanart and mediatype in (mediatypes.MOVIE, mediatypes.TVSHOW) \
        or settings.save_extrafanart_mvids and mediatype == mediatypes.MUSICVIDEO

def remove_basename(mediatype):
    return mediatype == mediatypes.MOVIE and not settings.savewith_basefilename \
    or mediatype == mediatypes.MUSICVIDEO and not settings.savewith_basefilename_mvids

class FileError(Exception):
    def __init__(self, message, cause=None):
        super(FileError, self).__init__()
        self.cause = cause
        self.message = message
