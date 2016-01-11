import re
import xbmc
import xbmcgui

class ArtworkTypeSelector(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        super(ArtworkTypeSelector, self).__init__(args, kwargs)
        self.existingart = kwargs.get('existingart')
        items = kwargs.get('arttypes')[:]
        items.sort()
        seasonitems = [item for item in items if item.startswith('season')]
        self.arttypes = [(item, item) for item in items if not item.startswith('season')]
        for origseason in seasonitems:
            season = origseason.split('.')
            if season[1] == '0':
                self.arttypes.append(('specials ' + season[2], origseason))
            elif season[1] != '-1':
                # Ignore 'all' seasons artwork, as I can't set artwork for it with JSON
                self.arttypes.append((' '.join(season), origseason))
        self.arttypes.sort(key=lambda art: _sort_art(art[1]))
        self.medialabel = kwargs.get('medialabel')
        self.guilist = None
        self.selected = None

    def prompt(self):
        self.doModal()
        return self.selected

    def onInit(self):
        self.getControl(1).setLabel('Choose art type for {0}'.format(self.medialabel))
        self.getControl(5).setVisible(False)
        self.guilist = self.getControl(6)
        self.guilist.setVisible(True)

        for arttype in self.arttypes:
            listitem = xbmcgui.ListItem(arttype[0])
            listitem.setLabel2(arttype[1])
            if self.existingart.get(arttype[1]):
                listitem.setArt({'icon': self.existingart[arttype[1]]})
            self.guilist.addItem(listitem)
        self.setFocus(self.guilist)

    def onClick(self, controlid):
        if controlid == 6:
            item = self.guilist.getSelectedItem()
            self.selected = item.getLabel2()
            self.close()

class ArtworkSelector(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        super(ArtworkSelector, self).__init__(args, kwargs)
        self.artlist = kwargs.get('artlist')
        self.arttype = kwargs.get('arttype')
        if self.arttype.startswith('season'):
            if '.0.' in self.arttype:
                self.arttype = 'specials ' + self.arttype.rsplit('.', 1)[1]
            else:
                self.arttype = self.arttype.replace('.', ' ')
        self.medialabel = kwargs.get('medialabel')
        self.multi = kwargs.get('multi', False)
        self.existingart = kwargs.get('existingart', ())
        self.guilist = None
        self.selected = None

    def prompt(self):
        self.doModal()
        return self.selected

    def onInit(self):
        self.getControl(1).setLabel('Choose {0} for {1}'.format(self.arttype, self.medialabel))
        self.getControl(5).setVisible(self.multi)
        self.guilist = self.getControl(6)
        self.guilist.setVisible(True)

        for image in self.artlist:
            lang = xbmc.convertLanguage(image['language'], xbmc.ENGLISH_NAME) if image['language'] else 'No language'
            label = '{0}, {1}, {2}'.format(lang, image['rating'].display, image['size'].display)
            listitem = xbmcgui.ListItem(label)
            listitem.setArt({'icon': image['url']})
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

def _sort_art(string, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, string)]
