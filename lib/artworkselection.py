import re
import xbmc
import xbmcgui

from lib.libs import mediatypes
from lib.libs.addonsettings import settings
from lib.libs.pykodi import localize as L

SEASON_NUMBER = 32002
SPECIALS = 20381
UNKNOWN_SOURCE = 32000
CHOOSE_TYPE_HEADER = 32050
CHOOSE_ART_HEADER = 32051
REFRESH_ITEM = 32409
AVAILABLE_COUNT = 32006

def prompt_for_artwork(mediatype, medialabel, availableart, monitor):
    if not availableart:
        return None, None

    arttypes = []
    for arttype, artlist in availableart.iteritems():
        if arttype.startswith('season.-1.'):
            # Ignore 'all' seasons artwork, as I can't set artwork for it with JSON
            continue
        label = arttype if not arttype.startswith('season.') else get_seasonlabel(arttype)
        for image in artlist:
            if image.get('existing'):
                arttypes.append({'arttype': arttype, 'label': label, 'count': len(artlist), 'url': image['url']})
                break
        if arttype not in (at['arttype'] for at in arttypes):
            arttypes.append({'arttype': arttype, 'label': label, 'count': len(artlist)})
    arttypes.sort(key=lambda art: sort_arttype(art['arttype']))
    typeselectwindow = ArtworkTypeSelector('DialogSelect.xml', settings.addon_path, arttypes=arttypes,
        medialabel=medialabel, show_refresh=mediatype in mediatypes.require_manualid)
    selectedarttype = None
    selectedart = None
    typelist = [at['arttype'] for at in arttypes]
    while selectedart is None and not monitor.abortRequested():
        # The loop shows the first window if viewer backs out of the second
        selectedarttype = typeselectwindow.prompt()
        if selectedarttype not in typelist:
            return selectedarttype, None
        if not selectedarttype:
            break
        multi = mediatypes.get_artinfo(mediatype, selectedarttype)['multiselect']
        artselectwindow = ArtworkSelector('DialogSelect.xml', settings.addon_path, artlist=availableart[selectedarttype],
            arttype=selectedarttype, medialabel=medialabel, multi=multi)
        selectedart = artselectwindow.prompt()
    return selectedarttype, selectedart

