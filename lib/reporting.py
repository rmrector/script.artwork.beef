import os
import xbmc
import xbmcvfs

from lib.libs import mediatypes
from lib.libs import pykodi
from lib.libs.addonsettings import settings
from lib.libs.mediainfo import get_basetype
from lib.libs.pykodi import localize as L, log

# TODO: Failed movie set matching, missing or updated uniqueid, processeditems label mismatch

REPORT_NAME = 'artwork-report'
REPORT_SIZE = 100000
REPORT_COUNT = 5
PER_ITEM_MULT = 5

PROCESSING_AUTOMATICALLY = "Processing list automatically"
PROCESSING_MANUALLY = "Manually processing {0}"
PROCESSING = "Processing {0}"
PROCESSING_FINISHED = "Processing finished"
PROCESSING_ABORTED = "Processing aborted"
NO_ITEMS = "No items in list"
ITEM_COUNT = "{0} items in list"
PROCESSED_COUNT = "{0} items processed"
NO_UPDATES = "No artwork updated"
UPDATE_COUNT = "{0} artwork updated"
NO_MISSING_ARTWORK = "Not missing artwork, not looking for any"
MISSING_LABEL = "Missing artwork"
UPDATED_LABEL = "Updated artwork"
ERROR_MESSAGE = "Encountered an error"
ERRORS_MESSAGE = "Errors were encountered"

def report_startup():
    if not xbmcvfs.exists(settings.datapath):
        xbmcvfs.mkdir(settings.datapath)
    with _get_file() as reportfile:
        reportfile.seek(0, os.SEEK_SET)
        newline = "= Versions: {0}".format(settings.useragent)
        line_exists = any(newline in line for line in reportfile)
        if not line_exists:
            reportfile.seek(0, os.SEEK_END)
            write(reportfile, newline)
            write(reportfile, '')

def report_start(medialist):
    with _get_file() as reportfile:
        write(reportfile, "== {0}: ".format(get_datetime()) + L(PROCESSING_AUTOMATICALLY))
        if not medialist:
            write(reportfile, L(NO_ITEMS))
            write(reportfile, '')
            return
        mediatypecount = {}
        for item in medialist:
            mediatypecount[item['mediatype']] = mediatypecount.get(item['mediatype'], 0) + 1

        write(reportfile, L(ITEM_COUNT).format(len(medialist)) + " - " +
            ', '.join('{0}: {1}'.format(mt, mediatypecount[mt]) for mt in mediatypecount))

def report_end(medialist, abortedcount):
    if len(medialist) <= 1:
        if _should_rotate():
            _rotate_file()
        return
    with _get_file() as reportfile:
        write(reportfile, get_datetime() + ": " + L(PROCESSING_ABORTED if abortedcount else PROCESSING_FINISHED))
        if abortedcount:
            write(reportfile, L(PROCESSED_COUNT).format(abortedcount))
        arttypecount = {}
        total = 0
        errorcount = 0
        for item in medialist:
            for arttype in item.get('updated art', ()):
                arttype = get_basetype(arttype)
                arttypecount[arttype] = arttypecount.get(arttype, 0) + 1
                total += 1
            if item.get('error'):
                errorcount += 1

        if not total:
            write(reportfile, L(NO_UPDATES))
        else:
            write(reportfile, L(UPDATE_COUNT).format(total) + " - " +
                ', '.join('{0}: {1}'.format(at, arttypecount[at]) for at in arttypecount))
        if errorcount:
            write(reportfile, L(ERRORS_MESSAGE))
        write(reportfile, '')
    if _should_rotate():
        _rotate_file()

def report_item(mediaitem, forcedreport=False, manual=False):
    if not forcedreport and not settings.report_peritem:
        return
    with _get_file() as reportfile:
        itemtitle = "{0} '{1}'".format(mediaitem['mediatype'], mediaitem['label']) if mediaitem['mediatype'] != mediatypes.EPISODE \
            else "{0} '{1}' of '{2}'".format(mediaitem['mediatype'], mediaitem['label'], mediaitem['showtitle'])
        message = "== {0}: ".format(get_datetime()) if forcedreport else ""
        message += PROCESSING_MANUALLY if manual else PROCESSING
        write(reportfile, message.format(itemtitle))
        if not mediaitem.get('missing art'):
            if not manual:
                write(reportfile, L(NO_MISSING_ARTWORK))
        else:
            write(reportfile, L(MISSING_LABEL) + ': ' + ', '.join(mediaitem['missing art']))

        if mediaitem.get('updated art'):
            write(reportfile, L(UPDATED_LABEL) + ': ' + ', '.join(mediaitem['updated art']))
        elif manual or mediaitem.get('missing art'):
            write(reportfile, L(NO_UPDATES))

        if mediaitem.get('error'):
            write(reportfile, L(ERROR_MESSAGE) + ' - ' + mediaitem['error'])
        if forcedreport:
            write(reportfile, '')
    if forcedreport and _should_rotate():
        _rotate_file()

def get_datetime():
    return pykodi.get_infolabel('System.Date(yyyy-mm-dd)') + ' ' + pykodi.get_infolabel('System.Time(hh:mm:ss xx)')

def write(reportfile, line):
    reportfile.write(line + '\n')

def _should_rotate():
    if not _exists():
        return False
    return xbmcvfs.Stat(_get_filepath()).st_size() > (REPORT_SIZE * (PER_ITEM_MULT if settings.report_peritem else 1))

def _rotate_file():
    newdate = ndate = pykodi.get_infolabel('System.Date(yyyy-mm-dd)')
    count = 0
    while _exists(newdate):
        count += 1
        newdate = ndate + '.' + str(count)
    if not xbmcvfs.copy(_get_filepath(), _get_filepath(newdate)):
        log("Could not copy latest report to new filename", xbmc.LOGWARNING, 'reporting')
        return False
    if not xbmcvfs.delete(_get_filepath()):
        log("Could not delete old copy of latest report", xbmc.LOGWARNING, 'reporting')
        return False

    # delete old reports
    _, files = xbmcvfs.listdir(settings.datapath)
    reportfiles = sorted(f[:-4] for f in files if f.startswith(REPORT_NAME))
    while len(reportfiles) > REPORT_COUNT:
        filename = reportfiles[0] + '.txt'
        if not xbmcvfs.delete(settings.datapath + filename):
            log("Could not delete old report '{0}'".format(filename), xbmc.LOGWARNING, 'reporting')
            return False
        del reportfiles[0]
    report_startup()
    return True

def _get_file():
    return open(xbmc.translatePath(_get_filepath()), 'a+')

def _exists(filetag=''):
    return xbmcvfs.exists(_get_filepath(filetag))

def _get_filepath(filetag=''):
    return settings.datapath + REPORT_NAME + ('.' + filetag if filetag else '') + '.txt'

report_startup()
