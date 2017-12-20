import os
import sys
import urllib
import xbmcvfs
from abc import ABCMeta
from contextlib import closing
import xml.etree.ElementTree as ET

if sys.version_info < (2, 7):
    from xml.parsers.expat import ExpatError as ParseError
else:
    from xml.etree.ElementTree import ParseError

from lib.libs import mediatypes
from lib.libs.utils import SortedDisplay, get_movie_path_list

NFO_FILE = 32003

class NFOFileAbstractProvider(object):
    __metaclass__ = ABCMeta
    name = SortedDisplay('file:nfo', NFO_FILE)

    def build_resultimage(self, url, title):
        if isinstance(url, unicode):
            url = url.encode('utf-8')
        if url.startswith('http'):
            url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
        resultimage = {'url': url, 'provider': self.name, 'preview': url}
        resultimage['title'] = '<{0}>'.format(title)
        resultimage['rating'] = SortedDisplay(0, '')
        resultimage['size'] = SortedDisplay(0, '')
        resultimage['language'] = 'xx'
        return resultimage

class NFOFileSeriesProvider(NFOFileAbstractProvider):
    mediatype = mediatypes.TVSHOW

    def get_exact_images(self, mediaitem):
        root = read_nfofile(mediaitem.file + 'tvshow.nfo')
        if root is None or root.find('art') is None:
            return {}

        artlistelement = root.find('art')
        result = {}
        for artelement in artlistelement:
            arttype = artelement.tag.lower()
            if arttype == 'season':
                num = artelement.get('num')
                if num is None:
                    continue
                try:
                    num = int(num)
                except ValueError:
                    continue
                if num < -1:
                    continue
                for seasonartelement in artelement:
                    url = seasonartelement.text.strip()
                    if seasonartelement.tag.isalnum() and url:
                        seasonarttype = 'season.{0}.{1}'.format(num, seasonartelement.tag.lower())
                        result[seasonarttype] = self.build_resultimage(url, seasonarttype)
            elif arttype.isalnum() and artelement.text.strip():
                result[arttype] = self.build_resultimage(artelement.text.strip(), arttype)
        return result

class NFOFileMovieProvider(NFOFileAbstractProvider):
    mediatype = mediatypes.MOVIE

    def get_exact_images(self, mediaitem):
        paths = get_movie_path_list(mediaitem.file)
        paths = [os.path.splitext(p)[0] + '.nfo' for p in paths]
        paths.append(os.path.dirname(paths[0]) + '/movie.nfo')

        artlist = None
        for nfopath in paths:
            root = read_nfofile(nfopath)
            if root is not None and root.find('art') is not None:
                artlist = root.find('art')
                break

        if artlist is None:
            return {}

        result = {}
        for artelement in artlist:
            arttype = artelement.tag.lower()
            url = artelement.text.strip()
            if arttype.isalnum() and url:
                result[arttype] = self.build_resultimage(url, arttype)
        return result

class NFOFileMovieSetProvider(NFOFileAbstractProvider):
    mediatype = mediatypes.MOVIESET

    def get_exact_images(self, mediaitem):
        path = mediaitem.file
        if os.path.basename(path):
            paths = [os.path.splitext(path)[0] + '.nfo', os.path.splitext(path)[0] + '/set.nfo']
        else:
            paths = [path + 'set.nfo']
        artlist = None
        for nfopath in paths:
            root = read_nfofile(nfopath)
            if root is not None and root.find('art') is not None:
                artlist = root.find('art')
                break

        if artlist is None:
            return {}

        result = {}
        for artelement in artlist:
            arttype = artelement.tag.lower()
            url = artelement.text.strip()
            if arttype.isalnum() and url:
                result[arttype] = self.build_resultimage(url, arttype)
        return result

class NFOFileEpisodeProvider(NFOFileAbstractProvider):
    mediatype = mediatypes.EPISODE

    def get_exact_images(self, mediaitem):
        root = read_nfofile(os.path.splitext(mediaitem.file)[0] + '.nfo')
        if root is None or root.find('art') is None:
            return {}

        result = {}
        artlistelement = root.find('art')
        for artelement in artlistelement:
            arttype = artelement.tag.lower()
            url = artelement.text.strip()
            if arttype.isalnum() and url:
                result[arttype] = self.build_resultimage(url, arttype)
        return result

class NFOFileMusicVideoProvider(NFOFileAbstractProvider):
    mediatype = mediatypes.MUSICVIDEO

    def get_exact_images(self, mediaitem):
        path = mediaitem.file
        artlist = None
        for nfopath in (os.path.splitext(path)[0] + '.nfo', os.path.dirname(path) + '/musicvideo.nfo'):
            root = read_nfofile(nfopath)
            if root is not None and root.find('art') is not None:
                artlist = root.find('art')
                break

        if artlist is None:
            return {}

        result = {}
        for artelement in artlist:
            arttype = artelement.tag.lower()
            url = artelement.text.strip()
            if arttype.isalnum() and url:
                result[arttype] = self.build_resultimage(url, arttype)
        return result

def read_nfofile(filename):
    if not xbmcvfs.exists(filename):
        return None
    with closing(xbmcvfs.File(filename)) as nfofile:
        try:
            return ET.parse(nfofile).getroot()
        except ParseError:
            pass
        # maybe it's all XML except the last line, like the wiki suggests for XML + URL
        nfofile.seek(0, 0)
        lines = nfofile.read().split('\n')
        while lines and not lines[-1].strip():
            del lines[-1] # Remove final blank lines
        if lines: # Remove the line that possibly contains the URL
            del lines[-1]
        if lines:
            try:
                return ET.XML('\n'.join(lines))
            except ParseError:
                pass