class ArtworkTypeSelector(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        super(ArtworkTypeSelector, self).__init__()
        self.arttypes = kwargs.get('arttypes')
        self.medialabel = kwargs.get('medialabel')
        self.show_refresh = kwargs.get('show_refresh')
        self.guilist = None
        self.selected = None

    def prompt(self):
        self.doModal()
        return self.selected

    def onInit(self):
        # This is called every time the window is shown
        if not self.selected:
            self.getControl(1).setLabel("Artwork Beef: " + L(CHOOSE_TYPE_HEADER).format(self.medialabel))
            self.getControl(3).setVisible(False)
            self.getControl(5).setVisible(self.show_refresh)
            self.getControl(5).setLabel(L(REFRESH_ITEM))
            self.guilist = self.getControl(6)
            for arttype in self.arttypes:
                listitem = xbmcgui.ListItem(arttype['label'])
                summary = L(AVAILABLE_COUNT).format(arttype['count'])
                listitem.setLabel2(summary)
                # DEPRECATED: Above Krypton and higher (only), below Jarvis and lower (only)
                listitem.setProperty('Addon.Summary', summary)
                listitem.setPath(arttype['arttype'])
                if arttype.get('url'):
                    listitem.setIconImage(arttype['url'])
                    # DEPRECATED: Above is deprecated in Jarvis, but still works through Krypton (at least)
                    # listitem.setArt({'icon': arttype.get('url')})
                self.guilist.addItem(listitem)
        else:
            self.selected = None
        self.setFocus(self.guilist)

    def onClick(self, controlid):
        if controlid == 5:
            self.selected = "!!-Refresh"
            self.close()
        elif controlid == 6:
            item = self.guilist.getSelectedItem()
            self.selected = item.getfilename()
            self.close()
        elif controlid == 7:
            self.close()

class ArtworkSelector(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        super(ArtworkSelector, self).__init__()
        self.arttype = kwargs.get('arttype')
        if self.arttype.startswith('season.'):
            if '.0.' in self.arttype:
                self.arttype = 'specials ' + self.arttype.rsplit('.', 1)[1]
            else:
                self.arttype = self.arttype.replace('.', ' ')
        self.medialabel = kwargs.get('medialabel')
        self.multi = kwargs.get('multi', False)
        self.artlist = kwargs.get('artlist')
        self.guilist = None
        self.selected = None

    def prompt(self):
        '''Returns a single url if not multi,
            else a tuple with item 0 a list of added urls, 1 a list of removed urls,
            None if cancelled'''
        self.doModal()
        return self.selected

    def onInit(self):
        self.getControl(1).setLabel("Artwork Beef: " + L(CHOOSE_ART_HEADER).format(self.arttype, self.medialabel))
        self.getControl(3).setVisible(False)
        self.getControl(5).setVisible(self.multi)
        self.getControl(5).setLabel('$LOCALIZE[186]')
        self.guilist = self.getControl(6)

        for image in self.artlist:
            provider = image['provider'].display
            if isinstance(provider, int):
                provider = L(provider)
            secondprovider = image.get('second provider')
            if secondprovider:
                if isinstance(secondprovider, int):
                    secondprovider = L(secondprovider)
                provider = '{0}, {1}'.format(provider, secondprovider)
            title = image.get('title')
            if not title and 'subtype' in image:
                title = image['subtype'].display
            language = xbmc.convertLanguage(image['language'], xbmc.ENGLISH_NAME) if image.get('language') else None
            if not title:
                title = language
            if title and len(title) < 20 and not secondprovider:
                label = '{0} from {1}'.format(title, provider)
                summary = language if language and language != title else ''
            else:
                label = provider
                if language and language != title:
                    title = language + ' ' + title
                summary = title if title else ''
            rating = image.get('rating')
            size = image.get('size')
            if (rating or size) and summary:
                summary += '\n'
            if size:
                summary += image['size'].display
            if rating and size:
                summary += '   '
            if rating:
                summary += image['rating'].display
            listitem = xbmcgui.ListItem(label)
            listitem.setLabel2(summary)
            # DEPRECATED: Above Krypton and higher (only), below Jarvis and lower (only)
            listitem.setProperty('Addon.Summary', summary)
            listitem.setIconImage(image['preview'])
            # DEPRECATED: Above is deprecated in Jarvis, but still works through Krypton (at least)
            # listitem.setArt({'icon': image['preview']})
            listitem.setPath(image['url'])
            if image.get('existing'):
                listitem.select(True)
            self.guilist.addItem(listitem)
        self.setFocus(self.guilist)

    def onClick(self, controlid):
        if controlid == 6:
            item = self.guilist.getSelectedItem()
            if self.multi:
                if self.selected is None:
                    self.selected = ([], [])
                self.toggleitemlists(item.getfilename(), item.isSelected())
                item.select(not item.isSelected())
            else:
                self.selected = item.getfilename()
                self.close()
        elif controlid == 5:
            if self.multi and self.selected is None:
                self.selected = ([], [])
            self.close()
        elif controlid == 7:
            self.selected = None
            self.close()

    def toggleitemlists(self, filename, selected):
        removefrom = self.selected[0] if selected else self.selected[1]
        appendto = self.selected[1] if selected else self.selected[0]
        if filename in removefrom:
            removefrom.remove(filename)
        else:
            appendto.append(filename)

    def onAction(self, action):
        if action.getId() in (xbmcgui.ACTION_NAV_BACK, xbmcgui.ACTION_PREVIOUS_MENU):
            self.selected = None
            self.close()

def get_seasonlabel(arttype):
    season = arttype.split('.')
    if season[1] == '0':
        return '{0}: {1}'.format(L(SPECIALS), season[2])
    elif season[1] != '-1':
        return '{0}: {1}'.format(L(SEASON_NUMBER).format(season[1]), season[2])

def sort_arttype(arttype, naturalsortresplit=re.compile('([0-9]+)')):
    result = []
    if arttype.startswith('season.0'):
        result.append(u'\u9999')
    elif arttype.startswith('season.'):
        result.append(u'\u9998')
    result.extend(int(text) if text.isdigit() else text.lower() for text in re.split(naturalsortresplit, arttype))
    return result
