import os
import time
import webbrowser

import pandas as pd
import numpy as np
import jinja2


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
            options["df"] = prepareJSDataframe(df)

        options["plotType"] = "lineplot"
        options["axId"] = self.axesId
        options["plotSettings"] = dict(x=x, y=y)
        self.fig.plots.append(options)

    def scatterplot(self, x, y, df=None, **kwargs):
        return scatterplot(x=x, y=y, df=df, ax=self, **kwargs)


def scatterplot(x, y, df=None, ax=None, **kwargs):
    options = {}

    if ax is None:
        assert df is not None, "If no ax object is specified, then you must pass `df`"
        fig = Fig()
        ax = fig.axes[0]
        fig.setData(df)
    else:
        fig = ax.fig
        if df is not None:
            options["df"] = prepareJSDataframe(df)

    options["plotType"] = "scatterplot"
    options["axId"] = ax.axesId
    options["plotSettings"] = dict(x=x, y=y)
    fig.plots.append(options)
    return fig, ax


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

    def addXdataSlider(self, axIndices=(0,), **kwargs):
        """ Add a slider to zoom in and out at different ranges of the data.
            Same as addDataSlider(axIndices, side="x", **kwargs)
            See addDataSlider() for details on the arguments
        """
        self.addDataSlider(axIndices=axIndices, side="x", **kwargs)

    def addYdataSlider(self, axIndices=(0,), **kwargs):
        """ Add a slider to zoom in and out at different ranges of the data.
            Same as addDataSlider(axIndices, side="y", **kwargs)
            See addDataSlider() for details on the arguments
        """
        self.addDataSlider(axIndices=axIndices, side="y", **kwargs)

    def addDataSlider(self, axIndices=(0,), side="x", **kwargs):
        """ Add a slider to zoom in and out at different ranges of the data.
        Args:
            axIndices:  (list of ints) indices of axes that will be affected by
                        the slider. ( default = [0] )
            side:       (str) which axis to "x", "y", "both" (default="x")
            **kwargs    aditional keyword arguments to be passed to the
                        javascript function.
                        TODO: list of aditional argument that can be used
        """
        assert side in {"x", "y", "both"}, "`side` argument to fig.addDataSlider() must be one of 'x', 'y' or 'both'"
        kwargs.update(dict(axes=list(axIndices)))
        self.operations.append(dict(
            kind="addDataSlider",
            args=[side],
            kwargs= kwargs,
            ))

    def show(self, filepath, launch=True, temp=False, temp_delay=5):
        """
        Args:
            temp:   (bool) if set to True, then the file will be deleted as soon
                    as it is launched (hence temporary file)
            temp_delay: (float) how many seconds to wait before deleting the
                    file.
        """

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
            if temp:
                time.sleep(temp_delay)
                os.remove(filepath)


    def _prepareDataframe(self, df):
        return prepareJSDataframe(df)


# ##############################################################################
#                                 FUNCTIONS
# ##############################################################################
def prepareJSDataframe(df):
    schema = {col:"continuous" for col in df.columns}
    data = [list(df.columns)] # header row

    # Convert rest of rows to list of lists
    # data.extend(df.values.tolist())

    # Convert np.NaNs to Nones - Because Echarts does not like NaN objects,
    # but it can handle nulls
    # Then convert to a list of lists
    data.extend(np.where(np.isnan(df), None, df).tolist())

    dff = {"data": data, "schema": schema}
    return dff
