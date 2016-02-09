import json
import os
import xbmc

from devhelper.pykodi import log

class ProcessedItems(object):
    version = 1
    def __init__(self, directory):
        self.tvshow = {}
        self.movie = []
        self.episode = []
        self.filename = os.path.join(directory, 'processeditems.json')

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
        with open(self.filename, 'w') as jsonfile:
            json.dump({'tvshow': self.tvshow, 'movie': self.movie, 'episode': self.episode, 'version': self.version}, jsonfile)

    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as jsonfile:
                try:
                    processed = json.load(jsonfile)
                except ValueError:
                    self.clear()
                    log("Had trouble loading ProcessedItems, starting fresh.", xbmc.LOGWARNING, tag='json')
                    return

                if processed.get('version') == self.version:
                    self.tvshow = dict((int(tvshowid), seasons) for tvshowid, seasons in processed.get('tvshow', {}).iteritems())
                else:
                    self.tvshow = {}
                self.movie = processed.get('movie', [])
                self.episode = processed.get('episode', [])
        else:
            self.clear()
