import os
import xbmcvfs
from abc import ABCMeta

from lib.libs import mediatypes
from lib.libs.addonsettings import settings
from lib.libs.mediainfo import arttype_matches_base, format_arttype, find_central_infodir
from lib.libs.utils import SortedDisplay, natural_sort, get_movie_path_list, get_pathsep, \
    iter_possible_cleannames, parent_dir

ARTWORK_EXTS = ('.jpg', '.png', '.gif')
ARTIST_INFOFOLDER_PROVIDER = SortedDisplay('file:art', 20223)

ARTTYPE_MAXLENGTH = 30

class ArtFilesAbstractProvider(object):
    __metaclass__ = ABCMeta
    # 13514 = Local art
    name = SortedDisplay('file:art', 13514)

    def buildimage(self, url, title, fromartistfolder=False):
        provider = ARTIST_INFOFOLDER_PROVIDER if fromartistfolder else self.name
        result = {'url': url, 'provider': provider, 'preview': url}
        result['title'] = title
        result['rating'] = SortedDisplay(0, '')
        result['size'] = SortedDisplay(0, '')
        result['language'] = 'xx'
        return result

    def getextra(self, path, exacttypes, thumbs=False):
        arttype = 'thumb' if thumbs else 'fanart'
        extradir = 'extrathumbs' if thumbs else 'extrafanart'
        sep = get_pathsep(path)
        missing, nextno = getopentypes(exacttypes, arttype)
        path += extradir + sep
        _, files = xbmcvfs.listdir(path)
        files.sort(key=natural_sort)
        result = {}
        for filename in files:
            check_filename = filename.lower()
            if not check_filename.endswith(ARTWORK_EXTS):
                continue
            popped = missing.pop(0) if missing else None
            nexttype = popped if popped else format_arttype(arttype, nextno)
            result[nexttype] = self.buildimage(path + filename, extradir + sep + filename)
            if not popped:
                nextno += 1
        return result

class ArtFilesSeriesProvider(ArtFilesAbstractProvider):
    mediatype = mediatypes.TVSHOW

    alttypes = {'logo': 'clearlogo', 'character': 'characterart'}

    def get_exact_images(self, mediaitem):
        path = mediaitem.file
        dirs, files = xbmcvfs.listdir(path)
        files.sort(key=natural_sort)
        result = {}
        for filename in files:
            check_filename = filename.lower()
            if not check_filename.endswith(ARTWORK_EXTS):
                continue
            basefile = os.path.splitext(check_filename)[0]
            if '.' in basefile or ' ' in basefile:
                continue
            if basefile.startswith('season') and basefile.count('-'):
                seasonsplit = basefile.split('-')
                if len(seasonsplit) == 3:
                    if seasonsplit[1] not in ('specials', 'all'):
                        continue
                    number = 0 if seasonsplit[1] == 'specials' else -1
                    arttype = seasonsplit[2]
                elif len(seasonsplit) == 2:
                    try:
                        number = int(seasonsplit[0].replace('season', ''))
                    except ValueError:
                        continue
                    arttype = seasonsplit[1]
                else:
                    continue
                if not arttype.isalnum():
                    continue
                arttype = 'season.{0}.{1}'.format(number, arttype)
            else:
                if not basefile.isalnum() or len(basefile) > ARTTYPE_MAXLENGTH:
                    continue
                arttype = basefile
                if settings.identify_alternatives and arttype in self.alttypes.keys():
                    arttype = self.alttypes[arttype]
                    if arttype in result.keys():
                        continue
            result[arttype] = self.buildimage(path + filename, filename)

        if dirs and 'extrafanart' in dirs:
                result.update(self.getextra(path, result.keys()))

        return result

class ArtFilesMovieProvider(ArtFilesAbstractProvider):
    mediatype = mediatypes.MOVIE

    alttypes = {'logo': 'clearlogo', 'disc': 'discart'}

    def get_exact_images(self, mediaitem):
        path = mediaitem.file
        paths = get_movie_path_list(path)
        result = {}
        sep = get_pathsep(path)
        path = os.path.dirname(paths[0]) + sep
        havespecific = []
        for dirname, moviefile in (os.path.split(p) for p in paths):
            dirname += sep
            check_moviebase = os.path.splitext(moviefile)[0].lower()
            dirs, files = xbmcvfs.listdir(dirname)
            for filename in files:
                check_filename = filename.lower()
                if not check_filename.endswith(ARTWORK_EXTS):
                    continue
                imagefile = os.path.splitext(check_filename)[0]
                specific = False
                if '-' in imagefile:
                    firstbit, imagefile = imagefile.rsplit('-', 1)
                    if firstbit != check_moviebase:
                        continue
                    specific = True
                if not imagefile.isalnum() or len(imagefile) > ARTTYPE_MAXLENGTH:
                    continue
                arttype = imagefile
                if settings.identify_alternatives and arttype in self.alttypes.keys():
                    arttype = self.alttypes[arttype]
                    if arttype in result.keys():
                        continue
                if specific or arttype not in havespecific:
                    result[arttype] = self.buildimage(dirname + filename, filename)
                if specific:
                    havespecific.append(arttype)

            if dirs:
                if 'extrafanart' in dirs:
                    result.update(self.getextra(path, result.keys()))
                if 'extrathumbs' in dirs:
                    result.update(self.getextra(path, result.keys(), True))

        return result

