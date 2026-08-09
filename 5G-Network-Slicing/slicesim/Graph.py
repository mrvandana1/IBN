# from statistics import mean

# from matplotlib import gridspec
# import matplotlib.animation as animation
# import matplotlib.pyplot as plt
# from matplotlib.ticker import FormatStrFormatter, FuncFormatter
# import randomcolor
# import colorsys
# from typing import List, Tuple

# from .utils import format_bps


# def distinct_colors(n: int) -> List[str]:
#     """
#     Generate n visually distinct colors in hex format.
#     """
#     hues = [i / n for i in range(n)]
#     colors = [colorsys.hsv_to_rgb(h, 0.7, 0.9) for h in hues]
#     return ["#%02x%02x%02x" % (int(r*255), int(g*255), int(b*255)) for r, g, b in colors]


# class Graph:
#     def __init__(self, base_stations, clients, xlim: Tuple[int, int], map_limits: Tuple[Tuple[int, int], Tuple[int, int]],
#                  output_dpi: int = 500, scatter_size: int = 15, output_filename: str = 'output.png'):
#         """
#         Initialize the Graph for visualization.
#         """
#         self.output_filename = output_filename
#         self.base_stations = base_stations
#         self.clients = clients
#         self.xlim = xlim
#         self.map_limits = map_limits
#         self.output_dpi = output_dpi
#         self.scatter_size = scatter_size
#         self.fig = plt.figure(figsize=(16,9))
#         #self.fig.canvas.set_window_title('Network Slicing Simulation')
#         self.fig.canvas.manager.set_window_title('Network Slicing Simulation')
#         self.gs = gridspec.GridSpec(4, 3, width_ratios=[6, 3, 3])

#         # Use distinct colors for base stations
#         colors = distinct_colors(len(base_stations))
#         for c, bs in zip(colors, self.base_stations):
#             bs.color = c

#     def draw_live(self, *stats):
#         """
#         Draw the live animation of the simulation.
#         """
#         ani = animation.FuncAnimation(self.fig, self.draw_all, fargs=stats, interval=1000)
#         plt.show()

#     def draw_all(self, *stats):
#         """
#         Draw all plots for the simulation.
#         """
#         plt.clf()
#         self.draw_map()
#         self.draw_stats(*stats)

#     def draw_map(self):
#         """
#         Draw the map with base stations and clients.
#         """
#         markers = ['o', 's', 'p', 'P', '*', 'H', 'X', 'D', 'v', '^', '<', '>', '1', '2', '3', '4']
#         self.ax = plt.subplot(self.gs[:, 0])
#         xlims, ylims = self.map_limits
#         self.ax.set_xlim(xlims)
#         self.ax.set_ylim(ylims)
#         self.ax.yaxis.set_major_formatter(FormatStrFormatter('%.0f m'))
#         self.ax.xaxis.set_major_formatter(FormatStrFormatter('%.0f m'))
#         self.ax.set_aspect('equal')
        
#         # base stations
#         for bs in self.base_stations:
#             circle = plt.Circle(bs.coverage.center, bs.coverage.radius,
#                                 fill=False, linewidth=2, alpha=0.9, color=bs.color)
#             self.ax.add_artist(circle)
        
#         # clients
#         legend_indexed = []
#         for c in self.clients:
#             label = None
#             if c.subscribed_slice_index not in legend_indexed and c.base_station is not None:
#                 label = c.get_slice().name
#                 legend_indexed.append(c.subscribed_slice_index)
#             self.ax.scatter(c.x, c.y,
#                             color=c.base_station.color if c.base_station is not None else '0.8',
#                             label=label, s=15,
#                             marker=markers[c.subscribed_slice_index % len(markers)])

#         box = self.ax.get_position()
#         self.ax.set_position([box.x0 - box.width * 0.05, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

#         leg = self.ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
#                              shadow=True, ncol=5)

#         for i in range(len(legend_indexed)):
#             #leg.legendHandles[i].set_color('k')
#             leg.legend_handles[i].set_color('k')


#     def draw_stats(self, vals, vals1, vals2, vals3, vals4, vals5, vals6):
#         """
#         Draw the statistics plots.
#         """
#         self.ax1 = plt.subplot(self.gs[0, 1])
#         self.ax1.plot(vals)
#         self.ax1.set_xlim(self.xlim)
#         locs = self.ax1.get_xticks()
#         locs[0] = self.xlim[0]
#         locs[-1] = self.xlim[1]
#         self.ax1.set_xticks(locs)
#         self.ax1.use_sticky_edges = False
#         self.ax1.set_title(f'Connected Clients Ratio')

