from ui.window_positioning import PositioningWindow

class PositioningController(PositioningWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = self.main.MaRGE.console

    def fix_console(self):
        self.layout_widgets.addWidget(self.console, 0, 0)
