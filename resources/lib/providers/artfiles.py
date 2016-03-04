import re
import xbmcvfs
from abc import ABCMeta

import mediatypes
from sorteddisplaytuple import SortedDisplay

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
            basefile = filename.rsplit('.', 1)[0]
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
        if path.count('/'):
            path, inputfilename = path.rsplit('/', 1)
            path = path + '/'
        else:
            path, inputfilename = path.rpslit('\\', 1)
            path = path + '\\'
        _, files = xbmcvfs.listdir(path)
        inputbase = inputfilename.rsplit('.', 1)[0]
        result = {}
        for filename in files:
            if not filename.endswith(('.jpg', '.png', '.gif')):
                continue
            basefile = filename.rsplit('.', 1)[0]
            if '-' in basefile:
                firstbit, basefile = basefile.rsplit('-', 1)
                if firstbit != inputbase:
                    continue
            if '.' in basefile or ' ' in basefile:
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

class ArtFilesEpisodeProvider(ArtFilesAbstractProvider):
    mediatype = mediatypes.EPISODE

    def get_exact_images(self, path):
        if path.count('/'):
            path, inputfilename = path.rsplit('/', 1)
            path = path + '/'
        else:
            path, inputfilename = path.rpslit('\\', 1)
            path = path + '\\'
        _, files = xbmcvfs.listdir(path)
        inputbase = inputfilename.rsplit('.', 1)[0]
        result = {}
        for filename in files:
            if not filename.endswith(('.jpg', '.png', '.gif')):
                continue
            basefile = filename.rsplit('.', 1)[0]
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

def natural_sort(string, naturalsortresplit=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(naturalsortresplit, string)]
