import collections
import os
import re
import sys
import time
import urllib
import xbmc
import xbmcaddon
from datetime import datetime

oldpython = sys.version_info < (2, 7)
if oldpython:
    import simplejson as json
else:
    import json

try:
    datetime.strptime('2112-04-01', '%Y-%m-%d')
except TypeError:
    pass

_log_level_tag_lookup = {
    xbmc.LOGDEBUG: 'D',
    xbmc.LOGINFO: 'I'
}

_log_scrub_strings = {}

ADDONID = 'script.artwork.beef'

thumbnailimages = ('image://video@',)
remoteimages = ('http',)
embeddedimages = ('image://video_', 'image://music')
notimagefiles = remoteimages + thumbnailimages + embeddedimages

_main_addon = None
def get_main_addon():
    global _main_addon
    if not _main_addon:
        _main_addon = Addon()
    return _main_addon

_watch_addon = None
def is_addon_watched():
    global _watch_addon
    if _watch_addon is None:
        if not get_conditional('System.HasAddon(script.module.devhelper)'):
            _watch_addon = False
        else:
            devhelper = Addon('script.module.devhelper')
            if devhelper.get_setting('watchalladdons'):
                _watch_addon = True
            else:
                _watch_addon = ADDONID in devhelper.get_setting('watchaddons_list')

    return _watch_addon

_kodiversion = None
def get_kodi_version():
    global _kodiversion
    if _kodiversion is None:
        _kodiversion = int(get_infolabel('System.BuildVersion').split('.')[0])
    return _kodiversion

def localize(messageid):
    if isinstance(messageid, basestring):
        result = messageid
    elif messageid >= 32000 and messageid < 33000:
        result = get_main_addon().getLocalizedString(messageid)
    else:
        result = xbmc.getLocalizedString(messageid)
    return result.encode('utf-8') if isinstance(result, unicode) else result

def get_conditional(conditional):
    return xbmc.getCondVisibility(conditional)

def get_infolabel(infolabel):
    return xbmc.getInfoLabel(infolabel)

def execute_builtin(builtin_command):
    xbmc.executebuiltin(builtin_command)

def datetime_now():
    try:
        return datetime.now()
    except ImportError:
        xbmc.sleep(50)
        return datetime_now()

def datetime_strptime(date_string, format_string):
    try:
        return datetime.strptime(date_string, format_string)
    except TypeError:
        try:
            return datetime(*(time.strptime(date_string, format_string)[0:6]))
        except ImportError:
            xbmc.sleep(50)
            return datetime_strptime(date_string, format_string)

def execute_jsonrpc(jsonrpc_command):
    if isinstance(jsonrpc_command, dict):
        try:
            jsonrpc_command = json.dumps(jsonrpc_command)
        except UnicodeDecodeError:
            jsonrpc_command = json.dumps(jsonrpc_command, ensure_ascii=False)

    json_result = xbmc.executeJSONRPC(jsonrpc_command)
    try:
        return json.loads(json_result, cls=UTF8JSONDecoder)
    except UnicodeDecodeError:
        return json.loads(json_result.decode('utf-8', 'replace'), cls=UTF8JSONDecoder)

def log(message, level=xbmc.LOGDEBUG, tag=None):
    if is_addon_watched() and level < xbmc.LOGNOTICE:
        # Messages from this add-on are being watched, elevate to NOTICE so Kodi logs it
        level_tag = _log_level_tag_lookup[level] + ': ' if level in _log_level_tag_lookup else ''
        level = xbmc.LOGNOTICE
    else:
        level_tag = ''

    if isinstance(message, (dict, list)) and len(message) > 300:
        message = str(message)
    elif isinstance(message, unicode):
        message = message.encode('utf-8')
    elif not isinstance(message, str):
        message = json.dumps(message, cls=UTF8PrettyJSONEncoder)

    addontag = ADDONID if not tag else ADDONID + ':' + tag
    file_message = '%s[%s] %s' % (level_tag, addontag, scrub_message(message))
    xbmc.log(file_message, level)

def scrub_message(message):
    for string in _log_scrub_strings.values():
        message = message.replace(string, "XXXXX")
    return message

def set_log_scrubstring(key, string):
    if string and len(string) > 4:
        _log_scrub_strings[key] = string
    elif key in _log_scrub_strings:
        del _log_scrub_strings[key]

def get_language(language_format=xbmc.ENGLISH_NAME, region=False):
    language = xbmc.getLanguage(language_format, region)
    if not language or region and language.startswith('-'):
        engname = xbmc.getLanguage(xbmc.ENGLISH_NAME)
        regiontag = language
        if ' (' in engname:
            language = engname[:engname.rfind(' (')]
        if language_format != xbmc.ENGLISH_NAME:
            language = xbmc.convertLanguage(language, language_format) + regiontag
    return language

def unquoteimage(imagestring):
    # extracted thumbnail images need to keep their 'image://' encoding
    if imagestring.startswith('image://') and not imagestring.startswith(('image://video', 'image://music')):
        return urllib.unquote(imagestring[8:-1])
    return imagestring

