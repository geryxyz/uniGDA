from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.pyplot as pyplot

def set_axes_size(w: float, h: float, axes: Axes):
    """ w, h: width, height in inches """
    left = axes.figure.subplotpars.left
    right = axes.figure.subplotpars.right
    top = axes.figure.subplotpars.top
    bottom = axes.figure.subplotpars.bottom
    horizontal_ratio = (right - left)
    vertical_ratio = (top - bottom)
    fig_width = float(w) / horizontal_ratio
    fig_height = float(h) / vertical_ratio
    axes.figure.set_size_inches(fig_width, fig_height)
