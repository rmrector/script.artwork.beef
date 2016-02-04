import sys
import xbmcgui

from devhelper import pykodi
from devhelper import quickjson

addon = pykodi.Addon()
sys.path.append(addon.resourcelibs)

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
        processing = processor.processing
        if processing:
            options = ['stop current process']
        else:
            options = ['add artwork for...']
        selected = xbmcgui.Dialog().select('Artwork Beef', options)
        if selected == 0:
            if processing:
                pykodi.execute_builtin('NotifyAll(script.artwork.beef, CancelCurrent)')
            else:
                show_add_artwork_menu()

def set_autoaddepisodes():
    serieslist = quickjson.get_tvshows()
    autoaddepisodes = addon.get_setting('autoaddepisodes_list')
    selected = SeriesSelector('DialogSelect.xml', addon.path, serieslist=serieslist, selected=autoaddepisodes).prompt()
    addon.set_setting('autoaddepisodes_list', selected)

def show_add_artwork_menu():
    options = ['new items', 'all items']
    selected = xbmcgui.Dialog().select('Artwork Beef: add artwork for...', options)
    if selected == 0:
        pykodi.execute_builtin('NotifyAll(script.artwork.beef, ProcessNewItems)')
    if selected == 1:
        pykodi.execute_builtin('NotifyAll(script.artwork.beef, ProcessAllItems)')

def get_command():
    command = {}
    for x in range(1, len(sys.argv)):
        arg = sys.argv[x].split("=")
        command[arg[0].strip().lower()] = arg[1].strip() if len(arg) > 1 else True

    return command

if __name__ == '__main__':
    main()
