from requests import Session

from lib.providers import search
from lib.libs import mediatypes
from lib.providers.base import ProviderError

from lib.providers.artfiles import ArtFilesSeriesProvider, ArtFilesMovieProvider, ArtFilesEpisodeProvider, ArtFilesMovieSetProvider
from lib.providers.fanarttv import FanartTVSeriesProvider, FanartTVMovieProvider, FanartTVMovieSetProvider
from lib.providers.nfofile import NFOFileSeriesProvider, NFOFileMovieProvider, NFOFileEpisodeProvider, NFOFileMovieSetProvider
from lib.providers.themoviedb import TheMovieDBMovieProvider, TheMovieDBEpisodeProvider, TheMovieDBMovieSetProvider
from lib.providers.thetvdbv2 import TheTVDBProvider

session = Session()
external = {
    mediatypes.TVSHOW: (TheTVDBProvider(session), FanartTVSeriesProvider(session)),
    mediatypes.MOVIE: (TheMovieDBMovieProvider(session), FanartTVMovieProvider(session)),
    mediatypes.MOVIESET: (TheMovieDBMovieSetProvider(session), FanartTVMovieSetProvider(session)),
    mediatypes.EPISODE: (TheMovieDBEpisodeProvider(session),)
}

forced = {
    mediatypes.TVSHOW: (ArtFilesSeriesProvider(), NFOFileSeriesProvider()),
    mediatypes.MOVIE: (ArtFilesMovieProvider(), NFOFileMovieProvider()),
    mediatypes.MOVIESET: (ArtFilesMovieSetProvider(), NFOFileMovieSetProvider()),
    mediatypes.EPISODE: (ArtFilesEpisodeProvider(), NFOFileEpisodeProvider())
}

search.init(session)
