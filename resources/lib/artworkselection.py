import re
import xbmc
import xbmcgui
from xbmc import getLocalizedString as localized

CURRENT_ART = 13512
SEASON_NUMBER = 20358
SPECIALS = 20381

class ArtworkTypeSelector(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        super(ArtworkTypeSelector, self).__init__()
        self.existingart = kwargs.get('existingart')
        items = kwargs.get('arttypes')[:]
        items.sort()
        seasonitems = [item for item in items if item[0].startswith('season.')]
        self.arttypes = [(item[0], item[0], item[1]) for item in items if not item[0].startswith('season.')]
        for origseason in seasonitems:
            season = origseason[0].split('.')
            if season[1] == '0':
                self.arttypes.append(('{0}: {1}'.format(localized(SPECIALS), season[2]), origseason[0], origseason[1]))
            elif season[1] != '-1':
                # Ignore 'all' seasons artwork, as I can't set artwork for it with JSON
                self.arttypes.append(('{0}: {1}'.format(localized(SEASON_NUMBER) % int(season[1]), season[2]), origseason[0], origseason[1]))
        self.arttypes.sort(key=lambda art: sort_art(art[1]))
        self.medialabel = kwargs.get('medialabel')
        self.guilist = None
        self.selected = None

    def prompt(self):
        self.doModal()
        return self.selected

    def onInit(self):
        # This is called every time the window is shown
        if not self.selected:
            self.getControl(1).setLabel('Choose art type for {0}'.format(self.medialabel))
            self.getControl(3).setVisible(False)
            self.getControl(5).setVisible(False)
            self.guilist = self.getControl(6)
            for arttype in self.arttypes:
                listitem = xbmcgui.ListItem(arttype[0])
                listitem.setProperty('Addon.Summary', '{0} available'.format(arttype[2]))
                listitem.setLabel2(arttype[1])
                if self.existingart.get(arttype[1]):
                    listitem.setIconImage(self.existingart[arttype[1]])
                    # Above is deprecated in Jarvis, but still works
                    # listitem.setArt({'icon': self.existingart[arttype[1]]})
                self.guilist.addItem(listitem)
        else:
            self.selected = None
        self.setFocus(self.guilist)

    def onClick(self, controlid):
        if controlid == 6:
            item = self.guilist.getSelectedItem()
            self.selected = item.getLabel2()
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
        self.hqpreview = kwargs.get('hqpreview', False)
        self.existingart = kwargs.get('existingart', [])
        artlist = kwargs.get('artlist')
        urllist = list(item['url'] for item in artlist)
        self.artlist = []
        for art in self.existingart:
            if art not in urllist:
                self.artlist.append({'url': art, 'preview': art, 'windowlabel': localized(CURRENT_ART)})
        self.artlist.extend(artlist)
        self.guilist = None
        self.selected = None

    def prompt(self):
        self.doModal()
        if self.multi and self.selected and not (self.selected[0] or self.selected[1]):
            return None
        return self.selected

    def onInit(self):
        self.getControl(1).setLabel('Choose {0} for {1}'.format(self.arttype, self.medialabel))
        self.getControl(3).setVisible(False)
        self.getControl(5).setVisible(self.multi)
        self.getControl(5).setLabel('$LOCALIZE[186]')
        self.guilist = self.getControl(6)

        for image in self.artlist:
            if 'windowlabel' in image:
                label = image['windowlabel']
                summary = 'Unknown source'
            else:
                provider = image['provider'].display
                if isinstance(provider, int):
                    provider = localized(provider)
                secondprovider = image.get('second provider')
                if secondprovider:
                    if isinstance(secondprovider, int):
                        secondprovider = localized(secondprovider)
                    provider = '{0}, {1}'.format(provider, secondprovider)
                title = image.get('title')
                if not title and 'subtype' in image:
                    title = image['subtype'].display
                language = xbmc.convertLanguage(image['language'], xbmc.ENGLISH_NAME) if image['language'] else None
                if not title:
                    title = language
                if title and len(title) < 20 and not secondprovider:
                    label = '{0} from {1}'.format(title, provider)
                    summary = language if language != title else ''
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
            listitem.setProperty('Addon.Summary', summary)
            listitem.setIconImage(image['url'] if self.hqpreview else image['preview'])
            # Above is deprecated in Jarvis, but still works
            # listitem.setArt({'icon': image['url'] if self.hqpreview else image['preview']})
            listitem.setPath(image['url'])
            if image['url'] in self.existingart:
                listitem.select(True)
            self.guilist.addItem(listitem)
        self.setFocus(self.guilist)

    def onClick(self, controlid):
        if controlid == 6:
            item = self.guilist.getSelectedItem()
            if self.multi:
                if self.selected == None:
                    self.selected = ([], [])
                if item.isSelected():
                    item.select(False)
                    # removed
                    if item.getfilename() in self.selected[0]:
                        self.selected[0].remove(item.getfilename())
                    else:
                        self.selected[1].append(item.getfilename())
                else:
                    item.select(True)
                    if item.getfilename() in self.selected[1]:
                        self.selected[1].remove(item.getfilename())
                    else:
                        self.selected[0].append(item.getfilename())
            else:
                self.selected = item.getfilename()
                self.close()
        elif controlid == 5:
            self.close()
        elif controlid == 7:
            self.selected = None
            self.close()

    def onAction(self, action):
        if action.getId() in (xbmcgui.ACTION_NAV_BACK, xbmcgui.ACTION_PREVIOUS_MENU):
            self.selected = None
            self.close()

def sort_art(string, naturalsortresplit=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(naturalsortresplit, string)]
