import sys
import urllib
import xbmcvfs

from lib.libs import pykodi, mediatypes, quickjson
from lib.libs.addonsettings import settings
from lib.libs.mediainfo import iter_base_arttypes, fill_multiart

def clean_artwork(mediaitem):
    updated_art = dict(_get_clean_art(*art) for art in mediaitem.art.iteritems())
    for basetype in iter_base_arttypes(updated_art.keys()):
        updated_art.update(fill_multiart(updated_art, basetype))
    if updated_art.get('cdart') and mediaitem.mediatype == mediatypes.MUSICVIDEO:
        # DEPRECATED: short - initial music video support used cdart like the old support in AD,
        #  but I really don't want to carry it to the music library
        if not updated_art.get('discart'):
            updated_art['discart'] = updated_art['cdart']
            updated_art['cdart'] = None

    # Remove local artwork if it is no longer available
    for arttype, url in updated_art.iteritems():
        if url and not url.startswith(pykodi.notlocalimages) and not xbmcvfs.exists(url):
            updated_art[arttype] = None
    return updated_art

def remove_otherartwork(mediaitem):
    ''' Remove artwork not enabled in add-on settings. '''
    keep_types = settings.save_additional_arttypes
    keep_types = [addon.strip() for addon in keep_types.split(',')]
    keep_types = dict(arttype.split(':', 2) if ':' in arttype else (arttype, sys.maxsize) for arttype in keep_types)
    finalart = {}

    finalart.update((arttype, None) for arttype in mediaitem.art if arttype not in finalart)
    return finalart

def remove_specific_arttype(mediaitem, arttype):
    '''pass 'all' as arttype to clear all artwork.'''
    if arttype == 'all':
        return dict((atype, None) for atype in mediaitem.art)
    finalart = dict(art for art in mediaitem.art.iteritems())
    if arttype in finalart:
        finalart[arttype] = None
    return finalart

def _get_clean_art(arttype, url):
    if not url: # Remove empty URLs
        url = None
    elif url.startswith('http'):
        # Ensure all HTTP urls are properly escaped
        url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")

    return arttype, url
