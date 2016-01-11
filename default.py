import sys

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
            processor.process_allartwork('episode', int(command['dbid']))
        elif command.get('mediatype'):
            processor.process_itemartwork(command['mediatype'], int(command['dbid']), mode)

def get_command():
    command = {}
    for x in range(1, len(sys.argv)):
        arg = sys.argv[x].split("=")
        command[arg[0].strip().lower()] = arg[1].strip() if len(arg) > 1 else True

    return command

if __name__ == '__main__':
    main()
