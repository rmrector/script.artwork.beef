import sys
import xbmc
import xbmcgui

from lib import cleaner
from lib.artworkprocessor import ArtworkProcessor
from lib.seriesselection import SeriesSelector
from lib.libs import mediainfo, mediatypes, pykodi, quickjson
from lib.libs.processeditems import ProcessedItems
from lib.libs.pykodi import localize as L, log

addon = pykodi.get_main_addon()

class M(object):
    ADD_MISSING_HEADER = 32401
    ADD_MISSING_MESSAGE = 32402
    STOP = 32403
    ADD_MISSING_FOR_NEW = 32404
    ADD_MISSING_FOR_ALL = 32405
    IDENTIFY_UNMATCHED_SETS = 32408
    REMOVE_EXTRA_ARTWORK = 32407
    REMOVED_ART_COUNT = 32027
    NO_UNMATCHED_SETS = 32029
    UNMATCHED_SETS = 32056

    LISTING_ALL = 32028
    MOVIES = 36901
    SERIES = 36903
    SEASONS = 36905
    EPISODES = 36907
    MOVIESETS = 20434

def main():
    command = get_command()
    if command.get('dbid') and command.get('mediatype'):
        processor = ArtworkProcessor()
        processor.process_item(command['mediatype'], int(command['dbid']), command.get('mode', 'auto'))
    elif 'command' in command:
        if command['command'] == 'set_autoaddepisodes':
            set_autoaddepisodes()
        elif command['command'] == 'remove_otherartwork':
            runon_allmedia(L(M.REMOVE_EXTRA_ARTWORK), L(M.REMOVED_ART_COUNT), cleaner.remove_otherartwork)
    else:
        processor = ArtworkProcessor()
        if processor.processor_busy:
            options = [(L(M.STOP), 'NotifyAll(script.artwork.beef, CancelCurrent)')]
        else:
            options = [(L(M.ADD_MISSING_FOR_NEW), 'NotifyAll(script.artwork.beef, ProcessNewItems)'),
                (L(M.ADD_MISSING_FOR_ALL), 'NotifyAll(script.artwork.beef, ProcessAllItems)'),
                (L(M.IDENTIFY_UNMATCHED_SETS), identify_unmatched_sets)]
        selected = xbmcgui.Dialog().select('Artwork Beef', [option[0] for option in options])
        if selected >= 0 and selected < len(options):
            action = options[selected][1]
            if isinstance(action, basestring):
                pykodi.execute_builtin(action)
            else:
                action()

def identify_unmatched_sets():
    busy = pykodi.get_busydialog()
    busy.create()
    processed = ProcessedItems()
    unmatched = [mset for mset in quickjson.get_moviesets() if not processed.get_data(mset['setid'], 'set')]
    busy.close()
    if unmatched:
        selected = xbmcgui.Dialog().select(L(M.UNMATCHED_SETS), [mset['label'] for mset in unmatched])
        if selected < 0:
            return # Cancelled
        mediaitem = unmatched[selected]
        processor = ArtworkProcessor()
        if processor.identify_movieset(mediaitem):
            processor.process_item(mediatypes.MOVIESET, mediaitem['setid'], 'auto')
    else:
        xbmcgui.Dialog().notification("Artwork Beef", L(M.NO_UNMATCHED_SETS), xbmcgui.NOTIFICATION_INFO)

def set_autoaddepisodes():
    busy = pykodi.get_busydialog()
    busy.create()
    serieslist = [series for series in quickjson.get_tvshows(True) if series.get('imdbnumber')]
    autoaddepisodes = addon.get_setting('autoaddepisodes_list')
    busy.close()
    selected = SeriesSelector('DialogSelect.xml', addon.path, serieslist=serieslist, selected=autoaddepisodes).prompt()
    addon.set_setting('autoaddepisodes_list', selected)
    if selected != autoaddepisodes:
        if xbmcgui.Dialog().yesno(L(M.ADD_MISSING_HEADER), L(M.ADD_MISSING_MESSAGE)):
            pykodi.execute_builtin('NotifyAll(script.artwork.beef, ProcessAfterSettings)')

def runon_allmedia(heading, countmessage, function):
    progress = xbmcgui.DialogProgressBG()
    progress.create(heading)
    monitor = xbmc.Monitor()

    steps_to_run = ((quickjson.get_movies, L(M.LISTING_ALL).format(L(M.MOVIES))),
            (quickjson.get_tvshows, L(M.LISTING_ALL).format(L(M.SERIES))),
            (quickjson.get_seasons, L(M.LISTING_ALL).format(L(M.SEASONS))),
            (quickjson.get_moviesets, L(M.LISTING_ALL).format(L(M.MOVIESETS))),
            (quickjson.get_episodes, L(M.LISTING_ALL).format(L(M.EPISODES))))
    stepsize = 100 // len(steps_to_run)

    def update_art_for_items(items, start):
        changedcount = 0
        for i, item in enumerate(items):
            progress.update(start + i * stepsize // len(items))
            mediainfo.prepare_mediaitem(item)

            processed = function(item)
            processed = mediainfo.get_artwork_updates(item['art'], processed)
            if processed:
                mediainfo.update_art_in_library(item['mediatype'], item['dbid'], processed)
                changedcount += len(processed)
            if monitor.abortRequested():
                break
        return changedcount

    fixcount = 0
    for i, (listfunc, message) in enumerate(steps_to_run):
        start = i * stepsize
        progress.update(start, message=message)
        fixcount += update_art_for_items(listfunc(), start)
        if monitor.abortRequested():
            break
    progress.close()

    countmessage = countmessage.format(fixcount)
    log(countmessage, xbmc.LOGINFO)
    xbmcgui.Dialog().notification('Artwork Beef', countmessage)

def get_command():
    command = {}
    for x in range(1, len(sys.argv)):
        arg = sys.argv[x].split("=")
        command[arg[0].strip().lower()] = arg[1].strip() if len(arg) > 1 else True

    return command

if __name__ == '__main__':
    main()
