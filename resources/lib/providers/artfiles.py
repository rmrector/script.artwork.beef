import os
import xbmcvfs
from abc import ABCMeta

import mediatypes
from utils import SortedDisplay, natural_sort, get_movie_path_list

class ArtFilesAbstractProvider(object):
    __metaclass__ = ABCMeta
    # 13514 = Local art
    name = SortedDisplay('file:art', 13514)

class ArtFilesSeriesProvider(ArtFilesAbstractProvider):
    mediatype = mediatypes.TVSHOW

    def get_exact_images(self, path):
        _, files = xbmcvfs.listdir(path)
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

            resultimage = {'url': path + filename, 'provider': self.name, 'preview': path + filename}
            resultimage['title'] = filename
            resultimage['rating'] = SortedDisplay(0, '')
            resultimage['size'] = SortedDisplay(0, '')
            resultimage['language'] = 'xx'
            result[arttype] = resultimage
        return result

class ArtFilesMovieProvider(ArtFilesAbstractProvider):
    mediatype = mediatypes.MOVIE

    def get_exact_images(self, path):
        paths = get_movie_path_list(path)
        result = {}
        for dirname, moviefile in (os.path.split(p) for p in paths):
            dirname += '/'
            moviebase = os.path.splitext(moviefile)[0]
            _, files = xbmcvfs.listdir(dirname)
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
                if arttype not in result:
                    resultimage = {'url': dirname + filename, 'provider': self.name, 'preview': dirname + filename}
                    resultimage['title'] = filename
                    resultimage['rating'] = SortedDisplay(0, '')
                    resultimage['size'] = SortedDisplay(0, '')
                    resultimage['language'] = 'xx'
                    result[arttype] = resultimage
        return result

class ArtFilesEpisodeProvider(ArtFilesAbstractProvider):
    mediatype = mediatypes.EPISODE

    def get_exact_images(self, path):
        path, inputfilename = os.path.split(path)
        path += '/'
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

            resultimage = {'url': path + filename, 'provider': self.name, 'preview': path + filename}
            resultimage['title'] = filename
            resultimage['rating'] = SortedDisplay(0, '')
            resultimage['size'] = SortedDisplay(0, '')
            resultimage['language'] = 'xx'
            result[arttype] = resultimage
        return result
