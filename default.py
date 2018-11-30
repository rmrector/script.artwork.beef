import sys
import xbmc
import xbmcgui
from itertools import chain

from lib import advancedsettings, cleaner, reporting
from lib.artworkprocessor import ArtworkProcessor
from lib.filemanager import FileManager, FileError
from lib.libs import mediainfo as info, mediatypes, pykodi, quickjson, utils
from lib.libs.addonsettings import settings
from lib.libs.processeditems import ProcessedItems
from lib.libs.pykodi import localize as L, log, get_kodi_version
from lib.providers import search
from lib.seriesselection import SeriesSelector

class M(object):
    ADD_MISSING_HEADER = 32401
    ADD_MISSING_MESSAGE = 32402
    STOP = 32403
    ADD_MISSING_FOR = 32416
    FOR_NEW_VIDEOS = 32417
    FOR_OLD_VIDEOS = 32418
    FOR_ALL_VIDEOS = 32419
    FOR_NEW_AUDIO = 32420
    FOR_OLD_AUDIO = 32421
    FOR_ALL_AUDIO = 32422
    IDENTIFY_UNMATCHED_SETS = 32408
    IDENTIFY_UNMATCHED_MVIDS = 32415
    REMOVE_SPECIFIC_TYPES = 32414
    MAKE_LOCAL = 32423
    CACHE_VIDEO_ARTWORK = 32424
    CACHE_MUSIC_ARTWORK = 32425
    DOWNLOAD_COUNT = 32816
    CACHED_COUNT = 32038
    REMOVED_ART_COUNT = 32027
    NO_UNMATCHED_ITEMS = 32029
    UNMATCHED_ITEMS = 32056
    REPORT_TITLE = 32007
    VERSION_REQUIRED = 32026
    REMOTE_CONTROL_REQUIRED = 32039
    NEW_LOCAL_FILES = 32431

    SAVE_ARTTYPES_TO_ASXML = 32650
    RESTORE_ASXML_BACKUP = 32651
    INTRO_TEXT = 32652
    INCLUDE_MULTIPLES = 32653

    LISTING_ALL = 32028
    MOVIES = 36901
    SERIES = 36903
    SEASONS = 36905
    EPISODES = 36907
    MOVIESETS = 36911
    MUSICVIDEOS = 36909
    ARTISTS = 36917
    ALBUMS = 36919
    SONGS = 36921

def main():
    settings.update_settings()
    mediatypes.update_settings()
    command = get_command()
    if command.get('dbid') and command.get('mediatype'):
        processor = ArtworkProcessor()
        processor.process_item(command['mediatype'], int(command['dbid']), command.get('mode', 'auto'))
    elif 'command' in command:
        if command['command'] == 'set_autoaddepisodes':
            set_autoaddepisodes()
        elif command['command'] == 'show_artwork_log':
            show_artwork_log()
        elif command['command'] == 'set_download_artwork' and command.get('mediatype'):
            set_download_artwork(command['mediatype'])
    else:
        processor = ArtworkProcessor()
        if processor.processor_busy:
            options = [(L(M.STOP), 'NotifyAll(script.artwork.beef:control, CancelCurrent)')]
        else:
            options = [(L(M.ADD_MISSING_FOR), add_missing_for),
                (L(M.NEW_LOCAL_FILES), 'NotifyAll(script.artwork.beef:control, ProcessLocalVideos)'),
                (L(M.IDENTIFY_UNMATCHED_SETS), lambda: identify_unmatched(mediatypes.MOVIESET)),
                (L(M.IDENTIFY_UNMATCHED_MVIDS), lambda: identify_unmatched(mediatypes.MUSICVIDEO)),
                (L(M.REMOVE_SPECIFIC_TYPES), remove_specific_arttypes),
                (L(M.MAKE_LOCAL), make_local),
                (L(M.CACHE_VIDEO_ARTWORK), cache_artwork)]
            if get_kodi_version() >= 18:
                options.append((L(M.CACHE_MUSIC_ARTWORK), lambda: cache_artwork('music')))
                options.append((L(M.SAVE_ARTTYPES_TO_ASXML), save_arttypes_to_asxml))
                if advancedsettings.has_backup():
                    options.append((L(M.RESTORE_ASXML_BACKUP), advancedsettings.restore_backup))
        selected = xbmcgui.Dialog().select('Artwork Beef', [option[0] for option in options])
        if selected >= 0 and selected < len(options):
            action = options[selected][1]
            if isinstance(action, basestring):
                pykodi.execute_builtin(action)
            else:
                action()

