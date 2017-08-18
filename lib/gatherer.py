from lib import providers
from lib.providers import ProviderError

MAX_ERRORS = 3

class Gatherer(object):
    def __init__(self, monitor, only_filesystem, languages):
        self.monitor = monitor
        self.only_filesystem = only_filesystem
        providers.base.languages = [lang for lang in languages if lang]
        self.providererrors = {}

    def getartwork(self, mediaitem, skipexisting=True):
        forcedartwork = {}
        availableartwork = {}
        services_hit = False
        error = None
        forcedartwork = self.get_forced_artwork(mediaitem['mediatype'], mediaitem.get('file'),
            mediaitem.get('seasons'), not skipexisting)
        existingtypes = [key for key, url in mediaitem['art'].iteritems() if url]
        existingtypes.extend(forcedartwork.keys())
        if skipexisting:
            if not self.only_filesystem and 'imdbnumber' in mediaitem and mediaitem['missing art']:
                availableartwork, error = self.get_external_artwork(mediaitem['mediatype'], mediaitem.get('seasons'),
                    mediaitem['imdbnumber'], mediaitem['missing art'])
                services_hit = True
        elif 'imdbnumber' in mediaitem:
            availableartwork, error = self.get_external_artwork(mediaitem['mediatype'], mediaitem.get('seasons'),
                mediaitem['imdbnumber'])
            services_hit = True
        # REVIEW: This 4 value return is bugging me
        return forcedartwork, availableartwork, services_hit, error

    def get_forced_artwork(self, mediatype, mediafile, seasons, allowmutiple=False):
        if not mediafile:
            return {}
        resultimages = {}
        for provider in providers.forced.get(mediatype, ()):
            for arttype, image in provider.get_exact_images(mediafile).iteritems():
                if arttype.startswith('season.'):
                    season = arttype.rsplit('.', 2)[1]
                    if int(season) not in seasons:
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

    def get_external_artwork(self, mediatype, seasons, imdbnumber, missing=None):
        images = {}
        error = None
        for provider in providers.external.get(mediatype, ()):
            errcount = self.providererrors.get(provider.name, 0)
            if errcount == MAX_ERRORS:
                continue
            try:
                providerimages = provider.get_images(imdbnumber, missing)
                self.providererrors[provider.name] = 0
            except ProviderError as ex:
                errcount += 1
                self.providererrors[provider.name] = errcount
                error = {'providername': provider.name.display}
                if errcount == 1: # notify on first error
                    error['message'] = ex.message
                elif errcount == MAX_ERRORS: # and on last error when we're no longer going to try this provider
                    error['message'] = "Encountered multiple errors, skipping provider for remaining items."
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
