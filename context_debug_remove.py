import sys
import xbmcgui

from context import get_dbid, get_mediatype
from lib import cleaner
from lib.filemanager import FileManager
from lib.libs import quickjson, mediainfo as info
from lib.libs.pykodi import localize as L

def remove_art():
    # TODO: seasons and episodes and whatever like "add missing artwork" does
    listitem = sys.listitem
    mediatype = get_mediatype(listitem)
    dbid = get_dbid(listitem)

    if not (dbid or mediatype):
        return

    if not xbmcgui.Dialog().yesno("Artwork Beef: " + L(32427), L(750)):
        return
    remove_localfiles = xbmcgui.Dialog().yesno("Artwork Beef", L(32062))
    mediaitem = info.MediaItem(quickjson.get_item_details(dbid, mediatype))
    mediaitem.selectedart = cleaner.remove_specific_arttype(mediaitem, '* all')
    if remove_localfiles:
        FileManager().remove_deselected_files(mediaitem, True)
    info.update_art_in_library(mediatype, dbid, mediaitem.selectedart)
    info.remove_local_from_texturecache(mediaitem.art.values(), True)
    xbmcgui.Dialog().notification("Artwork Beef", L(32027).format(len(mediaitem.selectedart)))

if __name__ == '__main__':
    remove_art()
