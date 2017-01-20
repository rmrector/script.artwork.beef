import providers
from providers import ProviderError
from libs import mediatypes
from libs.mediainfo import arttype_matches_base

class Gatherer(object):
    def __init__(self, monitor, only_filesystem):
        self.monitor = monitor
        self.only_filesystem = only_filesystem

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
            if not self.only_filesystem and 'imdbnumber' in mediaitem and next(list_missing_arttypes(
                    mediaitem['mediatype'], mediaitem.get('seasons'), existingtypes), False):
                availableartwork, error = self.get_external_artwork(mediaitem['mediatype'], mediaitem.get('seasons'),
                    existingtypes, mediaitem['imdbnumber'])
                services_hit = True
        elif 'imdbnumber' in mediaitem:
            availableartwork, error = self.get_external_artwork(mediaitem['mediatype'], mediaitem.get('seasons'),
                existingtypes, mediaitem['imdbnumber'], False)
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

    def get_external_artwork(self, mediatype, seasons, existingarttypes, imdbnumber, skipmissing=True):
        missing = list(list_missing_arttypes(mediatype, seasons, existingarttypes)) if skipmissing else None
        images = {}
        error = None
        for provider in providers.external.get(mediatype, ()):
            try:
                providerimages = provider.get_images(imdbnumber, missing)
            except ProviderError as ex:
                error = {'providername': provider.name.display, 'message': ex.message}
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

def list_missing_arttypes(mediatype, seasons, existingarttypes):
    fullartinfo = mediatypes.artinfo[mediatype]
    for arttype, artinfo in fullartinfo.iteritems():
        if not artinfo['autolimit']:
            continue
        elif artinfo['autolimit'] == 1:
            if arttype not in existingarttypes:
                yield arttype
        else:
            artcount = sum(1 for art in existingarttypes if arttype_matches_base(art, arttype))
            if artcount < artinfo['autolimit']:
                yield arttype

    if mediatype == mediatypes.TVSHOW:
        seasonartinfo = mediatypes.artinfo.get(mediatypes.SEASON)
        for season in seasons.iteritems():
            for arttype, artinfo in seasonartinfo.iteritems():
                arttype = '%s.%s.%s' % (mediatypes.SEASON, season[0], arttype)
                if not artinfo['autolimit']:
                    continue
                elif artinfo['autolimit'] == 1:
                    if arttype not in existingarttypes:
                        yield arttype
                else:
                    artcount = sum(1 for art in existingarttypes if arttype_matches_base(art, arttype))
                    if artcount < artinfo['autolimit']:
                        yield arttype