def quoteimage(imagestring):
    if imagestring.startswith('image://'):
        return imagestring
    # Kodi goes lowercase and doesn't encode some chars
    result = 'image://{0}/'.format(urllib.quote(imagestring, '()!'))
    result = re.sub(r'%[0-9A-F]{2}', lambda mo: mo.group().lower(), result)
    return result

def unquotearchive(filepath):
    # DEPRECATED: Krypton and below need this, Leia changed archive support to be a standard file path
    if not filepath or not filepath.startswith(('rar://', 'zip://')):
        return filepath
    result = filepath[6:].split('/', 1)[0]
    return urllib.unquote(result)

def get_command(*first_arg_keys):
    command = {}
    start = len(first_arg_keys) if first_arg_keys else 1
    for x in range(start, len(sys.argv)):
        arg = sys.argv[x].split("=")
        command[arg[0].strip().lower()] = arg[1].strip() if len(arg) > 1 else True

    if first_arg_keys:
        for i, argkey in enumerate(first_arg_keys, 1):
            if len(sys.argv) <= i:
                break
            command[argkey] = sys.argv[i]
    return command

def get_busydialog():
    return DialogBusy()

class Addon(xbmcaddon.Addon):
    def __init__(self, *args, **kwargs):
        super(Addon, self).__init__()
        self.addonid = self.getAddonInfo('id')
        self.version = self.getAddonInfo('version')
        self.path = self.getAddonInfo('path')
        self.datapath = self.getAddonInfo('profile') # WARN: This can change if Kodi profile changes
        self.resourcespath = os.path.join(xbmc.translatePath(self.path).decode('utf-8'), u'resources')
        if not os.path.isdir(self.resourcespath):
            self.resourcespath = None

    def get_setting(self, settingid):
        result = self.getSetting(settingid)
        if result == 'true':
            result = True
        elif result == 'false':
            result = False
        elif settingid.endswith('_list'):
            result = [addon.strip() for addon in result.split('|')]
            if len(result) == 1 and not result[0]:
                result = []
        return result

    def set_setting(self, settingid, value):
        if settingid.endswith('_list') and not isinstance(value, basestring) \
        and isinstance(value, collections.Sequence):
            value = '|'.join(value)
        elif isinstance(value, bool):
            value = 'true' if value else 'false'
        elif not isinstance(value, basestring):
            value = str(value)
        self.setSetting(settingid, value)

class ObjectJSONEncoder(json.JSONEncoder):
    # Will still flop on circular objects
    def __init__(self, *args, **kwargs):
        kwargs['skipkeys'] = True
        super(ObjectJSONEncoder, self).__init__(*args, **kwargs)

    def default(self, obj):
        # Called for objects that aren't directly JSON serializable
        if isinstance(obj, collections.Mapping):
            return dict((key, obj[key]) for key in obj.keys())
        if isinstance(obj, collections.Sequence):
            return list(obj)
        if callable(obj):
            return str(obj)
        try:
            result = dict(obj.__dict__)
            result['* objecttype'] = str(type(obj))
            return result
        except AttributeError:
            pass # obj has no __dict__ attribute
        result = {'* dir': dir(obj)}
        result['* objecttype'] = str(type(obj))
        return result

class UTF8PrettyJSONEncoder(ObjectJSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs['ensure_ascii'] = False
        kwargs['indent'] = 2
        kwargs['separators'] = (',', ': ')
        super(UTF8PrettyJSONEncoder, self).__init__(*args, **kwargs)

    def iterencode(self, obj, _one_shot=False):
        for result in super(UTF8PrettyJSONEncoder, self).iterencode(obj, _one_shot):
            if isinstance(result, unicode):
                result = result.encode('utf-8')
            yield result

class UTF8JSONDecoder(json.JSONDecoder):
    def raw_decode(self, s, idx=0):
        args = (s,) if oldpython else (s, idx)
        result, end = super(UTF8JSONDecoder, self).raw_decode(*args)
        result = self._json_unicode_to_str(result)
        return result, end

    def _json_unicode_to_str(self, jsoninput):
        if isinstance(jsoninput, dict):
            return dict((self._json_unicode_to_str(key), self._json_unicode_to_str(value)) for key, value in jsoninput.iteritems())
        elif isinstance(jsoninput, list):
            return [self._json_unicode_to_str(item) for item in jsoninput]
        elif isinstance(jsoninput, unicode):
            return jsoninput.encode('utf-8')
        else:
            return jsoninput

class DialogBusy(object):
    def __init__(self):
        self.visible = False
        window = 'busydialognocancel' if get_kodi_version() >= 18 else 'busydialog'
        self._activate = 'ActivateWindow({0})'.format(window)
        self._close = 'Dialog.Close({0})'.format(window)

    def create(self):
        xbmc.executebuiltin(self._activate)
        self.visible = True

    def close(self):
        xbmc.executebuiltin(self._close)
        self.visible = False

    def __del__(self):
        if self.visible:
            try:
                xbmc.executebuiltin(self._close)
            except AttributeError:
                pass