def notify_count(message, count):
    countmessage = message.format(count)
    log(countmessage, xbmc.LOGINFO)
    xbmcgui.Dialog().notification('Artwork Beef', countmessage)

def add_missing_for():
    options = [(L(M.FOR_NEW_VIDEOS), 'ProcessNewVideos'), (L(M.FOR_OLD_VIDEOS), 'ProcessNewAndOldVideos'),
        (L(M.FOR_ALL_VIDEOS), 'ProcessAllVideos')]
    if get_kodi_version() >= 18:
        options.extend(((L(M.FOR_NEW_AUDIO), 'ProcessNewMusic'), (L(M.FOR_OLD_AUDIO), 'ProcessNewAndOldMusic'),
            (L(M.FOR_ALL_AUDIO), 'ProcessAllMusic')))

    selected = xbmcgui.Dialog().select(L(M.ADD_MISSING_FOR), [option[0] for option in options])
    if selected >= 0 and selected < len(options):
        pykodi.execute_builtin('NotifyAll(script.artwork.beef:control, {0})'.format(options[selected][1]))

def remove_specific_arttypes():
    options = [(L(M.MOVIES), lambda: quickjson.get_item_list(mediatypes.MOVIE), mediatypes.MOVIE),
        (L(M.SERIES), quickjson.get_tvshows, mediatypes.TVSHOW),
        (L(M.SEASONS), quickjson.get_seasons, mediatypes.SEASON),
        (L(M.MOVIESETS), lambda: quickjson.get_item_list(mediatypes.MOVIESET), mediatypes.MOVIESET),
        (L(M.EPISODES), quickjson.get_episodes, mediatypes.EPISODE),
        (L(M.MUSICVIDEOS), lambda: quickjson.get_item_list(mediatypes.MUSICVIDEO), mediatypes.MUSICVIDEO)]
    if get_kodi_version() >= 18:
        options.extend(((L(M.ARTISTS), lambda: quickjson.get_item_list(mediatypes.ARTIST), mediatypes.ARTIST),
            (L(M.ALBUMS), lambda: quickjson.get_item_list(mediatypes.ALBUM), mediatypes.ALBUM),
            (L(M.SONGS), lambda: quickjson.get_item_list(mediatypes.SONG), mediatypes.SONG)))

    selected = xbmcgui.Dialog().select(L(M.REMOVE_SPECIFIC_TYPES), [option[0] + " ..." for option in options])
    if selected < 0 or selected >= len(options):
        return
    busy = pykodi.get_busydialog()
    busy.create()
    allitems = options[selected][1]()
    counter = {}
    types_to_remove = set()
    for arttype, url in chain.from_iterable(d.get('art', {}).iteritems() for d in allitems):
        if '.' in arttype: continue
        counter['* all'] = counter.get('* all', 0) + 1
        counter[arttype] = counter.get(arttype, 0) + 1
        if not info.keep_arttype(options[selected][2], arttype, url):
            types_to_remove.add(arttype)
            counter['* nowhitelist'] = counter.get('* nowhitelist', 0) + 1

    arttypes = sorted(counter.keys())
    busy.close()
    ftype = lambda intype: '* ' + ', '.join(sorted(types_to_remove)) if intype == '* nowhitelist' else intype
    selectedarttype = xbmcgui.Dialog().select(options[selected][0],
        ["{0}: {1}".format(ftype(arttype), counter[arttype]) for arttype in arttypes])
    if selectedarttype >= 0 and selectedarttype < len(arttypes):
        def removetypes(mediaitem):
            changedart = cleaner.remove_specific_arttype(mediaitem, arttypes[selectedarttype])
            info.remove_local_from_texturecache((mediaitem.art[arttype] for arttype in changedart), True)
            return changedart
        fixcount = runon_medialist(removetypes, L(M.REMOVE_SPECIFIC_TYPES), allitems, options[selected][0])
        notify_count(L(M.REMOVED_ART_COUNT), fixcount)

