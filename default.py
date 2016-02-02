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
    processor = ArtworkProcessor()
    if command.get('dbid'):
        mode = command.get('mode', 'auto')
        if mode == 'autoepisodes':
            processor.process_allepisodes(int(command['dbid']))
        elif command.get('mediatype'):
            processor.process_item(command['mediatype'], int(command['dbid']), mode)
    else:
        options = [None, 'settings...']
        processing = processor.processing
        if processing:
            options[0] = 'stop current process'
        else:
            options[0] = 'grab artwork for...'
        selected = xbmcgui.Dialog().select('Artwork Beef', options)
        if selected == 0:
            if processing:
                pykodi.execute_builtin('NotifyAll(script.artwork.beef, CancelCurrent)')
            else:
                handle_grab_artwork()
        elif selected == 1:
            xbmcgui.Dialog().ok('Artwork Beef', 'No can do, boss.')

def handle_grab_artwork():
    options = ['new items', 'all items']
    selected = xbmcgui.Dialog().select('Artwork Beef: grab artwork for...', options)
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
