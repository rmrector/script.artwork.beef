import urllib

from utils import natural_sort as ns

def cleanartwork(art):
    result = dict(_get_clean_item(*item) for item in art.iteritems())
    result.update(_remove_duplicate_fanart(result))

    return result

def _get_clean_item(arttype, url):
    if arttype != 'thumb':
        if not url: # Remove empty URLs
            url = None
        elif url.startswith('http'):
            # Ensure all HTTP urls are properly escaped
            url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")

    return arttype, url

def _remove_duplicate_fanart(art):
    new_fanart = {}
    fanart_urls = [art[arttype] for arttype in sorted(art.keys(), key=ns) if arttype.startswith('fanart')]
    fanart_set = set(fanart_urls)
    if len(fanart_urls) != len(fanart_set):
        count = 0
        for url in fanart_urls:
            if url and url in fanart_set:
                new_fanart['fanart{0}'.format(count if count else '')] = url
                fanart_set.remove(url)
                count += 1

        new_fanart.update((arttype, None) for arttype in art.keys() if arttype.startswith('fanart') and arttype not in new_fanart)

    return new_fanart or art