def make_local():
    fileman = FileManager()
    def downloadforitem(mediaitem):
        try:
            fileman.downloadfor(mediaitem)
            newart = dict((k, v) for k, v in mediaitem.downloadedart.iteritems()
                if not v or not v.startswith('http'))
            for arttype in newart:
                # remove old URL from texture cache
                if mediaitem.art.get(arttype, '').startswith('http'):
                    quickjson.remove_texture_byurl(mediaitem.art[arttype])
            return newart
        except FileError as ex:
            mediaitem.error = ex.message
            log(ex.message, xbmc.LOGERROR)
            xbmcgui.Dialog().notification("Artwork Beef", ex.message, xbmcgui.NOTIFICATION_ERROR)
            return {}
    downloaded = runon_medialist(downloadforitem, L(M.MAKE_LOCAL), fg=True)
    xbmcgui.Dialog().ok("Artwork Beef", L(M.DOWNLOAD_COUNT).format(downloaded)
        + ' - {0:0.2f}MB'.format(fileman.size / 1000000.00))

def cache_artwork(librarytype='videos'):
    fileman = FileManager(False, True)
    if not fileman.imagecachebase:
        xbmcgui.Dialog().notification("Artwork Beef", L(M.REMOTE_CONTROL_REQUIRED),
            xbmcgui.NOTIFICATION_WARNING)
        return
    heading = L(M.CACHE_VIDEO_ARTWORK if librarytype == 'videos' else M.CACHE_MUSIC_ARTWORK)
    cached = runon_medialist(lambda mi: fileman.cachefor(mi.art, True), heading, librarytype, fg=True)
    xbmcgui.Dialog().ok("Artwork Beef", L(M.CACHED_COUNT).format(cached))

def identify_unmatched(mediatype):
    busy = pykodi.get_busydialog()
    busy.create()
    processed = ProcessedItems()
    ulist = quickjson.get_item_list(mediatype)
    if mediatype == mediatypes.MUSICVIDEO:
        for item in ulist:
            item['label'] = info.build_music_label(item)
    unmatched = [item for item in ulist if not processed.get_data(item[mediatype + 'id'], mediatype, item['label'])]
    busy.close()
    if unmatched:
        selected = xbmcgui.Dialog().select(L(M.UNMATCHED_ITEMS), [item['label'] for item in unmatched])
        if selected < 0:
            return # Cancelled
        mediaitem = info.MediaItem(unmatched[selected])
        info.add_additional_iteminfo(mediaitem, processed, search)
        processor = ArtworkProcessor()
        if processor.manual_id(mediaitem):
            processor.process_item(mediatype, mediaitem.dbid, 'auto')
    else:
        xbmcgui.Dialog().notification("Artwork Beef", L(M.NO_UNMATCHED_ITEMS), xbmcgui.NOTIFICATION_INFO)

def set_download_artwork(mediatype):
    if mediatype not in mediatypes.artinfo:
        return
    options = list((x for x, y in mediatypes.artinfo[mediatype].items() if y['autolimit']))
    options.extend(mediatypes.othertypes[mediatype])
    pykodi.get_main_addon().set_setting(mediatype + '.download_arttypes', ', '.join(options))

def save_arttypes_to_asxml():
    can_continue = xbmcgui.Dialog().ok("Artwork Beef", L(M.INTRO_TEXT))
    if not can_continue:
        return
    include_multiple = xbmcgui.Dialog().yesno("Artwork Beef", L(M.INCLUDE_MULTIPLES))
    art_toset = {}
    for mediatype in mediatypes.artinfo:
        if include_multiple:
            art_toset[mediatype] = list(mediatypes.iter_every_arttype(mediatype))
        else:
            art_toset[mediatype] = [a for a in mediatypes.iter_every_arttype(mediatype)
                if not a[-1].isdigit()]

    advancedsettings.save_arttypes(art_toset)

