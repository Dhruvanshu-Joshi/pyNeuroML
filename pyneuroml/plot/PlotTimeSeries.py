#!/usr/bin/env python3
"""
Functions related to plotting of time series

File: pyneuroml/plot/PlotTimeSeries.py

Copyright 2024 NeuroML contributors
"""


import logging
import math
import typing

import numpy
import pyneuroml.lems as pynmll
import pyneuroml.plot.Plot as pynmlplt
from matplotlib import pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def plot_time_series(
    trace_data: typing.Union[
        typing.Dict[typing.Any, typing.Any],
        typing.List[typing.Dict[typing.Any, typing.Any]],
    ],
    title: str = "",
    offset: bool = True,
    show_plot_already: bool = True,
    scalebar_location: typing.Optional[str] = None,
    scalebar_length: typing.Optional[float] = None,
    labels: bool = False,
    **kwargs: typing.Any,
) -> None:
    """Plot time series data from a dictionary of data

    .. versionadded:: 1.2.2

    .. seealso::

        :py:func:`pyneuroml.plot.Plot.generate_plot`
            general plotting function

    :param trace_data: a dictionary of trace data, or list of such dictionaries
        The keys are used as labels in the legend.
        At least one 't' key must exist in each dict, which holds the time axis data.
    :type trace_data: dict or list(dict)
    :param title: plot title, use "" to leave it blank
    :type title: str
    :param offset: whether the time series should be offset from each other
        along the y axis for clarity.
        This is often useful when plotting voltage traces for a population of
        cells where overlapping traces would make it hard to see individual
        values
    :type offset: bool
    :param scalebar_location: where a scalebar should be placed
        If None, no scalebar is shown.
        See the documentation of matplotlib-scalebar for more information:
        https://github.com/ppinard/matplotlib-scalebar
    :type scalebar_location: str or None
    :param scalebar_length: length of scalebar in units of data (only valid if
        scalebar_location is not None)
    :type scalebar_length: float
    :param labels: toggle using labels for legends
        If labels is None, no legend is shown
    :type labels: bool
    :param kwargs: other key word arguments that are passed to the
        `pyneuroml.plot.Plot.generate_plot` function
    :returns: None
    :raises ValueError: if a 't' (time) key is not found in the traces data

    """
    if type(trace_data) is dict:
        trace_data = [trace_data]

    num_traces = 0
    for td in trace_data:
        num_traces += len(td)
    logger.debug(f"Plotting {num_traces} time series")

    xs = []
    ys = []
    if labels is True:
        labelvals = []
    else:
        labelvals = None

    # calculate trace width
    miny = float(math.inf)
    maxy = float(-math.inf)

    for td in trace_data:
        if "t" not in td.keys():
            raise ValueError("A 't' (time) key must be provided in the trace data")

        if offset is True or scalebar_location is not None:
            for key, trace in td.items():
                if key == "t":
                    continue

                max_trace = max(trace)
                min_trace = min(trace)
                if max_trace > maxy:
                    maxy = max_trace
                if min_trace < miny:
                    miny = min_trace

    trace_width = abs(miny) + abs(maxy)
    print(f"trace max, min, width are: {maxy}, {miny}, {trace_width}")

    ctr = 0
    for td in trace_data:
        if offset is False:
            for key, trace in td.items():
                if key == "t":
                    continue
                xs.append(td["t"])
                ys.append(trace)
                if labels is True:
                    labelvals.append(key)
        else:
            for key, trace in td.items():
                if key == "t":
                    continue
                offset_trace = numpy.array(trace) + (ctr * trace_width)
                xs.append(td["t"])
                ys.append(offset_trace)
                if labels is True:
                    labelvals.append(key)
                ctr += 1

    ax = pynmlplt.generate_plot(
        xvalues=xs,
        yvalues=ys,
        title=title,
        labels=labelvals,
        show_plot_already=False,
        **kwargs,
    )

    # clear ytics
    if offset is True:
        ax.set_yticks([])

    if scalebar_location is not None:
        if scalebar_length is None:
            scalebar_length = trace_width / 2

        scalebar_ = ScaleBar(
            1,
            rotation="vertical",
            scale_loc="none",
            location=scalebar_location,
            fixed_value=scalebar_length,
            label=str(scalebar_length),
            label_loc="right",
        )

        print(f"Note: length of the scalebar is {scalebar_length} units")
        ax.add_artist(scalebar_)

    if show_plot_already is True:
        plt.show()


def plot_time_series_from_lems_file(
    lems_file_name: str, base_dir: str = ".", title: str = "", **kwargs
) -> None:
    """Plot time series from a LEMS file.

    Wrapper around the `plot_time_series` function. This reads a LEMS file,
    loads the data and then passes it to it.

    .. versionadded:: 1.2.2

    .. seealso::

        :py:func:`pyneuroml.plot.PlotTimeSeries.plot_time_series`
            main plotter function

    :param lems_file_name: path to LEMS simulation file
    :type lems_file_name: str
    :param base_dir: directory where LEMS file resides
    :type base_dir: str
    :param **kwargs: other arguments passed to `plot_time_series`
    :returns: None

    """
    traces = pynmll.load_sim_data_from_lems_file(
        lems_file_name, get_events=False, get_traces=True
    )

    plot_time_series(traces, **kwargs)


def plot_time_series_from_data_files(
    data_file_names: typing.Union[str, typing.List[str]], **kwargs
):
    """Plot time series from a data file.

    The first column must be the time, the other columns are data.

    .. versionadded:: 1.2.2

    :param data_file_names: name/path to data file(s)
    :type data_file_names: str or list of strings
    :param kwargs: other key word arguments that are passed to the
        `plot_time_series` function

    """
    all_traces = []
    if type(data_file_names) is str:
        data_file_names = [data_file_names]

    for f in data_file_names:
        print(f"Processing: {f}")
        traces = {}
        data_array = numpy.loadtxt(f)
        traces["t"] = data_array[:, 0]
        num_cols = numpy.shape(data_array)[1]
        for i in range(1, num_cols, 1):
            traces[str(i)] = data_array[:, i]
        all_traces.append(traces)

    plot_time_series(all_traces, labels=False, **kwargs)
