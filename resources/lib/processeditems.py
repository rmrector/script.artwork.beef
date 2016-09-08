import sys
import xbmc
import xbmcvfs
from contextlib import closing

if sys.version_info < (2, 7):
    import simplejson as json
else:
    import json

from devhelper.pykodi import log

class ProcessedItems(object):
    version = 1
    def __init__(self, directory):
        self.tvshow = {}
        self.movie = []
        self.episode = []
        self.filename = directory + 'processeditems.json'
        self.load()

    def extend(self, extender):
        for tvshowid, seasons in extender.get('tvshow', {}).iteritems():
            if seasons > self.tvshow.get(tvshowid):
                self.tvshow[tvshowid] = seasons
        self.movie.extend(extender.get('movie', ()))
        self.episode.extend(extender.get('episode', ()))

    def set(self, setter):
        self.tvshow = setter.get('tvshow', {})
        self.movie = setter.get('movie', [])
        self.episode = setter.get('episode', [])

    def clear(self):
        self.tvshow = {}
        self.movie = []
        self.episode = []

    def save(self):
        with closing(xbmcvfs.File(self.filename, 'w')) as jsonfile:
            json.dump({'tvshow': self.tvshow, 'movie': self.movie, 'episode': self.episode, 'version': self.version}, jsonfile)

    def load(self):
        self.clear()
        if xbmcvfs.exists(self.filename):
            with closing(xbmcvfs.File(self.filename)) as jsonfile:
                try:
                    processed = json.load(jsonfile)
                except ValueError:
                    log("Had trouble loading ProcessedItems, starting fresh.", xbmc.LOGWARNING, tag='json')
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
