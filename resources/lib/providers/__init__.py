import mediatypes
from fanarttv import FanartTVSeriesProvider, FanartTVMovieProvider
from themoviedb import TheMovieDBProvider
from thetvdbv2 import TheTVDBProvider

# These shouldn't be determined by the providers, but the processor, according to settings for some of them
# noauto might come from providers. Fanart.tv has a lot of fanart dupes, so I want to mark those from the provider
# Providers will need to return aspect ratio
HAPPY_IMAGE = 'happy'
NOAUTO_IMAGE = 'noauto'
GOOFY_IMAGE = 'goofy'

_providers = {
    mediatypes.TVSHOW: (TheTVDBProvider(), FanartTVSeriesProvider()),
    mediatypes.MOVIE: (TheMovieDBProvider(), FanartTVMovieProvider())
}

def get_providers():
    return _providers
