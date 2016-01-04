import mediatypes
from fanarttv import FanartTvSeriesProvider, FanartTvMovieProvider
from thetvdbv2 import TheTVDBProvider

_providers = {mediatypes.TVSHOW: (TheTVDBProvider(), FanartTvSeriesProvider()), mediatypes.MOVIE: (FanartTvMovieProvider(),)}
def get_providers():
    return _providers
