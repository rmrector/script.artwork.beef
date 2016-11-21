import re
import xbmc
from collections import namedtuple
from os.path import split, basename, dirname

from devhelper import pykodi
from devhelper.pykodi import log

addon = pykodi.get_main_addon()

SortedDisplay = namedtuple('SortedDisplay', ['sort', 'display'])

def localize(messageid):
    if isinstance(messageid, basestring):
        return messageid
    if messageid >= 32000 and messageid < 33000:
        return addon.getLocalizedString(messageid)
    return xbmc.getLocalizedString(messageid)

def natural_sort(string, split_regex=re.compile(r'([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(split_regex, string)]

# TODO: Load from advancedsettings.xml
moviestacking = [re.compile(r'(.*?)([ _.-]*(?:cd|dvd|p(?:ar)?t|dis[ck])[ _.-]*[0-9]+)(.*?)(\.[^.]+)$', re.IGNORECASE),
    re.compile(r'(.*?)([ _.-]*(?:cd|dvd|p(?:ar)?t|dis[ck])[ _.-]*[a-d])(.*?)(\.[^.]+)$', re.IGNORECASE),
    re.compile(r'(.*?)([ ._-]*[a-d])(.*?)(\.[^.]+)$', re.IGNORECASE)
]
def get_movie_path_list(stackedpath):
    """Returns a list of filenames that can be used to find a movie's supporting files.
    The list includes both possible filenames for stacks, and the VIDEO_TS/BDMV parent directory.
    If neither applies, returns a list of one item, the original path.
    Check for the supporting files from each of these results."""
    result = []
    if not stackedpath.startswith('stack://'):
        result = [stackedpath]
    else:
        firstpath, path2 = stackedpath[8:].split(' , ')[0:2]

        path, filename = split(firstpath)
        if filename:
            filename2 = basename(path2)
            for regex in moviestacking:
                offset = 0
                while True:
                    match = regex.match(filename, offset)
                    match2 = regex.match(filename2, offset)
                    if match != None and match2 != None and match.group(1).lower() == match2.group(1).lower():
                        if match.group(2).lower() == match2.group(2).lower():
                            offset = match.start(3)
                            continue
                        result = [firstpath, path + '/' + filename[:offset] + match.group(1).rstrip() + match.group(4)]
                    break
        else: # folder stacking
            pass # I can't even get Kodi to add stacked VIDEO_TS rips period
        if not result:
            log("Couldn't get an unstacked path from \"{0}\"".format(stackedpath), xbmc.LOGINFO)
            result = [firstpath]
    if basename(dirname(result[0])) in ('VIDEO_TS', 'BDMV'):
        result.append(dirname(dirname(result[0])) + '/' + basename(result[0]))
    return result
