import sqlite3
import xbmc
import xbmcvfs

from lib.libs.addonsettings import settings

VERSION = 1
# DEPRECATED short 2017-08-26: `medialabel IS NULL` x3 is only for transitioning from VERSION = 0
#  maybe the first check in `_get_version` can go later on

class ProcessedItems(object):
    def __init__(self):
        # data is uniqueid for sets, last known season for TV shows, musicbrainz track/album/artist IDs for music videos
        self.db = Database('processeditems', upgrade_processeditems)

    def is_stale(self, mediaid, mediatype, medialabel):
        result = self.db.fetchone("""SELECT * FROM processeditems WHERE mediaid=? AND mediatype=?
            AND (medialabel=? or medialabel IS NULL) AND nextdate > datetime('now')""", (mediaid, mediatype, medialabel))
        return True if not result else False

    def set_nextdate(self, mediaid, mediatype, medialabel, nextdate):
        exists = self._key_exists(mediaid, mediatype)
        scriptbit = "datetime('{0}')".format(nextdate) if nextdate else 'null'
        script = "UPDATE processeditems SET nextdate={0}, medialabel=? WHERE mediaid=? AND mediatype=?" if exists \
            else "INSERT INTO processeditems (nextdate, medialabel, mediaid, mediatype) VALUES ({0}, ?, ?, ?)"
        self.db.execute(script.format(scriptbit), (medialabel, mediaid, mediatype))

    def get_data(self, mediaid, mediatype, medialabel):
        result = self.db.fetchone("""SELECT * FROM processeditems WHERE mediaid=? AND mediatype=?
            AND (medialabel=? or medialabel IS NULL)""", (mediaid, mediatype, medialabel))
        if result:
            return result['data']

    def set_data(self, mediaid, mediatype, medialabel, data):
        exists = self._key_exists(mediaid, mediatype)
        script = "UPDATE processeditems SET data=?, medialabel=? WHERE mediaid=? AND mediatype=?" if exists \
            else "INSERT INTO processeditems (data, medialabel, mediaid, mediatype) VALUES (?, ?, ?, ?)"
        self.db.execute(script, (data, medialabel, mediaid, mediatype))

    def exists(self, mediaid, mediatype, medialabel):
        return bool(self.db.fetchone("""SELECT * FROM processeditems WHERE mediaid=? AND mediatype=?
            AND (medialabel=? or medialabel IS NULL)""", (mediaid, mediatype, medialabel)))

    def does_not_exist(self, mediaid, mediatype, medialabel):
        return not self.exists(mediaid, mediatype, medialabel)

    def _key_exists(self, mediaid, mediatype):
        return bool(self.db.fetchone("SELECT * FROM processeditems WHERE mediaid=? AND mediatype=?",
            (mediaid, mediatype)))

def upgrade_processeditems(db, fromversion):
    if fromversion == VERSION:
        return VERSION

    if fromversion == -1:
        # new install, build the database fresh
        db.execute("""CREATE TABLE processeditems (mediaid INTEGER NOT NULL, mediatype TEXT NOT NULL,
            medialabel TEXT, nextdate DATETIME, data TEXT, PRIMARY KEY (mediaid, mediatype))""")
        return VERSION

    workingversion = fromversion
    if workingversion == 0:
        db.execute("""ALTER TABLE processeditems ADD COLUMN medialabel TEXT""")
        workingversion = 1

    return workingversion

SETTINGS_TABLE_VALUE = 'database-settings'
# must be quoted to use as identifier
SETTINGS_TABLE = '"{0}"'.format(SETTINGS_TABLE_VALUE)

class Database(object):
    def __init__(self, databasename, upgrade_fn):
        dbpath = settings.datapath
        if not xbmcvfs.exists(dbpath):
            xbmcvfs.mkdir(dbpath)
        dbpath = xbmc.translatePath(dbpath + databasename + '.db')
        self._conn = sqlite3.connect(dbpath)
        self._conn.row_factory = sqlite3.Row
        self._conn.text_factory = str
        self._cursor = self._conn.cursor()
        self._setup(upgrade_fn)

    def execute(self, query, args=()):
        with self._conn:
            self._execute_raw(query, args)

    def executemany(self, *queriesandargs):
        with self._conn:
            for queryargs in queriesandargs:
                self._execute_raw(*queryargs)

    def fetchall(self, query, args=()):
        self._execute_raw(query, args)
        return self._cursor.fetchall()

    def fetchone(self, query, args=()):
        self._execute_raw(query, args)
        return self._cursor.fetchone()

    def _execute_raw(self, query, args=()):
        self._cursor.execute(query, args)

    def _setup(self, upgrade_fn):
        version = self._get_version()
        newversion = upgrade_fn(self, version)
        if version != newversion:
            self._update_version(newversion)

    def _build_settings(self, version=-1):
        self.executemany(
            ("CREATE TABLE {0} (name TEXT PRIMARY KEY NOT NULL, value TEXT)".format(SETTINGS_TABLE),),
            ("INSERT INTO {0} (name, value) VALUES ('database version', ?)".format(SETTINGS_TABLE), (str(version),))
        )

    def _get_version(self):
        if not self.fetchone("SELECT name FROM sqlite_master WHERE type='table' AND name='processeditems'"):
            self._build_settings()
            return -1 # for future databases, this check goes away ...
        if not self.fetchone("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (SETTINGS_TABLE_VALUE,)):
            self._build_settings(0) # ... and this is empty
            return 0 # and returns -1

        return int(self._get_setting_value('database version', 0))

    def _get_setting_value(self, settingname, default=None):
        result = self.fetchone("SELECT value FROM {0} WHERE name=?".format(SETTINGS_TABLE), (settingname,))
        if not result:
            return default
        return result['value']

    def _update_version(self, newversion):
        exists = bool(self.fetchone("SELECT * FROM {0} WHERE name='database version'".format(SETTINGS_TABLE)))
        script = "UPDATE {0} SET value=? WHERE name=?" if exists else "INSERT INTO {0} (value, name) VALUES (?, ?)"
        self.execute(script.format(SETTINGS_TABLE), (str(newversion), 'database version'))
