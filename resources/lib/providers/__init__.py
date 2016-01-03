import mediatypes
from fanarttv import FanartTvSeriesProvider, FanartTvMovieProvider

_providers = {mediatypes.TVSHOW: (FanartTvSeriesProvider(),), mediatypes.MOVIE: (FanartTvMovieProvider(),)}
def get_providers():
    return _providers
