import json
import os

class ProcessedItems(object):
    def __init__(self, directory):
        self.tvshow = []
        self.movie = []
        self.episode = []
        self.filename = os.path.join(directory, 'processeditems.json')

    def extend(self, extender):
        self.tvshow.extend(extender.get('tvshow', ()))
        self.movie.extend(extender.get('movie', ()))
        self.episode.extend(extender.get('episode', ()))

    def set(self, setter):
        self.tvshow = setter.get('tvshow', [])
        self.movie = setter.get('movie', [])
        self.episode = setter.get('episode', [])

    def clear(self):
        self.tvshow = []
        self.movie = []
        self.episode = []

    def save(self):
        with open(self.filename, 'w') as jsonfile:
            json.dump({'tvshow': self.tvshow, 'movie': self.movie, 'episode': self.episode}, jsonfile)

    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as jsonfile:
                try:
                    processed = json.load(jsonfile)
                except ValueError:
                    return
                self.tvshow = processed.get('tvshow', [])
                self.movie = processed.get('movie', [])
                self.episode = processed.get('episode', [])
