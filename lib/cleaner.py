import sys
import urllib

from devhelper import pykodi

import mediatypes
from mediainfo import arttype_matches_base, iter_base_arttypes, iter_urls_for_arttype

def clean_artwork(mediaitem):
    updated_art = dict(_get_clean_art(*art) for art in mediaitem['art'].iteritems())
    for basetype in iter_base_arttypes(updated_art):
        remove_duplicate_fanart = basetype == 'fanart'
        updated_art.update(_arrange_multiart(updated_art, basetype, remove_duplicate_fanart))

    return updated_art

def remove_otherartwork(mediaitem):
    ''' Remove artwork not enabled in add-on settings. '''
    keep_types = pykodi.get_main_addon().get_setting('save_additional_arttypes')
    keep_types = [addon.strip() for addon in keep_types.split(',')]
    keep_types = dict(arttype.split(':', 2) if ':' in arttype else (arttype, sys.maxsize) for arttype in keep_types)
    finalart = {}

    for basetype in iter_base_arttypes(mediaitem['art']):
        if basetype in keep_types:
            try:
                max_allowed = int(keep_types[basetype])
            except ValueError:
                max_allowed = sys.maxsize
        else:
            max_allowed = mediatypes.artinfo[mediaitem['mediatype']].get(basetype, {}).get('autolimit', 0)
        finalart.update(_arrange_multiart(mediaitem['art'], basetype, limit=max_allowed))

    finalart.update((arttype, None) for arttype in mediaitem['art'] if arttype not in finalart)
    return finalart

def _get_clean_art(arttype, url):
    if not url: # Remove empty URLs
        url = None
    elif url.startswith('http'):
        # Ensure all HTTP urls are properly escaped
        url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")

    return arttype, url

def _arrange_multiart(art, basetype, remove_duplicates=False, limit=sys.maxsize):
    ''' Patches holes in multiple art (if fanart1 and fanart3 are missing, 2 and 4 are moved up). '''
    new_art = {}
    art_urls = list(iter_urls_for_arttype(art, basetype))
    art_set = set(art_urls)
    for i, url in enumerate((u for u in art_urls if u in art_set) if remove_duplicates else art_urls):
        if i >= limit:
            break
        new_art['{0}{1}'.format(basetype, i if i else '')] = url
        art_set.discard(url)

    new_art.update((arttype, None) for arttype in art.keys() if arttype_matches_base(arttype, basetype) and arttype not in new_art)

    return new_art