class ArtFilesMovieSetProvider(ArtFilesAbstractProvider):
    mediatype = mediatypes.MOVIESET

    alttypes = {'logo': 'clearlogo', 'folder': 'thumb'}

    def get_exact_images(self, mediaitem):
        path, inputfilename = os.path.split(mediaitem.file)
        sep = get_pathsep(path)
        path += sep
        dirs, files = xbmcvfs.listdir(path)
        check_inputbase = os.path.splitext(inputfilename)[0] if inputfilename else ''
        result = {}
        if inputfilename:
            dirname = next((name for name in dirs if name in iter_possible_cleannames(check_inputbase)), None)
            if dirname: # '[centraldir]/[set name]/[arttype].[ext]'
                dirname = path + dirname + sep
                _, dfiles = xbmcvfs.listdir(dirname)
                for filename in dfiles:
                    if not filename.endswith(ARTWORK_EXTS):
                        continue
                    arttype = os.path.splitext(filename)[0]
                    if not arttype.isalnum() or len(arttype) > ARTTYPE_MAXLENGTH:
                        continue
                    if settings.identify_alternatives and arttype in self.alttypes.keys():
                        arttype = self.alttypes[arttype]
                        if arttype in result.keys():
                            continue

                    result[arttype] = self.buildimage(dirname + filename, filename)

        if not result:
            for filename in files:
                if not filename.endswith(ARTWORK_EXTS):
                    continue
                basefile = os.path.splitext(filename)[0]
                if check_inputbase: # '[centraldir]/[set name]-[arttype].[ext]'
                    if '-' not in basefile:
                        continue
                    firstbit, arttype = basefile.rsplit('-', 1)
                    if not arttype.isalnum() or firstbit not in iter_possible_cleannames(check_inputbase):
                        continue
                else: # parent of movie directory
                    if not basefile.isalnum() or len(basefile) > ARTTYPE_MAXLENGTH:
                        continue
                    arttype = basefile

                if settings.identify_alternatives and arttype in self.alttypes.keys():
                    arttype = self.alttypes[arttype]
                    if arttype in result.keys():
                        continue

                result[arttype] = self.buildimage(path + filename, filename)
        return result

class ArtFilesEpisodeProvider(ArtFilesAbstractProvider):
    mediatype = mediatypes.EPISODE

    def get_exact_images(self, mediaitem):
        path, inputfilename = os.path.split(mediaitem.file)
        path += get_pathsep(path)
        _, files = xbmcvfs.listdir(path)
        check_inputbase = os.path.splitext(inputfilename)[0].lower()
        result = {}
        for filename in files:
            check_filename = filename.lower()
            if not check_filename.endswith(ARTWORK_EXTS):
                continue
            basefile = os.path.splitext(check_filename)[0]
            if '-' not in basefile:
                continue
            firstbit, arttype = basefile.rsplit('-', 1)
            if firstbit != check_inputbase or not arttype.isalnum():
                continue

            result[arttype] = self.buildimage(path + filename, filename)
        return result

class ArtFilesMusicVideoProvider(ArtFilesAbstractProvider):
    mediatype = mediatypes.MUSICVIDEO

    alttypes = {'logo': 'clearlogo', 'disc': 'discart', 'cdart': 'discart'}

    def get_exact_images(self, mediaitem):
        path, inputfilename = os.path.split(mediaitem.file)
        path += get_pathsep(path)
        dirs, files = xbmcvfs.listdir(path)
        check_inputbase = os.path.splitext(inputfilename)[0].lower()
        paths = get_movie_path_list(path)
        result = {}
        sep = get_pathsep(path)
        path = os.path.dirname(paths[0]) + sep
        havespecific = []
        for filename in files:
            check_filename = filename.lower()
            if not check_filename.endswith(ARTWORK_EXTS):
                continue
            basefile = os.path.splitext(check_filename)[0]
            specific = False
            if '-' in basefile:
                firstbit, basefile = basefile.rsplit('-', 1)
                if firstbit != check_inputbase:
                    continue
                specific = True
            if not basefile.isalnum() or len(basefile) > ARTTYPE_MAXLENGTH:
                continue
            arttype = basefile
            if settings.identify_alternatives and arttype in self.alttypes.keys():
                arttype = self.alttypes[arttype]
                if arttype in result.keys():
                    continue
            if specific or arttype not in havespecific:
                result[arttype] = self.buildimage(path + filename, filename)
            if specific:
                havespecific.append(arttype)

        if dirs:
            if 'extrafanart' in dirs:
                result.update(self.getextra(path, result.keys()))
            if 'extrathumbs' in dirs:
                result.update(self.getextra(path, result.keys(), True))

        return result

