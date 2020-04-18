from lib.libs import mediatypes
from lib.providers.base import ProviderError

from lib.providers.artfiles import ArtFilesSeriesProvider, ArtFilesMovieProvider, ArtFilesEpisodeProvider, \
    ArtFilesMovieSetProvider, ArtFilesMusicVideoProvider, ArtFilesArtistProvider, ArtFilesAlbumProvider, \
    ArtFilesSongProvider
from lib.providers.fanarttv import FanartTVAlbumProvider, FanartTVArtistProvider, FanartTVSeriesProvider, \
    FanartTVMovieProvider, FanartTVMovieSetProvider, FanartTVMusicVideoProvider
from lib.providers.nfofile import NFOFileSeriesProvider, NFOFileMovieProvider, NFOFileEpisodeProvider, \
    NFOFileMovieSetProvider, NFOFileMusicVideoProvider
from lib.providers.theaudiodb import TheAudioDBAlbumProvider, TheAudioDBArtistProvider, TheAudioDBMusicVideoProvider, \
    TheAudioDBSongProvider, TheAudioDBSearch
from lib.providers.themoviedb import TheMovieDBMovieProvider, TheMovieDBEpisodeProvider, TheMovieDBMovieSetProvider, \
    TheMovieDBSearch
from lib.providers.thetvdbv2 import TheTVDBProvider
from lib.providers.videofile import VideoFileMovieProvider, VideoFileEpisodeProvider, VideoFileMusicVideoProvider

external = {
    mediatypes.TVSHOW: (TheTVDBProvider(), FanartTVSeriesProvider()),
    mediatypes.MOVIE: (TheMovieDBMovieProvider(), FanartTVMovieProvider()),
    mediatypes.MOVIESET: (TheMovieDBMovieSetProvider(), FanartTVMovieSetProvider()),
    mediatypes.EPISODE: (TheMovieDBEpisodeProvider(),),
    mediatypes.MUSICVIDEO: (TheAudioDBMusicVideoProvider(), FanartTVMusicVideoProvider()),
    mediatypes.ARTIST: (TheAudioDBArtistProvider(), FanartTVArtistProvider()),
    mediatypes.ALBUM: (TheAudioDBAlbumProvider(), FanartTVAlbumProvider()),
    mediatypes.SONG: (TheAudioDBSongProvider(),)
}

forced = {
    mediatypes.TVSHOW: (ArtFilesSeriesProvider(), NFOFileSeriesProvider()),
    mediatypes.MOVIE: (ArtFilesMovieProvider(), NFOFileMovieProvider(), VideoFileMovieProvider()),
    mediatypes.MOVIESET: (ArtFilesMovieSetProvider(), NFOFileMovieSetProvider()),
    mediatypes.EPISODE: (ArtFilesEpisodeProvider(), NFOFileEpisodeProvider(), VideoFileEpisodeProvider()),
    mediatypes.MUSICVIDEO: (ArtFilesMusicVideoProvider(), NFOFileMusicVideoProvider(), VideoFileMusicVideoProvider()),
    mediatypes.ARTIST: (ArtFilesArtistProvider(),),
    mediatypes.ALBUM: (ArtFilesAlbumProvider(),),
    mediatypes.SONG: (ArtFilesSongProvider(),)
}

_tmdbsearch = TheMovieDBSearch()
search = {mediatypes.MOVIESET: _tmdbsearch, mediatypes.MUSICVIDEO: TheAudioDBSearch(), mediatypes.TVSHOW: _tmdbsearch}
del _tmdbsearch
