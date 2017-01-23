from requests import Session

import search
from lib.libs import mediatypes
from base import ProviderError

from artfiles import ArtFilesSeriesProvider, ArtFilesMovieProvider, ArtFilesEpisodeProvider, ArtFilesMovieSetProvider
from fanarttv import FanartTVSeriesProvider, FanartTVMovieProvider, FanartTVMovieSetProvider
from nfofile import NFOFileSeriesProvider, NFOFileMovieProvider, NFOFileEpisodeProvider, NFOFileMovieSetProvider
from themoviedb import TheMovieDBMovieProvider, TheMovieDBEpisodeProvider, TheMovieDBMovieSetProvider
from thetvdbv2 import TheTVDBProvider

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
