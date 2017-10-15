from lib.providers import search
from lib.libs import mediatypes
from lib.providers.base import ProviderError

from lib.providers.artfiles import ArtFilesSeriesProvider, ArtFilesMovieProvider, ArtFilesEpisodeProvider, ArtFilesMovieSetProvider
from lib.providers.fanarttv import FanartTVSeriesProvider, FanartTVMovieProvider, FanartTVMovieSetProvider
from lib.providers.nfofile import NFOFileSeriesProvider, NFOFileMovieProvider, NFOFileEpisodeProvider, NFOFileMovieSetProvider
from lib.providers.themoviedb import TheMovieDBMovieProvider, TheMovieDBEpisodeProvider, TheMovieDBMovieSetProvider
from lib.providers.thetvdbv2 import TheTVDBProvider
from lib.providers.videofile import VideoFileMovieProvider, VideoFileEpisodeProvider

external = {
    mediatypes.TVSHOW: (TheTVDBProvider(), FanartTVSeriesProvider()),
    mediatypes.MOVIE: (TheMovieDBMovieProvider(), FanartTVMovieProvider()),
    mediatypes.MOVIESET: (TheMovieDBMovieSetProvider(), FanartTVMovieSetProvider()),
    mediatypes.EPISODE: (TheMovieDBEpisodeProvider(),)
}

forced = {
    mediatypes.TVSHOW: (ArtFilesSeriesProvider(), NFOFileSeriesProvider()),
    mediatypes.MOVIE: (ArtFilesMovieProvider(), NFOFileMovieProvider(), VideoFileMovieProvider()),
    mediatypes.MOVIESET: (ArtFilesMovieSetProvider(), NFOFileMovieSetProvider()),
    mediatypes.EPISODE: (ArtFilesEpisodeProvider(), NFOFileEpisodeProvider(), VideoFileEpisodeProvider())
}

search.init()
