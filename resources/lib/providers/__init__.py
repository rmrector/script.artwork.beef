import mediatypes
from base import ProviderError

from fanarttv import FanartTVSeriesProvider, FanartTVMovieProvider
from themoviedb import TheMovieDBProvider, TheMovieDBEpisodeProvider
from thetvdbv2 import TheTVDBProvider

_providers = {
    mediatypes.TVSHOW: (TheTVDBProvider(), FanartTVSeriesProvider()),
    mediatypes.MOVIE: (TheMovieDBProvider(), FanartTVMovieProvider()),
    mediatypes.EPISODE: (TheMovieDBEpisodeProvider(),)
}

def get_providers():
    return _providers
