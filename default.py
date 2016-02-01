import sys
import xbmcgui

from devhelper import pykodi

addon = pykodi.Addon()
sys.path.append(addon.resourcelibs)

from artworkprocessor import ArtworkProcessor

def main():
    # TODO: Start from program pops up a select list with some options.
    # Like scan -> new / all, settings -> select series for auto grabbing episode art
    command = get_command()
    if command.get('dbid'):
        processor = ArtworkProcessor()
        mode = command.get('mode', 'auto')
        if mode == 'autoepisodes':
            processor.process_allepisodes(int(command['dbid']))
        elif command.get('mediatype'):
            processor.process_item(command['mediatype'], int(command['dbid']), mode)
    else:
        options = ['grab artwork for new items', 'grab artwork for all items', 'select series to auto grab episode art', 'stop current operation']
        selected = xbmcgui.Dialog().select('Artwork Beef', options)
        if selected == 0:
            pykodi.execute_builtin('NotifyAll(script.artwork.beef, ProcessNewItems)')
        if selected == 1:
            pykodi.execute_builtin('NotifyAll(script.artwork.beef, ProcessAllItems)')
        elif selected == 2:
            xbmcgui.Dialog().ok('Artwork Beef', 'No can do, boss.')
        elif selected == 3:
            pykodi.execute_builtin('NotifyAll(script.artwork.beef, CancelCurrent)')

def get_command():
    command = {}
    for x in range(1, len(sys.argv)):
        arg = sys.argv[x].split("=")
        command[arg[0].strip().lower()] = arg[1].strip() if len(arg) > 1 else True

    return command

if __name__ == '__main__':
    main()
