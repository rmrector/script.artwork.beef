import sys
import xbmc

from lib.artworkprocessor import ArtworkProcessor

# DEPRECATED: StringCompare in addon.xml is deprecated in Krypton, gone in Leia,
#  but both resolve to False when unrecognized so the result is the same for all versions

def main(mode):
    listitem = sys.listitem
    mediatype = get_mediatype(listitem)
    dbid = get_dbid(listitem)

    if dbid and mediatype:
        processor = ArtworkProcessor()
        processor.process_item(mediatype, dbid, mode)

def get_mediatype(listitem):
    try:
        item = listitem.getVideoInfoTag().getMediaType()
        if not item:
            item = listitem.getMusicInfoTag().getMediaType()
        return item
    except AttributeError:
        # DEPRECATED: Before Krypton
        pass
    count = 0
    mediatype = xbmc.getInfoLabel('ListItem.DBTYPE')
    while not mediatype and count < 5:
        count += 1
        xbmc.sleep(200)
        mediatype = xbmc.getInfoLabel('ListItem.DBTYPE')
    if not mediatype:
        xbmc.executebuiltin('Notification(Artwork Beef cannot proceed, "Got an unexpected content type. Try again, it should work.", 6000, DefaultIconWarning.png)')
    return mediatype

def get_dbid(listitem):
    try:
        dbid = listitem.getVideoInfoTag().getDbId()
        if dbid == -1:
            dbid = listitem.getMusicInfoTag().getDbId()
        return dbid
    except AttributeError:
        # DEPRECATED: Before Krypton
        pass
    if listitem.getLabel() != xbmc.getInfoLabel('ListItem.Label'):
        # InfoLabels can report the wrong item
        return int(listitem.getfilename().split('?')[0].rstrip('/').split('/')[-1])
    else:
        return int(xbmc.getInfoLabel('ListItem.DBID'))

if __name__ == '__main__':
    main('auto')
