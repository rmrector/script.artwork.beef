import xbmcgui

class SeriesSelector(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        super(SeriesSelector, self).__init__(args, kwargs)
        self.serieslist = kwargs.get('serieslist')
        self.selected = kwargs.get('selected', [])
        self.guilist = None

    def prompt(self):
        self.doModal()
        return self.selected

    def onInit(self):
        self.getControl(1).setLabel('$LOCALIZE[32400]')
        self.getControl(3).setVisible(False)
        self.getControl(5).setVisible(True)
        self.getControl(5).setLabel('$LOCALIZE[186]')
        self.guilist = self.getControl(6)
        self.guilist.setVisible(True)

        for series in self.serieslist:
            listitem = xbmcgui.ListItem(series['label'])
            listitem.setProperty('Addon.Summary', str(series['year']) + ' - ' + series['plot'])
            art = series['art']
            art['thumb'] = series['art']['poster']
            listitem.setArt(art)
            if series['label'] in self.selected:
                listitem.select(True)
            self.guilist.addItem(listitem)
        self.setFocus(self.guilist)

    def onClick(self, controlid):
        if controlid == 6:
            item = self.guilist.getSelectedItem()
            if item.isSelected():
                item.select(False)
                self.selected.remove(item.getLabel())
            else:
                item.select(True)
                self.selected.append(item.getLabel())
        elif controlid == 5:
            self.close()
        elif controlid == 7:
            self.selected = []
            self.close()