#         self.ax2 = plt.subplot(self.gs[1, 1])
#         self.ax2.plot(vals1)
#         self.ax2.set_xlim(self.xlim)
#         self.ax2.set_xticks(locs)
#         self.ax2.yaxis.set_major_formatter(FuncFormatter(format_bps))
#         self.ax2.use_sticky_edges = False
#         self.ax2.set_title('Total Bandwidth Usage')

#         self.ax3 = plt.subplot(self.gs[2, 1])
#         self.ax3.plot(vals2)
#         self.ax3.set_xlim(self.xlim)
#         self.ax3.set_xticks(locs)
#         self.ax3.use_sticky_edges = False
#         self.ax3.set_title('Bandwidth Usage Ratio in Slices (Averaged)')

#         self.ax4 = plt.subplot(self.gs[3, 1])
#         self.ax4.plot(vals3)
#         self.ax4.set_xlim(self.xlim)
#         self.ax4.set_xticks(locs)
#         self.ax4.use_sticky_edges = False
#         self.ax4.set_title('Client Count Ratio per Slice')

#         self.ax5 = plt.subplot(self.gs[0, 2])
#         self.ax5.plot(vals4)
#         self.ax5.set_xlim(self.xlim)
#         self.ax5.set_xticks(locs)
#         self.ax5.use_sticky_edges = False
#         self.ax5.set_title('Coverage Ratio')

#         self.ax6 = plt.subplot(self.gs[1, 2])
#         self.ax6.plot(vals5)
#         self.ax6.set_xlim(self.xlim)
#         self.ax6.set_xticks(locs)
#         self.ax6.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
#         self.ax6.use_sticky_edges = False
#         self.ax6.set_title('Block ratio')

#         self.ax7 = plt.subplot(self.gs[2, 2])
#         self.ax7.plot(vals6)
#         self.ax7.set_xlim(self.xlim)
#         self.ax7.set_xticks(locs)
#         self.ax7.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
#         self.ax7.use_sticky_edges = False
#         self.ax7.set_title('Handover ratio')

#         self.ax8 = plt.subplot(self.gs[3, 2])
#         row_labels = [
#             'Initial number of clients',
#             'Average connected clients',
#             'Average bandwidth usage',
#             'Average load factor of slices',
#             'Average coverage ratio',
#             'Average block ratio',
#             'Average handover ratio',
#         ]
#         l, r = self.xlim
#         cell_text = [
#             [f'{len(self.clients)}'],
#             [f'{mean(vals[l:r]):.2f}'],
#             [f'{format_bps(mean(vals1[l:r]), return_float=True)}'],
#             [f'{mean(vals2[l:r]):.2f}'],
#             [f'{mean(vals4[l:r]):.2f}'],
#             [f'{mean(vals5[l:r]):.4f}'],
#             [f'{mean(vals6[l:r]):.4f}'],
#         ]
        
#         self.ax8.axis('off')
#         self.ax8.axis('tight')
#         self.ax8.tick_params(axis='x', which='major', pad=15)
#         self.ax8.table(cellText=cell_text, rowLabels=row_labels, colWidths=[0.35, 0.2], loc='center right')

#         plt.tight_layout()

#     def save_fig(self):
#         """
#         Save the current figure to a file.
#         """
#         self.fig.savefig(self.output_filename, dpi=1000)

#     def show_plot(self):
#         """
#         Show the plot window.
#         """
#         plt.show()

#     def get_map_limits(self):
#         """
#         Deprecated: Get the map limits based on base station coverage.
#         """
#         x_min = min([bs.coverage.center[0]-bs.coverage.radius for bs in self.base_stations])
#         x_max = max([bs.coverage.center[0]+bs.coverage.radius for bs in self.base_stations])
#         y_min = min([bs.coverage.center[1]-bs.coverage.radius for bs in self.base_stations])
#         y_max = max([bs.coverage.center[1]+bs.coverage.radius for bs in self.base_stations])

#         return (x_min, x_max), (y_min, y_max)
# from statistics import mean

# from matplotlib import gridspec
# import matplotlib.animation as animation
# import matplotlib.pyplot as plt
# from matplotlib.ticker import FormatStrFormatter, FuncFormatter
# import randomcolor
# import colorsys
# from typing import List, Tuple

# from .utils import format_bps