class ArtFilesArtistProvider(ArtFilesAbstractProvider):
    mediatype = mediatypes.ARTIST

    alttypes = {'folder': 'thumb', 'logo': 'clearlogo'}

    def get_exact_images(self, mediaitem):
        path = find_central_infodir(mediaitem)
        if not path:
            return {}
        _, files = xbmcvfs.listdir(path)
        result = {}
        for filename in files:
            check_filename = filename.lower()
            if not check_filename.endswith(ARTWORK_EXTS):
                continue
            arttype = os.path.splitext(check_filename)[0]
            if not arttype.isalnum() or len(arttype) > ARTTYPE_MAXLENGTH:
                continue
            if settings.identify_alternatives and arttype in self.alttypes.keys():
                arttype = self.alttypes[arttype]
                if arttype in result.keys():
                    continue
            result[arttype] = self.buildimage(path + filename, filename, True)
        return result

class ArtFilesAlbumProvider(ArtFilesArtistProvider):
    mediatype = mediatypes.ALBUM

    alttypes = {'folder': 'thumb', 'cover': 'thumb', 'disc': 'discart', 'cdart': 'discart'}

    def get_exact_images(self, mediaitem):
        paths = (mediaitem.file, find_central_infodir(mediaitem))
        if settings.albumartwithmediafiles:
            paths = (paths[1], paths[0])
        result = {}
        for path in paths:
            if not path:
                continue
            _, files = xbmcvfs.listdir(path)
            for filename in files:
                check_filename = filename.lower()
                if not check_filename.endswith(ARTWORK_EXTS):
                    continue
                arttype = os.path.splitext(check_filename)[0]
                if not arttype.isalnum() or len(arttype) > ARTTYPE_MAXLENGTH:
                    continue
                if settings.identify_alternatives and arttype in self.alttypes.keys():
                    arttype = self.alttypes[arttype]
                    if arttype in result.keys():
                        continue
                result[arttype] = self.buildimage(path + filename, filename, path != mediaitem.file)

        for disc in sorted(mediaitem.discfolders.keys()):
            path = mediaitem.discfolders[disc]
            _, files = xbmcvfs.listdir(path)
            for filename in files:
                check_filename = filename.lower()
                if not check_filename.endswith(ARTWORK_EXTS):
                    continue
                arttype = os.path.splitext(check_filename)[0]
                if not arttype.isalnum() or len(arttype) > ARTTYPE_MAXLENGTH:
                    continue
                if settings.identify_alternatives and arttype in self.alttypes.keys():
                    arttype = self.alttypes[arttype]
                parentdir = parent_dir(path) + get_pathsep(path)
                if arttype == 'discart':
                    if 'discart' not in result:
                        result['discart'] = self.buildimage(path + filename, parentdir + filename)
                    if not disc:
                        continue
                    arttype += str(disc)
                if arttype in result:
                    continue
                result[arttype] = self.buildimage(path + filename, parentdir + filename)

        return result

class ArtFilesSongProvider(ArtFilesAbstractProvider):
    mediatype = mediatypes.SONG

    def get_exact_images(self, mediaitem):
        paths = (mediaitem.file, find_central_infodir(mediaitem))
        if not paths[0] and not paths[1]:
            return {}
        if settings.albumartwithmediafiles:
            paths = (paths[1], paths[0])
        if mediaitem.file:
            check_inputbase = os.path.splitext(os.path.basename(mediaitem.file))[0].lower()
        result = {}
        for path in paths:
            if not path:
                continue
            centraldir = path != mediaitem.file
            path = os.path.dirname(path) + get_pathsep(path)
            _, files = xbmcvfs.listdir(path)
            for filename in files:
                check_filename = filename.lower()
                if not check_filename.endswith(ARTWORK_EXTS):
                    continue
                basefile = os.path.splitext(check_filename)[0]
                if '-' not in basefile:
                    continue
                firstbit, arttype = basefile.rsplit('-', 1)
                if not arttype.isalnum():
                    continue
                if not centraldir and firstbit != check_inputbase:
                    continue
                if centraldir and firstbit not in (i.lower() for i in iter_possible_cleannames(mediaitem.label)):
                    continue
                result[arttype] = self.buildimage(path + filename, filename, centraldir)
        return result

def getopentypes(existingtypes, arttype):
    keys = [exact for exact in sorted(existingtypes, key=natural_sort)
        if arttype_matches_base(arttype, exact)]
    missing = []
    nextstart = 0
    for count in xrange(100):
        if not keys:
            nextstart = count
            break
        exact = format_arttype(arttype, count)
        if exact in keys:
            keys.remove(exact)
        else:
            missing.append(exact)
    return missing, nextstart
