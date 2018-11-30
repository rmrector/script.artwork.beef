import urllib
import xbmcvfs

from lib.libs import pykodi, mediatypes, quickjson
from lib.libs.mediainfo import iter_base_arttypes, fill_multiart, keep_arttype
from lib.libs.addonsettings import settings

# 0=original URLs, 1=new URL, 2=URL match
old_urls_fix = {
    'tvdb': (
        ('http://www.thetvdb.com/banners/', 'http://thetvdb.com/banners/', 'https://thetvdb.com/banners/'),
        'https://www.thetvdb.com/banners/',
        'thetvdb.com/banners/'),
    'tadb': (
        ('http://media.theaudiodb.com/images/', 'http://www.theaudiodb.com/images/'),
        'https://www.theaudiodb.com/images/',
        'theaudiodb.com/images/')}

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
        if not url:
            continue
        if not url.startswith(pykodi.notimagefiles) and not mediaitem.borked_filename \
                and not xbmcvfs.exists(url):
            # Remove local artwork if it is no longer available
            updated_art[arttype] = None
            continue
        if not settings.clean_imageurls:
            continue
        for fixcfg in old_urls_fix.values():
            # fix other web service URLs
            if url.startswith(fixcfg[0]):
                updated_art[arttype] = fixcfg[1] + url[url.index(fixcfg[2]) + len(fixcfg[2]):]
                quickjson.remove_texture_byurl(url)
    return updated_art

def remove_specific_arttype(mediaitem, arttype):
    '''pass '* all' as arttype to clear all artwork, '* nowhitelist' to clear images not on whitelist.'''
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
    elif url.startswith('http') and settings.clean_imageurls:
        # Ensure all HTTP urls are properly escaped
        url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")

    return arttype, url
