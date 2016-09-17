import sys
import xbmc
import xbmcgui

from devhelper import pykodi
from devhelper import quickjson

addon = pykodi.get_main_addon()
sys.path.append(addon.resourcelibs)

from utils import localize as L

ADD_MISSING_HEADER = 32401
ADD_MISSING_MESSAGE = 32402

STOP = 32403
ADD_MISSING_FOR_NEW = 32404
ADD_MISSING_FOR_ALL = 32405
from artworkprocessor import ArtworkProcessor
from seriesselection import SeriesSelector

def main():
    command = get_command()
    processor = ArtworkProcessor()
    if command.get('dbid'):
        mode = command.get('mode', 'auto')
        if mode == 'autoepisodes':
            processor.process_allepisodes(int(command['dbid']))
        elif command.get('mediatype'):
            processor.process_item(command['mediatype'], int(command['dbid']), mode)
    elif command.get('command') == 'set_autoaddepisodes':
        set_autoaddepisodes()
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

def get_command():
    command = {}
    for x in range(1, len(sys.argv)):
        arg = sys.argv[x].split("=")
        command[arg[0].strip().lower()] = arg[1].strip() if len(arg) > 1 else True

    return command

if __name__ == '__main__':
    main()
