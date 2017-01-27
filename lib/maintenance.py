import random
from datetime import timedelta

from libs import mediatypes, pykodi
from libs.oldprocesseditems import ProcessedItems as OldProcessedItems
from libs.processeditems import ProcessedItems
from libs.pykodi import datetime_strptime, log

def check_upgrades():
    check_processeditems_upgrade()

def check_processeditems_upgrade():
    addon = pykodi.get_main_addon()
    old = OldProcessedItems(addon.datapath)
    if not old.exists:
        return

    old.load()
    processed = ProcessedItems()
    lastalldate = addon.get_setting('lastalldate')
    if not lastalldate or lastalldate == '0':
        old.delete()
        return

    log("Converting old processeditems.json to new processeditems.db")
    if '.' in lastalldate:
        lastalldate = lastalldate[:lastalldate.index('.')]
    lastalldate = datetime_strptime(lastalldate, '%Y-%m-%d %H:%M:%S')
    for movieid in old.movie:
        if not processed.exists(movieid, mediatypes.MOVIE):
            nextdate = lastalldate + timedelta(days=60 + random.randrange(-10, 11))
            processed.set_nextdate(movieid, mediatypes.MOVIE, nextdate)
    for episodeid in old.episode:
        if not processed.exists(episodeid, mediatypes.EPISODE):
            nextdate = lastalldate + timedelta(days=60 + random.randrange(-10, 11))
            processed.set_nextdate(episodeid, mediatypes.EPISODE, nextdate)
    for tvshowid, season in old.tvshow.iteritems():
        tvshowid = int(tvshowid)
        if not processed.exists(tvshowid, mediatypes.TVSHOW):
            nextdate = lastalldate + timedelta(days=60 + random.randrange(-10, 11))
            processed.set_nextdate(tvshowid, mediatypes.TVSHOW, nextdate)
            processed.set_data(tvshowid, mediatypes.TVSHOW, season)

    old.delete()
    addon.set_setting('lastalldate', '')
    addon.set_setting('lastunprocesseddate', '')
    log("Done converting")