# def distinct_colors(n: int) -> List[str]:
#     """
#     Generate n visually distinct colors in hex format.
#     """
#     hues = [i / n for i in range(n)]
#     colors = [colorsys.hsv_to_rgb(h, 0.7, 0.9) for h in hues]
#     return ["#%02x%02x%02x" % (int(r*255), int(g*255), int(b*255)) for r, g, b in colors]


# class Graph:
#     def __init__(self, base_stations, clients, xlim: Tuple[int, int], map_limits: Tuple[Tuple[int, int], Tuple[int, int]],
#                  output_dpi: int = 500, scatter_size: int = 15, output_filename: str = 'output.png'):
#         """
#         Initialize the Graph for visualization.
#         """
#         self.output_filename = output_filename
#         self.base_stations = base_stations
#         self.clients = clients
#         self.xlim = xlim
#         self.map_limits = map_limits
#         self.output_dpi = output_dpi
#         self.scatter_size = scatter_size
#         self.fig = plt.figure(figsize=(16,9))
#         #self.fig.canvas.set_window_title('Network Slicing Simulation')
#         if hasattr(self.fig.canvas, "manager"):
#             self.fig.canvas.manager.set_window_title("Network Slicing Simulation")

#         self.gs = gridspec.GridSpec(4, 3, width_ratios=[6, 3, 3])

#         # Use distinct colors for base stations
#         colors = distinct_colors(len(base_stations))
#         for c, bs in zip(colors, self.base_stations):
#             bs.color = c

#     def draw_live(self, *stats):
#         """
#         Draw the live animation of the simulation.
#         """
#         ani = animation.FuncAnimation(self.fig, self.draw_all, fargs=stats, interval=1000)
#         plt.show()

#     def draw_all(self, *stats):
#         """
#         Draw all plots for the simulation.
#         """
#         plt.clf()
#         self.draw_map()
#         self.draw_stats(*stats)

#     def draw_map(self):
#         """
#         Draw the map with base stations and clients.
#         """
#         markers = ['o', 's', 'p', 'P', '*', 'H', 'X', 'D', 'v', '^', '<', '>', '1', '2', '3', '4']
#         self.ax = plt.subplot(self.gs[:, 0])
#         xlims, ylims = self.map_limits
#         self.ax.set_xlim(xlims)
#         self.ax.set_ylim(ylims)
#         self.ax.yaxis.set_major_formatter(FormatStrFormatter('%.0f m'))
#         self.ax.xaxis.set_major_formatter(FormatStrFormatter('%.0f m'))
#         self.ax.set_aspect('equal')
        
#         # base stations
#         for bs in self.base_stations:
#             circle = plt.Circle(bs.coverage.center, bs.coverage.radius,
#                                 fill=False, linewidth=2, alpha=0.9, color=bs.color)
#             self.ax.add_artist(circle)
        
#         # clients
#         legend_indexed = []
#         for c in self.clients:
#             label = None
#             if c.subscribed_slice_index not in legend_indexed and c.base_station is not None:
#                 label = c.get_slice().name
#                 legend_indexed.append(c.subscribed_slice_index)
#             self.ax.scatter(c.x, c.y,
#                             color=c.base_station.color if c.base_station is not None else '0.8',
#                             label=label, s=15,
#                             marker=markers[c.subscribed_slice_index % len(markers)])

#         box = self.ax.get_position()
#         self.ax.set_position([box.x0 - box.width * 0.05, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

#         leg = self.ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05),
#                              shadow=True, ncol=5)

#         for i in range(len(legend_indexed)):
#             leg.legendHandles[i].set_color('k')

#     def draw_stats(self, vals, vals1, vals2, vals3, vals4, vals5, vals6):
#         """
#         Draw the statistics plots.
#         """
#         self.ax1 = plt.subplot(self.gs[0, 1])
#         self.ax1.plot(vals)
#         self.ax1.set_xlim(self.xlim)
#         locs = self.ax1.get_xticks()
#         locs[0] = self.xlim[0]
#         locs[-1] = self.xlim[1]
#         self.ax1.set_xticks(locs)
#         self.ax1.use_sticky_edges = False
#         self.ax1.set_title(f'Connected Clients Ratio')

#         self.ax2 = plt.subplot(self.gs[1, 1])
#         self.ax2.plot(vals1)
#         self.ax2.set_xlim(self.xlim)
#         self.ax2.set_xticks(locs)
#         self.ax2.yaxis.set_major_formatter(FuncFormatter(format_bps))
#         self.ax2.use_sticky_edges = False
#         self.ax2.set_title('Total Bandwidth Usage')

