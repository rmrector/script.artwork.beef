import sys
import xbmc
import xbmcgui

from devhelper import pykodi
from devhelper import quickjson
from devhelper.pykodi import log

addon = pykodi.get_main_addon()
sys.path.append(addon.resourcelibs)

import cleaner
from artworkprocessor import ArtworkProcessor, update_cleaned_artwork
from utils import localize as L
from seriesselection import SeriesSelector

ADD_MISSING_HEADER = 32401
ADD_MISSING_MESSAGE = 32402
STOP = 32403
ADD_MISSING_FOR_NEW = 32404
ADD_MISSING_FOR_ALL = 32405
CLEAN_ART_URLS = 32406
FIXED_URL_COUNT = 32026

def main():
    command = get_command()
    processor = ArtworkProcessor()
    if command.get('dbid') and command.get('mediatype'):
        mode = command.get('mode', 'auto')
        processor.process_item(command['mediatype'], int(command['dbid']), mode)
    elif command.get('command') == 'set_autoaddepisodes':
        set_autoaddepisodes()
    elif command.get('command') == 'clean_arturls':
        clean_arturls()
    else:
        busy = processor.processor_busy
        if busy:
            options = [(L(STOP), 'NotifyAll(script.artwork.beef, CancelCurrent)')]
        else:
            options = [(L(ADD_MISSING_FOR_NEW), 'NotifyAll(script.artwork.beef, ProcessNewItems)'),
                (L(ADD_MISSING_FOR_ALL), 'NotifyAll(script.artwork.beef, ProcessAllItems)')]
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
        if xbmcgui.Dialog().yesno(L(ADD_MISSING_HEADER), L(ADD_MISSING_MESSAGE)):
            pykodi.execute_builtin('NotifyAll(script.artwork.beef, ProcessAfterSettings)')

def clean_arturls():
    progress = xbmcgui.DialogProgressBG()
    def clean_items(items, start):
        fixedcount = 0
        for i, item in enumerate(items):
            progress.update(start + i * 25 // len(items))
            itemart = dict((arttype, pykodi.unquoteimage(url)) for arttype, url in item['art'].iteritems())
            if 'episodeid' in item:
                itemart = dict((arttype, url) for arttype, url in itemart.iteritems() if '.' not in arttype)

            cleaned = cleaner.cleanartwork(itemart)
            if cleaned != itemart:
                fixedcount += count_changedkeys(itemart, cleaned)
                update_cleaned_artwork(item, cleaned)
        return fixedcount

    progress.create(L(CLEAN_ART_URLS), "Listing all movies")
    fixcount = clean_items(quickjson.get_movies(), 0)
    progress.update(25, message="Listing all series")
    fixcount += clean_items(quickjson.get_tvshows(), 25)
    progress.update(50, message="Listing all seasons")
    fixcount += clean_items(quickjson.get_seasons(), 50)
    progress.update(75, message="Listing all episodes")
    fixcount += clean_items(quickjson.get_episodes(), 75)
    progress.close()
    log(L(FIXED_URL_COUNT).format(fixcount), xbmc.LOGINFO)
    xbmcgui.Dialog().notification('Artwork Beef', L(FIXED_URL_COUNT).format(fixcount))

def count_changedkeys(d1, d2):
    result = sum(1 for key in d1 if d2.get(key) != d1[key])
    result += sum(1 for key in d2 if key not in d1)
    return result

def get_command():
    command = {}
    for x in range(1, len(sys.argv)):
        arg = sys.argv[x].split("=")
        command[arg[0].strip().lower()] = arg[1].strip() if len(arg) > 1 else True

    return command

if __name__ == '__main__':
    main()
