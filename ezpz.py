import pandas as pd
import jinja2
import numpy as np
import webbrowser

# ##############################################################################
#                                   SETTINGS
# ##############################################################################
TEMPLATE_FILE = "template.html"

# ##############################################################################
#                                   SETUP
# ##############################################################################
templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)


# ##############################################################################
#                                 CLASSES
# ##############################################################################
class Axes(object):
    def __init__(self, fig, axesId):
        self.axesId = axesId
        self.fig = fig

    @staticmethod
    def fromFig(fig, axesId=0):
        return Axes(fig, axesId=axesId)

    def lineplot(self, x, y, df=None, **kwargs):
        options = {}
        if df is not None:
            options[df] = prepareDataframe(df)

        options["plotType"] = "lineplot"
        options["axId"] = self.axesId
        options["plotSettings"] = dict(x=x, y=y)
        self.fig.plots.append(options)


class Fig(object):
    def __init__(self, grid=None, **kwargs):
        self.figSettings = kwargs
        self.n_axes = 1
        if grid is not None:
            self.figSettings["grid"] = list(grid)
            self.n_axes = grid[0]*grid[1]

        self.axes = [Axes(self, id) for id in range(self.n_axes)]

        self.df = None
        self.plots = []
        self.operations = []
        self.containerId="myplot"

    def setData(self, df):
        self.df = df
        self.schema = {col:"continuous" for col in df.columns}

    def linkAxisPointers(self, axIndices, side="both", **kwargs):
        assert side in {"x", "y", "both"}, "`side` argument to fig.linkAxisPointers() must be one of 'x', 'y' or 'both'"
        # TODO: do dummy checking
        self.operations.append(dict(
            kind="linkAxisPointers",
            args=[axIndices, side],
            kwargs= kwargs,
            ))

    def syncXrange(self, axIndices):
        self.syncRange(side="x", axIndices=axIndices)

    def syncYrange(self, axIndices):
        self.syncRange(side="y", axIndices=axIndices)

    def syncRange(self, axIndices, side):
        """
        Args:
            side:   (str)one of "x", "y", "both"
            indice: (list of ints) Axes indices
        """
        # TODO: do dummy checking
        assert side in {"x", "y", "both"}, "`side` argument to fig.syncRange() must be one of 'x', 'y' or 'both'"
        self.operations.append(dict(
        kind="_createSyncRangeFlags",
        args=[side, axIndices],
        kwargs= {},
        ))


    def show(self, filepath, launch=True):

        # DATA
        dataDict = self._prepareDataframe(df)

        # TEMPLATE
        template = templateEnv.get_template(TEMPLATE_FILE)
        s = template.render(dataDict=dataDict, containerId=self.containerId, plots=self.plots, figSettings=self.figSettings, operations=self.operations)

        # SAVE OR RETURN
        if filepath is None:
            return s
        else:
            with open(filepath, "w") as fob:
                fob.write(s)
            if launch:
                webbrowser.open_new_tab(filepath)

    def _prepareDataframe(self, df):
        data = [list(self.df.columns)]
        data.extend(df.values.tolist())
        schema = {col:"continuous" for col in df.columns}
        dff = {"data": data, "schema": schema}
        return dff
