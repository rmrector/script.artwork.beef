import sqlite3
import xbmc
import xbmcvfs

from lib.libs.pykodi import Addon

class ProcessedItems(object):
    def __init__(self):
        dbpath = Addon().datapath
        if not xbmcvfs.exists(dbpath):
            xbmcvfs.mkdir(dbpath)
        dbpath = xbmc.translatePath(dbpath + 'processeditems.db')
        # data is uniqueid for sets, last known season for TV shows
        create_table_scripts = ["""CREATE TABLE IF NOT EXISTS processeditems (mediaid INTEGER NOT NULL, mediatype TEXT NOT NULL,
            nextdate DATETIME, data TEXT, PRIMARY KEY (mediaid, mediatype))"""]
        self.db = Database(dbpath, create_table_scripts)

    def is_stale(self, mediaid, mediatype):
        result = self.db.fetchone("""SELECT * FROM processeditems WHERE mediaid=? AND mediatype=?
            AND nextdate > datetime('now')""", (mediaid, mediatype))
        return True if not result else False

    def set_nextdate(self, mediaid, mediatype, nextdate):
        exists = self.exists(mediaid, mediatype)
        scriptbit = "datetime('{0}')".format(nextdate) if nextdate else 'null'
        script = "UPDATE processeditems SET nextdate={0} WHERE mediaid=? AND mediatype=?" if exists \
            else "INSERT INTO processeditems (nextdate, mediaid, mediatype) VALUES ({0}, ?, ?)"
        self.db.execute(script.format(scriptbit), (mediaid, mediatype))

    def get_data(self, mediaid, mediatype):
        result = self.db.fetchone("SELECT * FROM processeditems WHERE mediaid=? AND mediatype=?", (mediaid, mediatype))
        if result:
            return result['data']

    def set_data(self, mediaid, mediatype, data):
        exists = self.exists(mediaid, mediatype)
        script = "UPDATE processeditems SET data=? WHERE mediaid=? AND mediatype=?" if exists \
            else "INSERT INTO processeditems (data, mediaid, mediatype) VALUES (?, ?, ?)"
        self.db.execute(script, (data, mediaid, mediatype))

    def exists(self, mediaid, mediatype):
        return True if self.db.fetchone("SELECT * FROM processeditems WHERE mediaid=? AND mediatype=?",
            (mediaid, mediatype)) else False

    def does_not_exist(self, mediaid, mediatype):
        return not self.exists(mediaid, mediatype)

class Database(object):
    def __init__(self, path, create_table_scripts):
        self._db = sqlite3.connect(path)
        self._db.row_factory = sqlite3.Row
        self._db_cursor = self._db.cursor()
        self._build_db(create_table_scripts)

    def execute(self, query, args=()):
        with self._db:
            self._execute_raw(query, args)

    def fetchall(self, query, args=()):
        self._execute_raw(query, args)
        return self._db_cursor.fetchall()

    def fetchone(self, query, args=()):
        self._execute_raw(query, args)
        return self._db_cursor.fetchone()

    def _execute_raw(self, query, args=()):
        self._db_cursor.execute(query, args)

    def _build_db(self, create_table_scripts):
        for script in create_table_scripts:
            self.execute(script)
