from devhelper import pykodi, quickjson

import mediatypes
from base import ProviderError

from artfiles import ArtFilesSeriesProvider, ArtFilesMovieProvider, ArtFilesEpisodeProvider
from fanarttv import FanartTVSeriesProvider, FanartTVMovieProvider
from nfofile import NFOFileSeriesProvider, NFOFileMovieProvider, NFOFileEpisodeProvider
from themoviedb import TheMovieDBProvider, TheMovieDBEpisodeProvider
from thetvdbv2 import TheTVDBProvider

external = {
    mediatypes.TVSHOW: (TheTVDBProvider(), FanartTVSeriesProvider()),
    mediatypes.MOVIE: (TheMovieDBProvider(), FanartTVMovieProvider()),
    mediatypes.EPISODE: (TheMovieDBEpisodeProvider(),)
}

forced = {
    mediatypes.TVSHOW: (NFOFileSeriesProvider(), ArtFilesSeriesProvider()),
    mediatypes.MOVIE: (NFOFileMovieProvider(), ArtFilesMovieProvider()),
    mediatypes.EPISODE: (NFOFileEpisodeProvider(), ArtFilesEpisodeProvider())
}

useragent = 'ArtworkBeef Kodi'

def update_useragent():
    global useragent
    beefversion = pykodi.get_main_addon().version
    props = quickjson.get_application_properties(['name', 'version'])
    appversion = '{0}.{1}'.format(props['version']['major'], props['version']['minor'])
    useragent = 'ArtworkBeef/{0} {1}/{2}'.format(beefversion, props['name'], appversion)

update_useragent()
