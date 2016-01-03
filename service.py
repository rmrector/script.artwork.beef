import xbmc
import sys

from devhelper import pykodi
from devhelper import quickjson

from devhelper.pykodi import log

addon = pykodi.Addon()
sys.path.append(addon.resourcelibs)

from artworkprocessor import ArtworkProcessor

def doit():
    item = quickjson.get_tvshows('random', limit=1, properties=['art', 'imdbnumber'])
    # item = [quickjson.get_tvshow_details(1957, properties=['art', 'imdbnumber'])]
    # item = quickjson.get_movies('random', limit=1, properties=['art', 'imdbnumber'])
    processor.process_medialist(item)

if __name__ == '__main__':
    log('Service started', xbmc.LOGINFO)
    processor = ArtworkProcessor()
    try:
        monitor = xbmc.Monitor()
        # the service can't watch for VideoLibrary.OnUpdate, as that is spit out once or twice every time a video plays, I want OnAdd
        # Probably just wait for OnScanStarted, then use sorted and filtered json requests
        doit()
        while not monitor.waitForAbort(10):
            doit()
    finally:
        del monitor

    log('Service stopped', xbmc.LOGINFO)
