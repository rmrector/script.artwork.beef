import sys
import xbmc
import xbmcgui

from devhelper import pykodi
from devhelper import quickjson
from devhelper.pykodi import log

addon = pykodi.get_main_addon()
sys.path.append(addon.resourcelibs)

import cleaner
import mediainfo
from artworkprocessor import ArtworkProcessor
from utils import localize as L
from seriesselection import SeriesSelector

class M(object):
    ADD_MISSING_HEADER = 32401
    ADD_MISSING_MESSAGE = 32402
    STOP = 32403
    ADD_MISSING_FOR_NEW = 32404
    ADD_MISSING_FOR_ALL = 32405
    CLEAN_ART_URLS = 32406
    REMOVE_EXTRA_ARTWORK = 32407
    FIXED_URL_COUNT = 32026
    REMOVED_ART_COUNT = 32027

    LISTING_ALL = 32028
    MOVIES = 36901
    SERIES = 36903
    SEASONS = 36905
    EPISODES = 36907

def main():
    command = get_command()
    if command.get('dbid') and command.get('mediatype'):
        processor = ArtworkProcessor()
        processor.process_item(command['mediatype'], int(command['dbid']), command.get('mode', 'auto'))
    elif 'command' in command:
        if command['command'] == 'set_autoaddepisodes':
            set_autoaddepisodes()
        elif command['command'] == 'clean_arturls':
            runon_allmedia(L(M.CLEAN_ART_URLS), L(M.FIXED_URL_COUNT), cleaner.clean_artwork)
        elif command['command'] == 'remove_otherartwork':
            runon_allmedia(L(M.REMOVE_EXTRA_ARTWORK), L(M.REMOVED_ART_COUNT), cleaner.remove_otherartwork)
    else:
        processor = ArtworkProcessor()
        if processor.processor_busy:
            options = [(L(M.STOP), 'NotifyAll(script.artwork.beef, CancelCurrent)')]
        else:
            options = [(L(M.ADD_MISSING_FOR_NEW), 'NotifyAll(script.artwork.beef, ProcessNewItems)'),
                (L(M.ADD_MISSING_FOR_ALL), 'NotifyAll(script.artwork.beef, ProcessAllItems)')]
        selected = xbmcgui.Dialog().select('Artwork Beef', [option[0] for option in options])
        if selected >= 0 and selected < len(options):
            pykodi.execute_builtin(options[selected][1])

def set_autoaddepisodes():
    xbmc.executebuiltin('ActivateWindow(busydialog)')
    serieslist = [series for series in quickjson.get_tvshows() if series.get('imdbnumber')]
    autoaddepisodes = addon.get_setting('autoaddepisodes_list')
    xbmc.executebuiltin('Dialog.Close(busydialog)')
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
