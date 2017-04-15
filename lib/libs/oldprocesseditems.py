import xbmcvfs
from contextlib import closing

from lib.libs.pykodi import json

class ProcessedItems(object):
    version = 1
    def __init__(self, directory):
        self.tvshow = {}
        self.movie = []
        self.episode = []
        self.filename = directory + 'processeditems.json'

    @property
    def exists(self):
        return xbmcvfs.exists(self.filename)

    def delete(self):
        if self.exists:
            xbmcvfs.delete(self.filename)

    def load(self):
        if self.exists:
            with closing(xbmcvfs.File(self.filename)) as jsonfile:
                try:
                    processed = json.load(jsonfile)
                except ValueError:
                    return

                if processed.get('version') == self.version:
                    tvshows = processed.get('tvshow')
                    if isinstance(tvshows, dict):
                        self.tvshow = dict((int(tvshowid), seasons) for tvshowid, seasons
                            in tvshows.iteritems())
                movies = processed.get('movie')
                if isinstance(movies, list):
                    self.movie = movies
                episodes = processed.get('episode')
                if isinstance(episodes, list):
                    self.episode = episodes
