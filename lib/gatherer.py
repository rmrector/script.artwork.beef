import traceback
import xbmc

from lib import providers
from lib.libs import mediatypes
from lib.libs.addonsettings import settings
from lib.libs.mediainfo import keep_arttype
from lib.libs.pykodi import localize as L, log
from lib.libs.utils import SortedDisplay
from lib.providers import ProviderError

MAX_ERRORS = 3
TOO_MANY_ERRORS = 32031

class Gatherer(object):
    def __init__(self, monitor, languages):
        self.monitor = monitor
        providers.base.languages = languages
        self.providererrors = {}

    def getartwork(self, mediaitem, fsonly=False, skipexisting=True):
        services_hit = False
        error = None
        mediaitem.forcedart = self.get_forced_artwork(mediaitem, not skipexisting)
        existingtypes = [key for key, url in mediaitem.art.iteritems() if url]
        existingtypes.extend(mediaitem.forcedart.keys())
        if skipexisting:
            if not fsonly and mediaitem.uniqueids and mediaitem.missingart:
                mediaitem.availableart, error = self.get_external_artwork(mediaitem.mediatype, mediaitem.seasons,
                    mediaitem.uniqueids, mediaitem.missingart)
                services_hit = True
        elif mediaitem.uniqueids:
            mediaitem.availableart, error = self.get_external_artwork(mediaitem.mediatype, mediaitem.seasons,
                mediaitem.uniqueids)
            services_hit = True
        # combine keyart to poster if keyart disabled or 'prefer titlefree poster' option enabled
        if 'keyart' in mediaitem.availableart and (settings.titlefree_poster or
                not mediatypes.get_artinfo(mediaitem.mediatype, 'keyart')['autolimit']):
            if 'poster' not in mediaitem.availableart:
                mediaitem.availableart['poster'] = []
            mediaitem.availableart['poster'].extend(mediaitem.availableart['keyart'])
        for arttype, imagelist in mediaitem.availableart.iteritems():
            _sort_images(arttype, imagelist, mediaitem.sourcemedia, mediaitem.mediatype)
        return services_hit, error

    def get_forced_artwork(self, mediaitem, allowmutiple=False):
        if not mediaitem.file:
            if mediaitem.mediatype not in mediatypes.audiotypes \
            or not mediatypes.central_directories[mediatypes.ARTIST]:
                return {}
        if mediaitem.borked_filename:
            return {}
        resultimages = {}
        for provider in providers.forced.get(mediaitem.mediatype, ()):
            for arttype, image in provider.get_exact_images(mediaitem).iteritems():
                if arttype.startswith('season.'):
                    season = arttype.rsplit('.', 2)[1]
                    if int(season) not in mediaitem.seasons:
                        continue
                if not keep_arttype(mediaitem.mediatype, arttype, image['url']):
                    continue
                if allowmutiple:
                    if arttype not in resultimages:
                        resultimages[arttype] = []
                    resultimages[arttype].append(image)
                else:
                    if arttype not in resultimages:
                        resultimages[arttype] = image
            if self.monitor.abortRequested():
                break
        return resultimages

    def get_external_artwork(self, mediatype, seasons, uniqueids, missing=None):
        images = {}
        error = None
        for provider in providers.external.get(mediatype, ()):
            errcount = self.providererrors.get(provider.name, 0)
            if errcount == MAX_ERRORS:
                continue
            try:
                providerimages = provider.get_images(uniqueids, missing)
                self.providererrors[provider.name] = 0
            except Exception as ex:
                # gross. need to split "getting" and "parsing" then catch and wrap exceptions
                # on the latter, then leave most of this code back for "ProviderError" only
                errcount += 1
                self.providererrors[provider.name] = errcount
                if errcount != 1 and errcount != MAX_ERRORS:
                    continue
                error = {'providername': provider.name.display}
                if errcount == 1: # notify on first error
                    error['message'] = getattr(ex, 'message', repr(ex))
                elif errcount == MAX_ERRORS: # and on last error when we're no longer going to try this provider
                    error['message'] = L(TOO_MANY_ERRORS)
                if not isinstance(ex, ProviderError):
                    log("Error parsing provider response", xbmc.LOGWARNING)
                    log(traceback.format_exc(), xbmc.LOGWARNING)
                continue
            for arttype, artlist in providerimages.iteritems():
                if arttype.startswith('season.'):
                    season = arttype.rsplit('.', 2)[1]
                    if int(season) not in seasons:
                        # Don't add artwork for seasons we don't have
                        continue
                if arttype not in images:
                    images[arttype] = []
                images[arttype].extend(artlist)
            if self.monitor.abortRequested():
                break
        return images, error

def _sort_images(basearttype, imagelist, mediasource, mediatype):
    # 1. Language, preferring fanart with no language/title if configured
    # 2. Match discart to media source
    # 3. Preferred source
    # 4. Size (in 200px groups), up to preferredsize
    # 5. Rating
    imagelist.sort(key=lambda image: image['rating'].sort, reverse=True)
    imagelist.sort(key=_size_sort, reverse=True)
    if basearttype == 'discart':
        if mediasource != 'unknown':
            imagelist.sort(key=lambda image: 0 if image.get('subtype', SortedDisplay(None, '')).sort == mediasource else 1)
    imagelist.sort(key=lambda image: _preferredsource_sort(image, mediatype), reverse=True)
    imagelist.sort(key=lambda image: _imagelanguage_sort(image, basearttype))

def _preferredsource_sort(image, mediatype):
    result = 1 if mediatypes.ispreferred_source(mediatype, image['provider'][0]) else 0
    return result

def _size_sort(image):
    imagesplit = image['size'].display.split('x')
    if len(imagesplit) != 2:
        return image['size'].sort // 200
    try:
        imagesize = int(imagesplit[0]), int(imagesplit[1])
    except ValueError:
        return image['size'].sort // 200
    if imagesize[0] > settings.preferredsize[0]:
        shrink = settings.preferredsize[0] / float(imagesize[0])
        imagesize = settings.preferredsize[0], imagesize[1] * shrink
    if imagesize[1] > settings.preferredsize[1]:
        shrink = settings.preferredsize[1] / float(imagesize[1])
        imagesize = imagesize[0] * shrink, settings.preferredsize[1]
    return max(imagesize) // 200

def _imagelanguage_sort(image, basearttype):
    if not providers.base.languages:
        return 1, image['language']

    primarysort = 1 if image['language'] not in providers.base.languages else \
        1.0 * providers.base.languages.index(image['language']) / len(providers.base.languages)

    if image['language']:
        if basearttype.endswith('fanart') and settings.titlefree_fanart or \
                basearttype.endswith('poster') and settings.titlefree_poster:
            primarysort += 1

    return primarysort, image['language']
