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

PROCESSING_AUTOMATICALLY = 32800
PROCESSING_MANUALLY = 32801
PROCESSING = 32802
PROCESSING_FINISHED = 32803
PROCESSING_ABORTED = 32804
NO_ITEMS = 32805
ITEM_COUNT = 32806
PROCESSED_COUNT = 32807
NO_UPDATES = 32808
UPDATE_COUNT = 32809
NO_MISSING_ARTWORK = 32810
MISSING_LABEL = 32811
UPDATED_LABEL = 32812
ERROR_MESSAGE = 32813
ERRORS_MESSAGE = 32814
RUNNING_VERSION = 32815
DOWNLOAD_COUNT = 32816
NO_IDS_MESSAGE = 32030

debug = False

def report_startup():
    if not xbmcvfs.exists(settings.datapath):
        xbmcvfs.mkdir(settings.datapath)
    with _get_file() as reportfile:
        reportfile.seek(0, os.SEEK_SET)
        newline = "= " + L(RUNNING_VERSION).format(settings.useragent)
        line_exists = any(newline in line for line in reportfile)
        if not line_exists:
            reportfile.seek(0, os.SEEK_END)
            write(reportfile, newline)
            finish_chunk(reportfile)

def report_start(medialist):
    if debug:
        return
    with _get_file() as reportfile:
        write(reportfile, "== {0}: ".format(get_datetime()) + L(PROCESSING_AUTOMATICALLY))
        if not medialist:
            write(reportfile, L(NO_ITEMS))
            write(reportfile, '')
            return
        mediatypecount = {}
        for item in medialist:
            mediatypecount[item.mediatype] = mediatypecount.get(item.mediatype, 0) + 1

        write(reportfile, L(ITEM_COUNT).format(len(medialist)) + " - " +
            ', '.join('{0}: {1}'.format(mt, mediatypecount[mt]) for mt in mediatypecount))

def report_end(medialist, abortedcount, downloaded_size):
    if debug:
        return
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
        downloaded = 0
        errorcount = 0
        for item in medialist:
            for arttype in item.updatedart:
                arttype = get_basetype(arttype)
                arttypecount[arttype] = arttypecount.get(arttype, 0) + 1
                total += 1
            if item.error:
                errorcount += 1
            downloaded += len(item.downloadedart)

        if downloaded:
            # TODO: include # of existing items downloaded, or the # of items added and downloaded
            write(reportfile, L(DOWNLOAD_COUNT).format(downloaded)
                + ' - {0:0.2f}MB'.format(downloaded_size / 1000000.00))
        if not total:
            write(reportfile, L(NO_UPDATES))
        else:
            write(reportfile, L(UPDATE_COUNT).format(total) + " - " +
                ', '.join('{0}: {1}'.format(at, arttypecount[at]) for at in arttypecount))
        if errorcount:
            write(reportfile, L(ERRORS_MESSAGE))
        finish_chunk(reportfile)
    if _should_rotate():
        _rotate_file()

def report_item(mediaitem, forcedreport=False, manual=False, downloaded_size=0):
    if debug or not forcedreport and not settings.report_peritem:
        return
    with _get_file() as reportfile:
        itemtitle = "{0} '{1}'".format(mediaitem.mediatype, mediaitem.label) if mediaitem.mediatype != mediatypes.EPISODE \
            else "{0} '{1}' of '{2}'".format(mediaitem.mediatype, mediaitem.label, mediaitem.showtitle)
        message = "== {0}: ".format(get_datetime()) if forcedreport else ""
        message += L(PROCESSING_MANUALLY if manual else PROCESSING)
        write(reportfile, message.format(itemtitle))
        message = L(NO_IDS_MESSAGE) if mediaitem.missingid \
            else L(MISSING_LABEL).format(', '.join(mediaitem.missingart)) if mediaitem.missingart \
            else L(NO_MISSING_ARTWORK)
        write(reportfile, message)

        if mediaitem.downloadedart:
            message = L(DOWNLOAD_COUNT).format(len(mediaitem.downloadedart))
            if downloaded_size:
                message += ' - {0:0.2f}MB'.format(downloaded_size / 1000000.00)
            write(reportfile, message)
        if mediaitem.updatedart:
            write(reportfile, L(UPDATED_LABEL).format(', '.join(mediaitem.updatedart)))
        elif manual or mediaitem.missingart:
            write(reportfile, L(NO_UPDATES))

        if mediaitem.error:
            write(reportfile, L(ERROR_MESSAGE).format(pykodi.scrub_message(mediaitem.error)))
        if forcedreport:
            finish_chunk(reportfile)
    if forcedreport and _should_rotate():
        _rotate_file()

def get_datetime():
    return pykodi.get_infolabel('System.Date(yyyy-mm-dd)') + ' ' + pykodi.get_infolabel('System.Time(hh:mm:ss xx)')

def write(reportfile, line):
    reportfile.write(line + '\n')

def finish_chunk(reportfile):
    reportfile.write('\n')

def get_latest_report():
    if not _exists(): return ""
    result = []
    with _get_file(True) as reportfile:
        inserti = 0
        for line in reportfile.readlines():
            result.insert(inserti, line)
            if line == '\n':
                inserti = 0
            else:
                inserti += 1
    return ''.join(result)

def _should_rotate():
    if not _exists():
        return False
    return xbmcvfs.Stat(_get_filepath()).st_size() > _get_maxsize()

def _get_maxsize():
    mult = PER_ITEM_MULT if settings.report_peritem else 1
    return REPORT_SIZE * mult

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

def _get_file(readonly=False):
    return open(xbmc.translatePath(_get_filepath()), 'r' if readonly else 'a+')

def _exists(filetag=''):
    return xbmcvfs.exists(_get_filepath(filetag))

def _get_filepath(filetag=''):
    return settings.datapath + REPORT_NAME + ('.' + filetag if filetag else '') + '.txt'

report_startup()