#         self.ax3 = plt.subplot(self.gs[2, 1])
#         self.ax3.plot(vals2)
#         self.ax3.set_xlim(self.xlim)
#         self.ax3.set_xticks(locs)
#         self.ax3.use_sticky_edges = False
#         self.ax3.set_title('Bandwidth Usage Ratio in Slices (Averaged)')

#         self.ax4 = plt.subplot(self.gs[3, 1])
#         self.ax4.plot(vals3)
#         self.ax4.set_xlim(self.xlim)
#         self.ax4.set_xticks(locs)
#         self.ax4.use_sticky_edges = False
#         self.ax4.set_title('Client Count Ratio per Slice')

#         self.ax5 = plt.subplot(self.gs[0, 2])
#         self.ax5.plot(vals4)
#         self.ax5.set_xlim(self.xlim)
#         self.ax5.set_xticks(locs)
#         self.ax5.use_sticky_edges = False
#         self.ax5.set_title('Coverage Ratio')

#         self.ax6 = plt.subplot(self.gs[1, 2])
#         self.ax6.plot(vals5)
#         self.ax6.set_xlim(self.xlim)
#         self.ax6.set_xticks(locs)
#         self.ax6.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
#         self.ax6.use_sticky_edges = False
#         self.ax6.set_title('Block ratio')

#         self.ax7 = plt.subplot(self.gs[2, 2])
#         self.ax7.plot(vals6)
#         self.ax7.set_xlim(self.xlim)
#         self.ax7.set_xticks(locs)
#         self.ax7.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
#         self.ax7.use_sticky_edges = False
#         self.ax7.set_title('Handover ratio')

#         self.ax8 = plt.subplot(self.gs[3, 2])
#         row_labels = [
#             'Initial number of clients',
#             'Average connected clients',
#             'Average bandwidth usage',
#             'Average load factor of slices',
#             'Average coverage ratio',
#             'Average block ratio',
#             'Average handover ratio',
#         ]
#         l, r = self.xlim
#         cell_text = [
#             [f'{len(self.clients)}'],
#             [f'{mean(vals[l:r]):.2f}'],
#             [f'{format_bps(mean(vals1[l:r]), return_float=True)}'],
#             [f'{mean(vals2[l:r]):.2f}'],
#             [f'{mean(vals4[l:r]):.2f}'],
#             [f'{mean(vals5[l:r]):.4f}'],
#             [f'{mean(vals6[l:r]):.4f}'],
#         ]
        
#         self.ax8.axis('off')
#         self.ax8.axis('tight')
#         self.ax8.tick_params(axis='x', which='major', pad=15)
#         self.ax8.table(cellText=cell_text, rowLabels=row_labels, colWidths=[0.35, 0.2], loc='center right')

#         plt.tight_layout()

#     def save_fig(self):
#         """
#         Save the current figure to a file.
#         """
#         self.fig.savefig(self.output_filename, dpi=1000)

#     def show_plot(self):
#         """
#         Show the plot window.
#         """
#         plt.show()

#     def get_map_limits(self):
#         """
#         Deprecated: Get the map limits based on base station coverage.
#         """
#         x_min = min([bs.coverage.center[0]-bs.coverage.radius for bs in self.base_stations])
#         x_max = max([bs.coverage.center[0]+bs.coverage.radius for bs in self.base_stations])
#         y_min = min([bs.coverage.center[1]-bs.coverage.radius for bs in self.base_stations])
#         y_max = max([bs.coverage.center[1]+bs.coverage.radius for bs in self.base_stations])

#         return (x_min, x_max), (y_min, y_max)



from statistics import mean
from typing import List, Tuple

from matplotlib import gridspec
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter, FuncFormatter
import colorsys

from .utils import format_bps


