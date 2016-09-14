import os
import re
import xbmcvfs
from abc import ABCMeta

from devhelper import pykodi

import mediatypes
from utils import SortedDisplay, natural_sort, get_movie_path_list

addon = pykodi.get_main_addon()

class ArtFilesAbstractProvider(object):
    __metaclass__ = ABCMeta
    # 13514 = Local art
    name = SortedDisplay('file:art', 13514)

    def __init__(self):
        self.identifyalternatives = addon.get_setting('identify_alternatives')

    def buildimage(self, url, title):
        result = {'url': url, 'provider': self.name, 'preview': url}
        result['title'] = title
        result['rating'] = SortedDisplay(0, '')
        result['size'] = SortedDisplay(0, '')
        result['language'] = 'xx'
        return result

    def getextra(self, path, exacttypes, thumbs=False):
        arttype = 'thumb' if thumbs else 'fanart'
        extradir = 'extrathumbs' if thumbs else 'extrafanart'
        sep = '\\' if '\\' in path else '/'
        missing, nextno = getopentypes(exacttypes, arttype)
        path += extradir + sep
        _, files = xbmcvfs.listdir(path)
        files.sort(key=natural_sort)
        result = {}
        for filename in files:
            if not filename.endswith(('.jpg', '.png', '.gif')):
                continue
            popped = missing.pop(0) if missing else None
            nexttype = popped if popped else arttype + (str(nextno) if nextno else '')
            result[nexttype] = self.buildimage(path + filename, extradir + sep + filename)
            if not popped:
                nextno += 1
        return result

class ArtFilesSeriesProvider(ArtFilesAbstractProvider):
    mediatype = mediatypes.TVSHOW

    alttypes = {'logo': 'clearlogo', 'character': 'characterart'}

    def get_exact_images(self, path):
        dirs, files = xbmcvfs.listdir(path)
        files.sort(key=natural_sort)
        result = {}
        for filename in files:
            if not filename.endswith(('.jpg', '.png', '.gif')):
                continue
            basefile = os.path.splitext(filename)[0]
            if '.' in basefile or ' ' in basefile:
                continue
            if basefile.startswith('season') and basefile.count('-'):
                seasonsplit = basefile.split('-')
                if len(seasonsplit) == 3:
                    number = 0 if seasonsplit[1] == 'specials' else -1
                    arttype = seasonsplit[2]
                elif len(seasonsplit) == 2:
                    try:
                        number = int(seasonsplit[0].replace('season', ''))
                    except ValueError:
                        number = -1
                    arttype = seasonsplit[1]
                else:
                    continue
                arttype = 'season.{0}.{1}'.format(number, arttype)
            else:
                if '-' in filename:
                    continue
                if len(basefile) > 20:
                    continue
                arttype = basefile
                if self.identifyalternatives and arttype in self.alttypes.keys():
                    arttype = self.alttypes[arttype]
                    if arttype in result.keys():
                        continue
            result[arttype] = self.buildimage(path + filename, filename)

        if self.identifyalternatives and dirs:
            if 'extrafanart' in dirs:
                result.update(self.getextra(path, result.keys()))

        return result

class ArtFilesMovieProvider(ArtFilesAbstractProvider):
    mediatype = mediatypes.MOVIE

    alttypes = {'logo': 'clearlogo', 'disc': 'discart'}

    def get_exact_images(self, path):
        paths = get_movie_path_list(path)
        result = {}
        sep = '\\' if '\\' in path else '/'
        for dirname, moviefile in (os.path.split(p) for p in paths):
            dirname += sep
            moviebase = os.path.splitext(moviefile)[0]
            dirs, files = xbmcvfs.listdir(dirname)
            for filename in files:
                if not filename.endswith(('.jpg', '.png', '.gif')):
                    continue
                imagefile = os.path.splitext(filename)[0]
                if '-' in imagefile:
                    firstbit, imagefile = imagefile.rsplit('-', 1)
                    if firstbit != moviebase:
                        continue
                if '.' in imagefile or ' ' in imagefile or len(imagefile) > 20:
                    continue
                arttype = imagefile
                if self.identifyalternatives and arttype in self.alttypes.keys():
                    arttype = self.alttypes[arttype]
                    if arttype in result.keys():
                        continue
                result[arttype] = self.buildimage(dirname + filename, filename)

        if self.identifyalternatives and dirs:
            path = os.path.dirname(path) + sep
            if 'extrafanart' in dirs:
                result.update(self.getextra(path, result.keys()))
            if 'extrathumbs' in dirs:
                result.update(self.getextra(path, result.keys(), True))

        return result

class ArtFilesEpisodeProvider(ArtFilesAbstractProvider):
    mediatype = mediatypes.EPISODE

    def get_exact_images(self, path):
        path, inputfilename = os.path.split(path)
        path += '\\' if '\\' in path else '/'
        _, files = xbmcvfs.listdir(path)
        inputbase = os.path.splitext(inputfilename)[0]
        result = {}
        for filename in files:
            if not filename.endswith(('.jpg', '.png', '.gif')):
                continue
            basefile = os.path.splitext(filename)[0]
            if '-' not in basefile:
                continue
            else:
                firstbit, arttype = basefile.rsplit('-', 1)
                if firstbit != inputbase:
                    continue

            result[arttype] = self.buildimage(path + filename, filename)
        return result

def getopentypes(existingtypes, arttype):
    keys = [exact for exact in sorted(existingtypes, key=natural_sort) if re.match(r'{0}\d*$'.format(arttype), exact)]
    missing = []
    nextstart = 0
    for count in xrange(100):
        if not keys:
            nextstart = count
            break
        exact = arttype + (str(count) if count else '')
        if exact in keys:
            keys.remove(exact)
        else:
            missing.append(exact)
    return missing, nextstart
