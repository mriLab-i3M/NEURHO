from ui.window_workflow import WorkflowWindow


class WorkflowController(WorkflowWindow):
    def __init__(self, *args, **kwargs):
        super(WorkflowController, self).__init__(*args, **kwargs)

        # Connect the signal for when the tab changes
        self.tabs.currentChanged.connect(self.onTabChange)

    def onTabChange(self, index):
        """Handle what happens when a tab is clicked."""
        if index == 0:
            self.MaRGE.fix_console()
            print("MRI Scan tab")
            # Add logic specific to MRI Scan tab here
        elif index == 1:
            print("Co-register tab clicked")
            # Add logic specific to Co-register tab here
        elif index == 2:
            self.PositioningController.fix_console()
            print("Positioning tab")
            # Add logic specific to Positioning tab here
        elif index == 3:
            print("Treatment tab clicked")
            # Add logic specific to Treatment tab here