def distinct_colors(n: int) -> List[str]:
    """
    Generate n visually distinct colors in hex format.
    """
    hues = [i / n for i in range(n)]
    colors = [colorsys.hsv_to_rgb(h, 0.7, 0.9) for h in hues]
    return ["#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255)) for r, g, b in colors]


def time_axis(values, step_seconds=1):
    """
    Generate time axis in seconds.
    """
    return [i * step_seconds for i in range(len(values))]


class Graph:
    def __init__(
        self,
        base_stations,
        clients,
        xlim: Tuple[int, int],
        map_limits: Tuple[Tuple[int, int], Tuple[int, int]],
        output_dpi: int = 500,
        scatter_size: int = 15,
        output_filename: str = "output.png",
    ):
        self.output_filename = output_filename
        self.base_stations = base_stations
        self.clients = clients
        self.xlim = xlim
        self.map_limits = map_limits
        self.output_dpi = output_dpi
        self.scatter_size = scatter_size

        self.fig = plt.figure(figsize=(16, 9))
        if hasattr(self.fig.canvas, "manager"):
            self.fig.canvas.manager.set_window_title("Network Slicing Simulation")

        self.gs = gridspec.GridSpec(4, 3, width_ratios=[6, 3, 3])

        colors = distinct_colors(len(base_stations))
        for c, bs in zip(colors, self.base_stations):
            bs.color = c

    def draw_live(self, *stats):
        ani = animation.FuncAnimation(
            self.fig, self.draw_all, fargs=stats, interval=1000
        )
        plt.show()

    def draw_all(self, *stats):
        plt.clf()
        self.draw_map()
        self.draw_stats(*stats)

    # ===================== MAP =====================
    def draw_map(self):
        markers = [
            "o", "s", "p", "P", "*", "H", "X", "D",
            "v", "^", "<", ">", "1", "2", "3", "4"
        ]

        self.ax = plt.subplot(self.gs[:, 0])
        xlims, ylims = self.map_limits
        self.ax.set_xlim(xlims)
        self.ax.set_ylim(ylims)
        self.ax.set_aspect("equal")

        self.ax.set_xlabel("X Position (meters)")
        self.ax.set_ylabel("Y Position (meters)")
        self.ax.xaxis.set_major_formatter(FormatStrFormatter("%.0f m"))
        self.ax.yaxis.set_major_formatter(FormatStrFormatter("%.0f m"))

        # Base stations
        for bs in self.base_stations:
            circle = plt.Circle(
                bs.coverage.center,
                bs.coverage.radius,
                fill=False,
                linewidth=2,
                alpha=0.9,
                color=bs.color,
            )
            self.ax.add_artist(circle)

        # Clients
        for c in self.clients:
            self.ax.scatter(
                c.x,
                c.y,
                color=c.base_station.color if c.base_station else "0.8",
                s=self.scatter_size,
                marker=markers[c.subscribed_slice_index % len(markers)],
            )

        # ---------- Vertical Legend ----------
        handles, labels = [], []
        for bs in self.base_stations:
            for sl in bs.slices:
                if sl.name not in labels:
                    handles.append(
                        plt.Line2D(
                            [0], [0],
                            marker="o",
                            linestyle="",
                            markerfacecolor=bs.color,
                            markersize=8,
                        )
                    )
                    labels.append(sl.name)

        self.ax.legend(
            handles,
            labels,
            title="Network Slices",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=True,
        )

    # ===================== STATS =====================
    def draw_stats(self, vals, vals1, vals2, vals3, vals4, vals5, vals6):

        self.ax1 = plt.subplot(self.gs[0, 1])
        self.ax1.plot(time_axis(vals), vals)
        self.ax1.set_title("Connected Clients Ratio")
        self.ax1.set_xlabel("Time (seconds)")
        self.ax1.set_ylabel("Ratio (0–1)")

        self.ax2 = plt.subplot(self.gs[1, 1])
        self.ax2.plot(time_axis(vals1), vals1)
        self.ax2.set_title("Total Bandwidth Usage")
        self.ax2.set_xlabel("Time (seconds)")
        self.ax2.set_ylabel("Bandwidth")
        self.ax2.yaxis.set_major_formatter(FuncFormatter(format_bps))

        self.ax3 = plt.subplot(self.gs[2, 1])
        self.ax3.plot(time_axis(vals2), vals2)
        self.ax3.set_title("Average Slice Load Ratio")
        self.ax3.set_xlabel("Time (seconds)")
        self.ax3.set_ylabel("Load Ratio")

        self.ax4 = plt.subplot(self.gs[3, 1])
        self.ax4.plot(time_axis(vals3), vals3)
        self.ax4.set_title("Average Clients per Slice")
        self.ax4.set_xlabel("Time (seconds)")
        self.ax4.set_ylabel("Clients")

        self.ax5 = plt.subplot(self.gs[0, 2])
        self.ax5.plot(time_axis(vals4), vals4)
        self.ax5.set_title("Coverage Ratio")
        self.ax5.set_xlabel("Time (seconds)")
        self.ax5.set_ylabel("Ratio (0–1)")

        self.ax6 = plt.subplot(self.gs[1, 2])
        self.ax6.plot(time_axis(vals5), vals5)
        self.ax6.set_title("Block Ratio")
        self.ax6.set_xlabel("Time (seconds)")
        self.ax6.set_ylabel("Blocked Attempts Ratio")

        self.ax7 = plt.subplot(self.gs[2, 2])
        self.ax7.plot(time_axis(vals6), vals6)
        self.ax7.set_title("Handover Ratio")
        self.ax7.set_xlabel("Time (seconds)")
        self.ax7.set_ylabel("Handovers / Attempt")

        # ---------- Summary Table ----------
        self.ax8 = plt.subplot(self.gs[3, 2])
        self.ax8.axis("off")

        row_labels = [
            "Initial number of clients",
            "Average connected clients",
            "Average bandwidth usage",
            "Average slice load",
            "Average coverage ratio",
            "Average block ratio",
            "Average handover ratio",
        ]

        cell_text = [
            [f"{len(self.clients)}"],
            [f"{mean(vals):.2f}"],
            [f"{format_bps(mean(vals1), return_float=True)}"],
            [f"{mean(vals2):.2f}"],
            [f"{mean(vals4):.2f}"],
            [f"{mean(vals5):.4f}"],
            [f"{mean(vals6):.4f}"],
        ]

        self.ax8.table(
            cellText=cell_text,
            rowLabels=row_labels,
            colWidths=[0.6],
            loc="center",
        )

        plt.tight_layout()

    def save_fig(self):
        self.fig.savefig(self.output_filename, dpi=self.output_dpi)

    def show_plot(self):
        plt.show()



# from statistics import mean

# from matplotlib import gridspec
# import matplotlib.animation as animation
# import matplotlib.pyplot as plt
# from matplotlib.ticker import FormatStrFormatter, FuncFormatter
# import colorsys
# from typing import List, Tuple

# from .utils import format_bps


# def distinct_colors(n: int) -> List[str]:
#     """
#     Generate n visually distinct colors in hex format.
#     """
#     hues = [i / n for i in range(n)]
#     colors = [colorsys.hsv_to_rgb(h, 0.7, 0.9) for h in hues]
#     return ["#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255)) for r, g, b in colors]


# ####### CHANGED
# def time_axis(vals):
#     """Generate simulation time axis"""
#     return list(range(len(vals)))


# class Graph:
#     def __init__(
#         self,
#         base_stations,
#         clients,
#         xlim: Tuple[int, int],
#         map_limits: Tuple[Tuple[int, int], Tuple[int, int]],
#         output_dpi: int = 500,
#         scatter_size: int = 15,
#         output_filename: str = "output.png",
#     ):
#         """
#         Initialize the Graph for visualization.
#         """
#         self.output_filename = output_filename
#         self.base_stations = base_stations
#         self.clients = clients
#         self.xlim = xlim
#         self.map_limits = map_limits
#         self.output_dpi = output_dpi
#         self.scatter_size = scatter_size

#         self.fig = plt.figure(figsize=(16, 9))
#         if hasattr(self.fig.canvas, "manager"):
#             self.fig.canvas.manager.set_window_title("Network Slicing Simulation")

#         self.gs = gridspec.GridSpec(4, 3, width_ratios=[6, 3, 3])

#         colors = distinct_colors(len(base_stations))
#         for c, bs in zip(colors, self.base_stations):
#             bs.color = c

#     def draw_live(self, *stats):
#         """
#         Draw the live animation of the simulation.
#         """
#         ani = animation.FuncAnimation(self.fig, self.draw_all, fargs=stats, interval=1000)
#         plt.show()

#     def draw_all(self, *stats):
#         """
#         Draw all plots for the simulation.
#         """
#         plt.clf()
#         self.draw_map()
#         self.draw_stats(*stats)

#     def draw_map(self):
#         """
#         Draw the map with base stations and clients.
#         """
#         markers = ['o', 's', 'p', 'P', '*', 'H', 'X', 'D', 'v', '^', '<', '>', '1', '2', '3', '4']
#         self.ax = plt.subplot(self.gs[:, 0])
#         xlims, ylims = self.map_limits
#         self.ax.set_xlim(xlims)
#         self.ax.set_ylim(ylims)
#         self.ax.set_aspect("equal")

#         self.ax.set_xlabel("X Position (meters)")     ####### CHANGED
#         self.ax.set_ylabel("Y Position (meters)")     ####### CHANGED

#         self.ax.xaxis.set_major_formatter(FormatStrFormatter('%.0f m'))
#         self.ax.yaxis.set_major_formatter(FormatStrFormatter('%.0f m'))

#         # Base stations
#         for bs in self.base_stations:
#             circle = plt.Circle(
#                 bs.coverage.center,
#                 bs.coverage.radius,
#                 fill=False,
#                 linewidth=2,
#                 alpha=0.9,
#                 color=bs.color,
#             )
#             self.ax.add_artist(circle)

#         # Clients
#         for c in self.clients:
#             self.ax.scatter(
#                 c.x,
#                 c.y,
#                 color=c.base_station.color if c.base_station is not None else "0.8",
#                 s=self.scatter_size,
#                 marker=markers[c.subscribed_slice_index % len(markers)],
#             )

#         ####### CHANGED — Proper legend for slices
#         handles = []
#         labels = []

#         for bs in self.base_stations:
#             for sl in bs.slices:
#                 if sl.name not in labels:
#                     handles.append(
#                         plt.Line2D(
#                             [0],
#                             [0],
#                             marker="o",
#                             linestyle="",
#                             markerfacecolor=bs.color,
#                             markersize=8,
#                         )
#                     )
#                     labels.append(sl.name)

#         self.ax.legend(
#             handles,
#             labels,
#             loc="upper center",
#             bbox_to_anchor=(0.5, -0.08),
#             ncol=4,
#             frameon=True,
#         )

#     # def draw_stats(self, vals, vals1, vals2, vals3, vals4, vals5, vals6):
#     #     """
#     #     Draw the statistics plots.
#     #     """
#     #     t = time_axis(vals)     ####### CHANGED

#     #     self.ax1 = plt.subplot(self.gs[0, 1])
#     #     self.ax1.plot(t, vals)
#     #     self.ax1.set_title("Connected Clients Ratio")
#     #     self.ax1.set_ylabel("Ratio")                 ####### CHANGED
#     #     self.ax1.set_xlabel("Simulation Time")       ####### CHANGED

#     #     self.ax2 = plt.subplot(self.gs[1, 1])
#     #     self.ax2.plot(t, vals1)
#     #     self.ax2.set_title("Total Bandwidth Usage")
#     #     self.ax2.set_ylabel("Bandwidth")             ####### CHANGED
#     #     self.ax2.set_xlabel("Simulation Time")       ####### CHANGED
#     #     self.ax2.yaxis.set_major_formatter(FuncFormatter(format_bps))

#     #     self.ax3 = plt.subplot(self.gs[2, 1])
#     #     self.ax3.plot(t, vals2)
#     #     self.ax3.set_title("Average Slice Load Ratio")
#     #     self.ax3.set_ylabel("Load Ratio")             ####### CHANGED
#     #     self.ax3.set_xlabel("Simulation Time")       ####### CHANGED

#     #     self.ax4 = plt.subplot(self.gs[3, 1])
#     #     self.ax4.plot(t, vals3)
#     #     self.ax4.set_title("Average Clients per Slice")
#     #     self.ax4.set_ylabel("Clients")               ####### CHANGED
#     #     self.ax4.set_xlabel("Simulation Time")       ####### CHANGED

#     #     self.ax5 = plt.subplot(self.gs[0, 2])
#     #     self.ax5.plot(t, vals4)
#     #     self.ax5.set_title("Coverage Ratio")
#     #     self.ax5.set_ylabel("Ratio")                 ####### CHANGED
#     #     self.ax5.set_xlabel("Simulation Time")       ####### CHANGED

#     #     self.ax6 = plt.subplot(self.gs[1, 2])
#     #     self.ax6.plot(t, vals5)
#     #     self.ax6.set_title("Block Ratio")
#     #     self.ax6.set_ylabel("Ratio")                 ####### CHANGED
#     #     self.ax6.set_xlabel("Simulation Time")       ####### CHANGED

#     #     self.ax7 = plt.subplot(self.gs[2, 2])
#     #     self.ax7.plot(t, vals6)
#     #     self.ax7.set_title("Handover Ratio")
#     #     self.ax7.set_ylabel("Ratio")                 ####### CHANGED
#     #     self.ax7.set_xlabel("Simulation Time")       ####### CHANGED

#     #     self.ax8 = plt.subplot(self.gs[3, 2])
#     #     self.ax8.axis("off")

#     #     row_labels = [
#     #         "Initial clients",
#     #         "Avg connected clients",
#     #         "Avg bandwidth usage",
#     #         "Avg slice load",
#     #         "Avg coverage",
#     #         "Avg block ratio",
#     #         "Avg handover ratio",
#     #     ]

#     #     cell_text = [
#     #         [f"{len(self.clients)}"],
#     #         [f"{mean(vals):.2f}"],
#     #         [f"{format_bps(mean(vals1), return_float=True)}"],
#     #         [f"{mean(vals2):.2f}"],
#     #         [f"{mean(vals4):.2f}"],
#     #         [f"{mean(vals5):.4f}"],
#     #         [f"{mean(vals6):.4f}"],
#     #     ]

#     #     self.ax8.table(
#     #         cellText=cell_text,
#     #         rowLabels=row_labels,
#     #         colWidths=[0.55],
#     #         loc="center",
#     #     )

#     #     plt.tight_layout()
#     def draw_stats(self, vals, vals1, vals2, vals3, vals4, vals5, vals6):

#         ####### CHANGED
#         def t_for(v):
#             return list(range(len(v)))

#         self.ax1 = plt.subplot(self.gs[0, 1])
#         self.ax1.plot(t_for(vals), vals)
#         self.ax1.set_title("Connected Clients Ratio")
#         self.ax1.set_ylabel("Ratio")
#         self.ax1.set_xlabel("Simulation Time")

#         self.ax2 = plt.subplot(self.gs[1, 1])
#         self.ax2.plot(t_for(vals1), vals1)
#         self.ax2.set_title("Total Bandwidth Usage")
#         self.ax2.set_ylabel("Bandwidth")
#         self.ax2.set_xlabel("Simulation Time")
#         self.ax2.yaxis.set_major_formatter(FuncFormatter(format_bps))

#         self.ax3 = plt.subplot(self.gs[2, 1])
#         self.ax3.plot(t_for(vals2), vals2)
#         self.ax3.set_title("Average Slice Load Ratio")
#         self.ax3.set_ylabel("Load Ratio")
#         self.ax3.set_xlabel("Simulation Time")

#         self.ax4 = plt.subplot(self.gs[3, 1])
#         self.ax4.plot(t_for(vals3), vals3)
#         self.ax4.set_title("Average Clients per Slice")
#         self.ax4.set_ylabel("Clients")
#         self.ax4.set_xlabel("Simulation Time")

#         self.ax5 = plt.subplot(self.gs[0, 2])
#         self.ax5.plot(t_for(vals4), vals4)
#         self.ax5.set_title("Coverage Ratio")
#         self.ax5.set_ylabel("Ratio")
#         self.ax5.set_xlabel("Simulation Time")

#         self.ax6 = plt.subplot(self.gs[1, 2])
#         self.ax6.plot(t_for(vals5), vals5)   ####### CHANGED
#         self.ax6.set_title("Block Ratio")
#         self.ax6.set_ylabel("Ratio")
#         self.ax6.set_xlabel("Simulation Time")

#         self.ax7 = plt.subplot(self.gs[2, 2])
#         self.ax7.plot(t_for(vals6), vals6)   ####### CHANGED
#         self.ax7.set_title("Handover Ratio")
#         self.ax7.set_ylabel("Ratio")
#         self.ax7.set_xlabel("Simulation Time")

#         self.ax8 = plt.subplot(self.gs[3, 2])
#         self.ax8.axis("off")

#         row_labels = [
#             "Initial clients",
#             "Avg connected clients",
#             "Avg bandwidth usage",
#             "Avg slice load",
#             "Avg coverage",
#             "Avg block ratio",
#             "Avg handover ratio",
#         ]

#         cell_text = [
#             [f"{len(self.clients)}"],
#             [f"{mean(vals):.2f}"],
#             [f"{format_bps(mean(vals1), return_float=True)}"],
#             [f"{mean(vals2):.2f}"],
#             [f"{mean(vals4):.2f}"],
#             [f"{mean(vals5):.4f}"],
#             [f"{mean(vals6):.4f}"],
#         ]

#         self.ax8.table(
#             cellText=cell_text,
#             rowLabels=row_labels,
#             colWidths=[0.55],
#             loc="center",
#         )

#         plt.tight_layout()

#     def save_fig(self):
#         """
#         Save the current figure to a file.
#         """
#         self.fig.savefig(self.output_filename, dpi=self.output_dpi)

#     def show_plot(self):
#         """
#         Show the plot window.
#         """
#         plt.show()
