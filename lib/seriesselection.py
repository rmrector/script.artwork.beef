import xbmcgui

from lib.libs.pykodi import localize as L

ACTION_SELECTSERIES = 32400

# TODO: Don't use 'imdbnumber'

class SeriesSelector(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        super(SeriesSelector, self).__init__(args, kwargs)
        self.serieslist = kwargs.get('serieslist')
        self.originalselected = kwargs.get('selected', [])
        self.selected = []
        self.guilist = None

    def prompt(self):
        self.doModal()
        return self.selected

    def onInit(self):
        self.getControl(1).setLabel(L(ACTION_SELECTSERIES))
        self.getControl(3).setVisible(False)
        self.getControl(5).setVisible(True)
        self.getControl(5).setLabel('$LOCALIZE[186]')
        self.guilist = self.getControl(6)
        self.guilist.setVisible(True)

        for series in self.serieslist:
            listitem = xbmcgui.ListItem(series['label'])
            summary = str(series['year']) + ' - ' + series['plot']
            listitem.setLabel2(summary)
            # DEPRECATED: Above Krypton and higher (only), below Jarvis and lower (only)
            listitem.setProperty('Addon.Summary', summary)
            listitem.setProperty('imdbnumber', series['imdbnumber'])
            art = series['art']
            if 'poster' in series['art']:
                art['thumb'] = series['art']['poster']
            listitem.setArt(art)
            if series['imdbnumber'] in self.originalselected:
                listitem.select(True)
                self.selected.append(series['imdbnumber'])
            self.guilist.addItem(listitem)
        self.originalselected = list(self.selected)
        self.setFocus(self.guilist)

    def onClick(self, controlid):
        if controlid == 6:
            item = self.guilist.getSelectedItem()
            if item.isSelected():
                item.select(False)
                self.selected.remove(item.getProperty('imdbnumber'))
            else:
                item.select(True)
                self.selected.append(item.getProperty('imdbnumber'))
        elif controlid == 5:
            self.close()
        elif controlid == 7:
            self.selected = self.originalselected
            self.close()

    def onAction(self, action):
        if action.getId() in (xbmcgui.ACTION_NAV_BACK, xbmcgui.ACTION_PREVIOUS_MENU):
            self.selected = self.originalselected
            self.close()
