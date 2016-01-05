import mediatypes
from fanarttv import FanartTvSeriesProvider, FanartTvMovieProvider
from themoviedb import TheMovieDbProvider
from thetvdbv2 import TheTVDBProvider

_providers = {
    mediatypes.TVSHOW: (TheTVDBProvider(), FanartTvSeriesProvider()),
    mediatypes.MOVIE: (TheMovieDbProvider(), FanartTvMovieProvider())
}

def get_providers():
    return _providers