def show_artwork_log():
    if pykodi.get_kodi_version() < 16:
        xbmcgui.Dialog().notification("Artwork Beef", L(M.VERSION_REQUIRED).format("Kodi 16"), xbmcgui.NOTIFICATION_INFO)
        return
    xbmcgui.Dialog().textviewer("Artwork Beef: " + L(M.REPORT_TITLE), reporting.get_latest_report())

def set_autoaddepisodes():
    busy = pykodi.get_busydialog()
    busy.create()
    serieslist = [series for series in quickjson.get_tvshows(True) if series.get('imdbnumber')]
    busy.close()
    selected = SeriesSelector('DialogSelect.xml', settings.addon_path, serieslist=serieslist, selected=settings.autoadd_episodes).prompt()
    if selected != settings.autoadd_episodes:
        settings.autoadd_episodes = selected
        if xbmcgui.Dialog().yesno(L(M.ADD_MISSING_HEADER), L(M.ADD_MISSING_MESSAGE)):
            pykodi.execute_builtin('NotifyAll(script.artwork.beef:control, ProcessAfterSettings)')

def runon_medialist(function, heading, medialist='videos', typelabel=None, fg=False):
    progress = xbmcgui.DialogProgress() if fg else xbmcgui.DialogProgressBG()
    progress.create(heading)
    monitor = xbmc.Monitor()

    if medialist == 'videos':
        steps_to_run = [(lambda: quickjson.get_item_list(mediatypes.MOVIE), L(M.MOVIES)),
            (info.get_cached_tvshows, L(M.SERIES)),
            (quickjson.get_seasons, L(M.SEASONS)),
            (lambda: quickjson.get_item_list(mediatypes.MOVIESET), L(M.MOVIESETS)),
            (quickjson.get_episodes, L(M.EPISODES)),
            (lambda: quickjson.get_item_list(mediatypes.MUSICVIDEO), L(M.MUSICVIDEOS))]
    elif medialist == 'music' and get_kodi_version() >= 18:
        steps_to_run = [(lambda: quickjson.get_item_list(mediatypes.ARTIST), L(M.ARTISTS)),
            (lambda: quickjson.get_item_list(mediatypes.ALBUM), L(M.ALBUMS)),
            (lambda: quickjson.get_item_list(mediatypes.SONG), L(M.SONGS))]
    else:
        steps_to_run = ((lambda: medialist, typelabel),)
    stepsize = 100 // len(steps_to_run)

    def update_art_for_items(items, start):
        changedcount = 0
        for i, item in enumerate(items):
            if fg:
                progress.update(start + i * stepsize // len(items), item['label'])
            else:
                progress.update(start + i * stepsize // len(items))
            item = info.MediaItem(item)
            if item.mediatype == mediatypes.SEASON:
                item.file = info.get_cached_tvshow(item.tvshowid)['file']
            updates = function(item)
            if isinstance(updates, int):
                changedcount += updates
            else:
                processed = utils.get_simpledict_updates(item.art, updates)
                if processed:
                    info.update_art_in_library(item.mediatype, item.dbid, processed)
                    changedcount += len(processed)
            if monitor.abortRequested() or fg and progress.iscanceled():
                break
        return changedcount

    fixcount = 0
    for i, (list_fn, listtype) in enumerate(steps_to_run):
        start = i * stepsize
        if fg:
            progress.update(start, line1=L(M.LISTING_ALL).format(listtype))
        else:
            progress.update(start, message=L(M.LISTING_ALL).format(listtype))
        fixcount += update_art_for_items(list_fn(), start)
        if monitor.abortRequested() or fg and progress.iscanceled():
            break

    info.clear_cache()
    progress.close()
    return fixcount

def get_command():
    command = {}
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i].split("=")
        command[arg[0].strip().lower()] = arg[1].strip() if len(arg) > 1 else True

    return command

if __name__ == '__main__':
    main()
