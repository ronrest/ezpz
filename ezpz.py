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
        return lineplot(x=x, y=y, df=df, ax=self, **kwargs)

    def scatterplot(self, x, y, df=None, **kwargs):
        return scatterplot(x=x, y=y, df=df, ax=self, **kwargs)

    def barplot(self, x, y, df=None, **kwargs):
        return barplot(x=x, y=y, df=df, ax=self, **kwargs)

    def stepplot(self, x, y, stepType="end", df=None, **kwargs):
        return stepplot(x=x, y=y, stepType="end", df=df, ax=self, **kwargs)


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

    def setData(self, df, schema={}):
        self.df = df
        # self.schema = {col:"continuous" for col in df.columns}
        self.schema = createSchema(df, schema=schema)

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

    def show(self, filepath, figsize=(), launch=True, temp=False, temp_delay=5):
        """
        Args:
            filepath:   (str) where the output HTML file will be saved
            figsize:    (tuple of 2 strings) dimensions of the figure on the page.
                        if integer values are passed, then it will interpret as
                        pixel dimensions.
                        But you can pass strings that would be valid in html for
                        setting width and height of a DIV element.
                        eg: ("100%", "50%") or ("400pt", "300pt") or ("400px", "300px")
            launch:     (bool) should it automatically launch a new browser tab
                        to view the plot? (default=True)
            temp:   (bool) if set to True, then the file will be deleted as soon
                    as it is launched (hence temporary file)
            temp_delay: (float) how many seconds to wait before deleting the
                    file.
        """

        # DATA
        dataDict = self._prepareDataframe(self.df, schema=self.schema)

        # FIGSIZE (convert to pixels string if numbers are provided )
        figsize = list(figsize)
        figsize[0] = figsize[0] if isinstance(figsize[0], str) else f"{figsize[0]}px"
        figsize[1] = figsize[1] if isinstance(figsize[1], str) else f"{figsize[1]}px"

        # TEMPLATE
        template = templateEnv.get_template(TEMPLATE_FILE)
        s = template.render(dataDict=dataDict, containerId=self.containerId, plots=self.plots, figSettings=self.figSettings, operations=self.operations, figsize=figsize)

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


    def _prepareDataframe(self, df, schema={}):
        return prepareJSDataframe(df, schema)


# ##############################################################################
#                                 PLOT FUNCTIONS
# ##############################################################################
def figaxXYplotBuilder(kind, x, y=None, df=None, ax=None, **kwargs):
    """ A generic function for building 2d XY plots """
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

    options["plotType"] = kind
    options["axId"] = ax.axesId

    if y is None:
        options["plotSettings"] = dict(x=x, **kwargs)
    else:
        options["plotSettings"] = dict(x=x, y=y, **kwargs)

    fig.plots.append(options)
    return fig, ax


def scatterplot(x, y, df=None, ax=None, pointSize=5, **kwargs):
    """
    Args:
        x  (str) name of column to use for x axis
        y  (str) name of column to use for y axis
        ax: Axes object to put the plot into.
        symbolSize  (float) size of the points
    """
    symbolSize = pointSize
    return figaxXYplotBuilder(kind="scatterplot", x=x, y=y, df=df, ax=ax, symbolSize=symbolSize, **kwargs)


def lineplot(x, y, df=None, ax=None, **kwargs):
    return figaxXYplotBuilder(kind="lineplot", x=x, y=y, df=df, ax=ax, **kwargs)


def barplot(x, y, df=None, ax=None, **kwargs):
    return figaxXYplotBuilder(kind="barplot", x=x, y=y, df=df, ax=ax, **kwargs)

def stepplot(x, y, stepType="end", df=None, ax=None, **kwargs):
    """ Create a step plot
    Args:
        x:          (str) name of column to use for x axis
        y:          (str) name of column to use for y axis
        stepType:   (str) When the change in value occurs
                    one of "start", "end", "middle"
        df:         (None of Pandas Dataframe) dataframe to use, if not using
                    the default one for the figure.
        ax:         (Axes object) which axes object to use.
                    if None, then it will create a new figure, and axes object.
        **kwargs:   Aditional keyword-argument pairs to pass.

    Returns:
        fig, ax : figure, and axes object where this plot is plotted to.
    """
    assert stepType.lower() in {"start", "end", "middle"}, 'stepType argument for stepplot() must be one of ["start", "end", "middle"]'
    return figaxXYplotBuilder(kind="stepplot", x=x, y=y, df=df, ax=ax, **kwargs)


def histogram(x, df=None, binMethod="squareRoot", showItemLabel=False, ax=None, **kwargs):
    """ Creates a histogram
    Args:
        x               (str) name of column containing data you want to plot
        binMethod:      (str) Controls how the bins are calculated. one of:
                              "squareRoot", "scott", "freedmanDiaconis", "sturges"
        showItemLabel: (bool) show the labels for each of the bars?
        ax:             Axes object to put the plot into.
    """
    return figaxXYplotBuilder(kind="histogram", x=x, df=df, ax=ax, binMethod=binMethod, showItemLabel=showItemLabel, **kwargs)


# ##############################################################################
#                                 DF FUNCTIONS
# ##############################################################################
def prepareJSDataframe(df, schema={}):
    """ Convert a pandas data frame to a format that can be read properly by
        the javascript DataFrame class in ezecharts.

    Args:
        df:     (pandas dataframe)
        schema: (dict) key-value mapping from column names to datatype
                to be used by ezecharts dataframe class for each column.
                If nothing is passed for this argument, it will TRY to determine
                an appropirate datatype automatically (same for any columns not
                included in the schema dictionay if you pass one.)
    """
    schema = createSchema(df, schema=schema)
    data = [list(df.columns)] # header row

    # Convert rest of rows to list of lists
    # data.extend(df.values.tolist())

    # Convert np.NaNs to Nones - Because Echarts does not like NaN objects,
    # but it can handle nulls
    # Then convert to a list of lists
    # data.extend(np.where(np.isnan(df), None, df).tolist()) # This method fails for strings
    data.extend(df.where(pd.notnull(df), None).values.tolist())

    dff = {"data": data, "schema": schema}
    return dff


def createSchema(df, schema={}):
    """ Create the schema for ezecharts dataframe from a pandas dataframe.
        You can optionally pass your own schema, for all or some of the columns,
        and these values will be used. It will try to determine an appropriate
        datatype for each other column automatically.

    Args:
        df:     (pandas dataframe)
        schema: (dict) key-value mapping from column names to datatype
                to be used by ezecharts dataframe class for each column.
                If nothing is passed for this argument, it will TRY to determine
                an appropirate datatype automatically (same for any columns not
                included in the schema dictionay if you pass one.)

                datatypes available:
                    categorical, continuous, time, string
    """
    schema = {col:schema.get(col, "continuous") for col in df.columns}
    return schema
