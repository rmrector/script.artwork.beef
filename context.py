import sys
import xbmc

from lib.artworkprocessor import ArtworkProcessor

def main(mode):
    listitem = sys.listitem
    mediatype = get_mediatype(listitem)
    dbid = get_dbid(listitem)

    if dbid and mediatype:
        processor = ArtworkProcessor()
        processor.process_item(mediatype, dbid, mode)

def get_mediatype(listitem):
    try:
        return listitem.getVideoInfoTag().getMediaType()
    except AttributeError:
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
        return listitem.getVideoInfoTag().getDbId()
    except AttributeError:
        pass
    infolabel = xbmc.getInfoLabel('ListItem.Label')
    truelabel = listitem.getLabel()
    if infolabel != truelabel:
        return int(listitem.getfilename().split('?')[0].rstrip('/').split('/')[-1])
    else:
        return int(xbmc.getInfoLabel('ListItem.DBID'))

if __name__ == '__main__':
    main('auto')
