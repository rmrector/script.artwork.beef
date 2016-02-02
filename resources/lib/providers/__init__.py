import mediatypes

from sorteddisplaytuple import SortedDisplay
from fanarttv import FanartTVSeriesProvider, FanartTVMovieProvider
from themoviedb import TheMovieDBProvider, TheMovieDBEpisodeProvider
from thetvdbv2 import TheTVDBProvider

# These shouldn't be determined by the providers, but the processor, according to settings for some of them
# noauto might come from providers. Fanart.tv has a lot of fanart dupes, so I want to mark those from the provider
HAPPY_IMAGE = SortedDisplay(0, 'happy')
NOAUTO_IMAGE = SortedDisplay(0, 'noauto')

_providers = {
    mediatypes.TVSHOW: (TheTVDBProvider(), FanartTVSeriesProvider()),
    mediatypes.MOVIE: (TheMovieDBProvider(), FanartTVMovieProvider()),
    mediatypes.EPISODE: (TheMovieDBEpisodeProvider(),)
}

def get_providers():
    return _providers
