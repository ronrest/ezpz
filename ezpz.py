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

    def setData(self, df):
        self.df = df
        self.schema = {col:"continuous" for col in df.columns}

    def plot(self, filepath, launch=True):
        plots = self.plots
        containerId="myplot"

        dataDict = self._prepareDataframe(df)
        # data = [list(self.df.columns)]
        # data.extend(df.values.tolist())
        # df.to_records(index=False)

        template = templateEnv.get_template(TEMPLATE_FILE)
        s = template.render(dataDict=dataDict, containerId=containerId, plots=plots, figSettings=self.figSettings)
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

