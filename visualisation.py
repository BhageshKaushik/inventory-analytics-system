"""
visualisation.py
================
Generates and saves all Matplotlib charts for the system.

Design decisions
----------------
* All numbers are computed by the Analytics class (manual Python code),
  not by Matplotlib or any data library.
* Charts are saved to the reports/ directory as PNG files.
* Non-interactive backend ("Agg") is used so charts save without
  requiring a display — works on headless servers too.
* Professional styling: readable fonts, gridlines, tight layout.
"""

import os
import matplotlib
matplotlib.use("Agg")           # Must be set before importing pyplot
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


REPORTS_DIR = "reports"


class Visualisation:
    """
    Creates and saves Matplotlib charts from analytics data.

    Parameters
    ----------
    analytics : Analytics — the analytics engine to pull numbers from.
    """

    def __init__(self, analytics):
        self._analytics = analytics
        os.makedirs(REPORTS_DIR, exist_ok=True)

    # ──────────────────────────────────────────────────────────────────────
    # Chart 1 — Bar chart: Total Sales by State
    # ──────────────────────────────────────────────────────────────────────

    def bar_sales_by_state(self, top_n: int = 15) -> str:
        """
        Horizontal bar chart of total sales revenue by ship-state.

        Parameters
        ----------
        top_n : int — how many top states to display (default 15).

        Returns
        -------
        str — file path of the saved chart.
        """
        data   = self._analytics.all_states_sales()[:top_n]
        states = [d["state"] for d in data]
        amounts = [d["total_amount"] for d in data]

        fig, ax = plt.subplots(figsize=(12, 7))

        bars = ax.barh(states, amounts, color="#4C72B0", edgecolor="white",
                       linewidth=0.6)
        ax.set_xlabel("Total Sales Amount (INR)", fontsize=12, labelpad=10)
        ax.set_ylabel("State", fontsize=12, labelpad=10)
        ax.set_title(f"Top {top_n} States by Total Sales Revenue",
                     fontsize=15, fontweight="bold", pad=15)
        ax.invert_yaxis()   # highest bar at top
        ax.xaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"₹{x/1_000_000:.1f}M")
        )
        ax.grid(axis="x", linestyle="--", alpha=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Value labels inside bars
        for bar, amt in zip(bars, amounts):
            ax.text(bar.get_width() * 0.98, bar.get_y() + bar.get_height() / 2,
                    f"₹{amt/1_000_000:.2f}M",
                    va="center", ha="right", fontsize=8, color="white",
                    fontweight="bold")

        plt.tight_layout()
        path = os.path.join(REPORTS_DIR, "sales_by_state.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"[Visualisation] Saved: {path}")
        return path

    # ──────────────────────────────────────────────────────────────────────
    # Chart 2 — Pie chart: Order Status Distribution
    # ──────────────────────────────────────────────────────────────────────

    def pie_order_status(self) -> str:
        """
        Pie chart showing the distribution of order Status.

        Returns
        -------
        str — file path of the saved chart.
        """
        distribution = self._analytics.order_status_distribution()

        # Sort slices by count descending so the chart is readable
        items = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in items]
        counts = [item[1] for item in items]

        # Colour palette
        colours = [
            "#4C72B0", "#DD8452", "#55A868", "#C44E52",
            "#8172B2", "#937860", "#DA8BC3", "#8C8C8C",
        ]
        # Pad colours if more slices than colours
        while len(colours) < len(labels):
            colours.append("#AAAAAA")

        fig, ax = plt.subplots(figsize=(9, 7))
        wedges, texts, autotexts = ax.pie(
            counts,
            labels=None,
            colors=colours[:len(labels)],
            autopct="%1.1f%%",
            startangle=140,
            pctdistance=0.82,
            wedgeprops={"edgecolor": "white", "linewidth": 1.5}
        )

        for at in autotexts:
            at.set_fontsize(9)
            at.set_color("white")
            at.set_fontweight("bold")

        ax.legend(wedges, [f"{l} ({c:,})" for l, c in zip(labels, counts)],
                  title="Status", loc="center left",
                  bbox_to_anchor=(1, 0, 0.5, 1), fontsize=9)
        ax.set_title("Order Status Distribution",
                     fontsize=15, fontweight="bold", pad=20)

        plt.tight_layout()
        path = os.path.join(REPORTS_DIR, "order_status_pie.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"[Visualisation] Saved: {path}")
        return path

    # ──────────────────────────────────────────────────────────────────────
    # Chart 3 — Bar chart: Total Sales by Category
    # ──────────────────────────────────────────────────────────────────────

    def bar_sales_by_category(self) -> str:
        """
        Vertical bar chart of total sales revenue per Category.

        Returns
        -------
        str — file path of the saved chart.
        """
        data       = self._analytics.category_performance()
        categories = [d["category"] for d in data]
        amounts    = [d["total_amount"] for d in data]

        fig, ax = plt.subplots(figsize=(13, 6))

        x = range(len(categories))
        bars = ax.bar(x, amounts, color="#55A868", edgecolor="white",
                      linewidth=0.6, width=0.6)

        ax.set_xticks(list(x))
        ax.set_xticklabels(categories, rotation=35, ha="right", fontsize=9)
        ax.set_ylabel("Total Sales Amount (INR)", fontsize=12, labelpad=10)
        ax.set_title("Total Sales Revenue by Product Category",
                     fontsize=15, fontweight="bold", pad=15)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda y, _: f"₹{y/1_000_000:.1f}M")
        )
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Value labels above bars
        for bar, amt in zip(bars, amounts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 10_000,
                    f"₹{amt/1_000_000:.2f}M",
                    ha="center", va="bottom", fontsize=7.5, rotation=90)

        plt.tight_layout()
        path = os.path.join(REPORTS_DIR, "sales_by_category.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"[Visualisation] Saved: {path}")
        return path

    # ──────────────────────────────────────────────────────────────────────
    # Chart 4 — Line chart: Monthly Sales Trend
    # ──────────────────────────────────────────────────────────────────────

    def line_monthly_sales(self) -> str:
        """
        Line chart showing total sales amount per month, sorted
        chronologically.

        Returns
        -------
        str — file path of the saved chart.
        """
        seasonal = self._analytics.seasonal_patterns()
        monthly  = seasonal["monthly"]

        # Sort month keys chronologically (format: "MM-YYYY")
        def month_sort_key(mkey):
            parts = mkey.split("-")
            return (int(parts[1]), int(parts[0]))   # (year, month)

        sorted_keys   = sorted(monthly.keys(), key=month_sort_key)
        amounts        = [monthly[k]["total_amount"] for k in sorted_keys]
        order_counts   = [monthly[k]["order_count"]  for k in sorted_keys]

        fig, ax1 = plt.subplots(figsize=(13, 6))

        # Primary axis: sales amount
        colour_line = "#4C72B0"
        ax1.plot(sorted_keys, amounts, marker="o", color=colour_line,
                 linewidth=2, markersize=6, label="Total Sales (INR)")
        ax1.fill_between(sorted_keys, amounts, alpha=0.15, color=colour_line)
        ax1.set_xlabel("Month", fontsize=12, labelpad=10)
        ax1.set_ylabel("Total Sales Amount (INR)", fontsize=12,
                       color=colour_line, labelpad=10)
        ax1.tick_params(axis="y", labelcolor=colour_line)
        ax1.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda y, _: f"₹{y/1_000_000:.1f}M")
        )
        ax1.set_xticks(range(len(sorted_keys)))
        ax1.set_xticklabels(sorted_keys, rotation=45, ha="right", fontsize=9)

        # Secondary axis: order count
        ax2 = ax1.twinx()
        ax2.bar(sorted_keys, order_counts, alpha=0.25, color="#DD8452",
                width=0.5, label="Order Count")
        ax2.set_ylabel("Number of Orders", fontsize=12, color="#DD8452",
                       labelpad=10)
        ax2.tick_params(axis="y", labelcolor="#DD8452")

        ax1.set_title("Monthly Sales Trend (Amount & Order Volume)",
                      fontsize=15, fontweight="bold", pad=15)

        # Combined legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2,
                   loc="upper left", fontsize=9)

        ax1.grid(axis="y", linestyle="--", alpha=0.4)
        ax1.spines["top"].set_visible(False)

        plt.tight_layout()
        path = os.path.join(REPORTS_DIR, "monthly_sales_trend.png")
        plt.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"[Visualisation] Saved: {path}")
        return path

    # ──────────────────────────────────────────────────────────────────────
    # Generate all charts at once
    # ──────────────────────────────────────────────────────────────────────

    def generate_all_charts(self) -> list:
        """
        Generate and save all four charts.

        Returns
        -------
        list[str] — paths to all saved chart files.
        """
        paths = []
        print("\n[Visualisation] Generating all charts...")
        try:
            paths.append(self.bar_sales_by_state())
        except Exception as e:
            print(f"[ERROR] bar_sales_by_state: {e}")
        try:
            paths.append(self.pie_order_status())
        except Exception as e:
            print(f"[ERROR] pie_order_status: {e}")
        try:
            paths.append(self.bar_sales_by_category())
        except Exception as e:
            print(f"[ERROR] bar_sales_by_category: {e}")
        try:
            paths.append(self.line_monthly_sales())
        except Exception as e:
            print(f"[ERROR] line_monthly_sales: {e}")

        print(f"[Visualisation] Done. {len(paths)} chart(s) saved to '{REPORTS_DIR}/'.")
        return paths
