import urllib
import xbmcvfs

from lib.libs import pykodi, mediatypes, quickjson
from lib.libs.mediainfo import iter_base_arttypes, fill_multiart, keep_arttype

old_thetvdb_urls = ('http://www.thetvdb.com/banners/', 'http://thetvdb.com/banners/',
    'https://thetvdb.com/banners/')

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

    for arttype, url in updated_art.iteritems():
        # Remove local artwork if it is no longer available
        if url and not url.startswith(pykodi.notlocalimages) and not xbmcvfs.exists(url):
            updated_art[arttype] = None
        if url.startswith(old_thetvdb_urls):
            # TheTVDB now has forced HTTPS, redirects to 'www'
            updated_art[arttype] = 'https://www.thetvdb.com/banners/' + url[url.index('/banners/') + 20:]
            quickjson.remove_texture_byurl(url)
    return updated_art

def remove_specific_arttype(mediaitem, arttype):
    '''pass 'all' as arttype to clear all artwork, nowhitelist to clear images not on whitelist.'''
    if arttype == '* all':
        return dict((atype, None) for atype in mediaitem.art)
    elif arttype == '* nowhitelist':
        return dict((atype, None) for atype, url in mediaitem.art.iteritems()
            if not keep_arttype(mediaitem.mediatype, atype, url))
    finalart = {}
    if arttype in mediaitem.art:
        finalart[arttype] = None
    return finalart

def _get_clean_art(arttype, url):
    if not url: # Remove empty URLs
        url = None
    elif url.startswith('http'):
        # Ensure all HTTP urls are properly escaped
        url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")

    return arttype, url
