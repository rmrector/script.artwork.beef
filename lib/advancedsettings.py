import xbmc
import xbmcgui
import xbmcvfs
import xml.etree.ElementTree as ET
from contextlib import closing

from lib.libs.pykodi import log, localize as L

FILENAME = 'special://userdata/advancedsettings.xml'
FILENAME_BAK = FILENAME + '.beef.bak'

ROOT_TAG = 'advancedsettings'
VIDEO_TAG = 'videolibrary'
MUSIC_TAG = 'musiclibrary'
ARTTYPE_TAG = 'arttype'

# 0: mediatype tag name, 1: library tag name, 2: Kodi's hardcoded art types to exclude from AS.xml
mediatype_map = {'tvshow': ('tvshowextraart', VIDEO_TAG, ('poster', 'banner', 'fanart')),
    'season': ('tvshowseasonextraart', VIDEO_TAG, ('poster', 'banner', 'fanart')),
    'episode': ('episodeextraart', VIDEO_TAG, ('thumb',)),
    'movie': ('movieextraart', VIDEO_TAG, ('poster', 'fanart')),
    'set': ('moviesetextraart', VIDEO_TAG, ('poster', 'fanart')),
    'musicvideo': ('musicvideoextraart', VIDEO_TAG, ('poster', 'fanart')),
    'artist': ('artistextraart', MUSIC_TAG, ('thumb', 'fanart')),
    'album': ('albumextraart', MUSIC_TAG, ('thumb',))}
unsupported_types = ('song',)

MALFORMED = 32654
BACKUP_SUCCESSFUL = 32655
BACKUP_UNSUCCESSFUL = 32656
RESTORE_SUCCESSFUL = 32657
RESTORE_UNSUCCESSFUL = 32658
RESTART_KODI = 32659

def save_arttypes(arttype_map):
    root = read_xml()
    if root is None:
        xbmcgui.Dialog().notification("Artwork Beef", L(MALFORMED), xbmcgui.NOTIFICATION_WARNING)
        return False

    set_arttypes(root, arttype_map)

    if save_backup():
        save_xml(root)
        xbmcgui.Dialog().ok("Artwork Beef", L(RESTART_KODI))

def set_arttypes(root, arttype_map):
    for key, artlist in arttype_map.items():
        if key not in mediatype_map:
            if key not in unsupported_types:
                log("Can't set arttypes for '{0}' in advancedsettings.xml".format(key), xbmc.LOGNOTICE)
            continue
        typemap = mediatype_map[key]
        library_elem = root.find(typemap[1])
        if library_elem is None:
            library_elem = ET.SubElement(root, typemap[1])
        mediatype_elem = library_elem.find(typemap[0])
        if artlist:
            if mediatype_elem is None:
                mediatype_elem = ET.SubElement(library_elem, typemap[0])
            else:
                mediatype_elem.clear()
            for arttype in artlist:
                if arttype in typemap[2]:
                    continue
                arttype_elem = ET.SubElement(mediatype_elem, ARTTYPE_TAG)
                arttype_elem.text = arttype
        elif mediatype_elem is not None:
            library_elem.remove(mediatype_elem)

def read_xml():
    if not xbmcvfs.exists(FILENAME):
        return ET.Element(ROOT_TAG)

    parser = ET.XMLParser(target=CommentedTreeBuilder())
    with closing(xbmcvfs.File(FILENAME)) as as_xml:
        try:
            return ET.parse(as_xml, parser).getroot()
        except ET.ParseError:
            log("Can't parse advancedsettings.xml", xbmc.LOGWARNING)

def save_xml(advancedsettings):
    indent(advancedsettings)
    with closing(xbmcvfs.File(FILENAME, 'w')) as as_xml:
        ET.ElementTree(advancedsettings).write(as_xml, 'utf-8', True)

def save_backup():
    if xbmcvfs.exists(FILENAME):
        xbmcvfs.copy(FILENAME, FILENAME_BAK)
        result = xbmcvfs.exists(FILENAME_BAK)
        if result:
            xbmcgui.Dialog().notification("Artwork Beef", L(BACKUP_SUCCESSFUL))
        else:
            xbmcgui.Dialog().notification("Artwork Beef", L(BACKUP_UNSUCCESSFUL), xbmc.LOGWARNING)
        return result
    log("advancedsettings.xml doesn't exist, can't save backup", xbmc.LOGNOTICE)
    return True

def restore_backup():
    if xbmcvfs.exists(FILENAME_BAK):
        xbmcvfs.copy(FILENAME_BAK, FILENAME)
        xbmcvfs.delete(FILENAME_BAK)
        result = xbmcvfs.exists(FILENAME)
        if result:
            xbmcgui.Dialog().notification("Artwork Beef", L(RESTORE_SUCCESSFUL))
        else:
            xbmcgui.Dialog().notification("Artwork Beef", L(RESTORE_UNSUCCESSFUL), xbmc.LOGWARNING)
        return result
    log("advancedsettings.xml.beef.bak doesn't exist, can't restore backup", xbmc.LOGWARNING)
    return False

def has_backup():
    return xbmcvfs.exists(FILENAME_BAK)

def indent(element, level=0):
    i = "\n" + level*"\t"
    if len(element):
        if not element.text or not element.text.strip():
            element.text = i + "\t"
        if not element.tail or not element.tail.strip():
            element.tail = i
        for element in element:
            indent(element, level + 1)
        if not element.tail or not element.tail.strip():
            element.tail = i
    else:
        if level and (not element.tail or not element.tail.strip()):
            element.tail = i

class CommentedTreeBuilder(ET.TreeBuilder):
    def comment(self, data):
        self.start(ET.Comment, {})
        self.data(data)
        self.end(ET.Comment)
