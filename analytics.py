"""
analytics.py
============
All sales and inventory analytical functions.

Design decisions
----------------
* All aggregations use manual Python loops — no Pandas, NumPy, or external
  analysis libraries.
* The Analytics class takes an OrderManager instance and reads orders from it.
* Every method returns structured Python dicts/lists so the CLI and
  Visualisation modules can consume them directly.
* Limitations and assumptions are documented inline and surfaced to the CLI.
"""

from algorithms import (
    quick_sort_by_amount,
    quick_sort_by_qty,
    heap_top_n,
    merge_sort_by_date,
)
from datetime import datetime


class Analytics:
    """
    Provides all analytical operations on the order dataset.

    Parameters
    ----------
    order_manager : OrderManager — the loaded order collection.
    """

    def __init__(self, order_manager):
        self._om = order_manager

    # ──────────────────────────────────────────────────────────────────────
    # 1. Top Sales Analysis
    # ──────────────────────────────────────────────────────────────────────

    def top_n_by_amount(self, n: int = 10) -> list:
        """
        Find the top N SKUs by total revenue (Amount).

        Approach
        --------
        1. Aggregate: sum Amount per SKU using a dict.
        2. Convert dict to list of (sku, total_amount) tuples.
        3. Sort descending using Quick Sort (manual implementation).
        4. Return top N.

        Returns
        -------
        list of dict: [{"sku": str, "total_amount": float}, ...]
        """
        totals = {}   # { sku: total_amount }

        for order in self._om.get_all_orders():
            sku = order.sku or "Unknown"
            totals[sku] = totals.get(sku, 0.0) + order.amount

        # Convert to sortable objects (we wrap in simple dicts)
        # Use our manual quick_sort via a wrapper
        items = [{"sku": k, "total_amount": v} for k, v in totals.items()]

        # Manual quick sort on dicts
        sorted_items = self._quick_sort_dicts(items, "total_amount", descending=True)
        return sorted_items[:n]

    def top_n_by_qty(self, n: int = 10) -> list:
        """
        Find the top N SKUs by total quantity sold.

        Returns
        -------
        list of dict: [{"sku": str, "total_qty": int}, ...]
        """
        totals = {}

        for order in self._om.get_all_orders():
            sku = order.sku or "Unknown"
            totals[sku] = totals.get(sku, 0) + order.qty

        items = [{"sku": k, "total_qty": v} for k, v in totals.items()]
        sorted_items = self._quick_sort_dicts(items, "total_qty", descending=True)
        return sorted_items[:n]

    # ──────────────────────────────────────────────────────────────────────
    # 2. Sales by Location
    # ──────────────────────────────────────────────────────────────────────

    def sales_by_city(self, city: str) -> dict:
        """
        Calculate total Amount for a given ship-city.

        Uses the city hash index from OrderManager for O(1) lookup.

        Returns
        -------
        dict: {"city": str, "total_amount": float, "order_count": int}
        """
        city = city.strip().upper()
        orders = self._om.get_by_city(city)
        total = sum(o.amount for o in orders)
        return {"city": city, "total_amount": total, "order_count": len(orders)}

    def sales_by_state(self, state: str) -> dict:
        """
        Calculate total Amount for a given ship-state.

        Linear scan required (no state index built) — O(n).

        Returns
        -------
        dict: {"state": str, "total_amount": float, "order_count": int}
        """
        state = state.strip().upper()
        total = 0.0
        count = 0

        for order in self._om.get_all_orders():
            if order.ship_state == state:
                total += order.amount
                count += 1

        return {"state": state, "total_amount": total, "order_count": count}

    def all_states_sales(self) -> list:
        """
        Calculate total sales for every state.

        Returns
        -------
        list of dict sorted descending by total_amount.
        """
        totals = {}

        for order in self._om.get_all_orders():
            state = order.ship_state or "Unknown"
            totals[state] = totals.get(state, 0.0) + order.amount

        items = [{"state": k, "total_amount": v} for k, v in totals.items()]
        return self._quick_sort_dicts(items, "total_amount", descending=True)

    # ──────────────────────────────────────────────────────────────────────
    # 3. Order Status Distribution
    # ──────────────────────────────────────────────────────────────────────

    def order_status_distribution(self) -> dict:
        """
        Count the number of orders in each Status.

        Uses linear scan (O(n)) — appropriate because:
        * Status is not indexed.
        * We need counts for ALL statuses (not a targeted search).

        Returns
        -------
        dict: { status_string: count }
        """
        distribution = {}

        for order in self._om.get_all_orders():
            status = order.status or "Unknown"
            distribution[status] = distribution.get(status, 0) + 1

        return distribution

    # ──────────────────────────────────────────────────────────────────────
    # 4. Category Performance
    # ──────────────────────────────────────────────────────────────────────

    def category_performance(self) -> list:
        """
        Calculate total Amount and total Qty for each Category.

        Returns
        -------
        list of dict sorted by total_amount descending:
        [{"category": str, "total_amount": float, "total_qty": int}, ...]
        """
        perf = {}   # { category: {"total_amount": float, "total_qty": int} }

        for order in self._om.get_all_orders():
            cat = order.category or "Unknown"
            if cat not in perf:
                perf[cat] = {"total_amount": 0.0, "total_qty": 0}
            perf[cat]["total_amount"] += order.amount
            perf[cat]["total_qty"]    += order.qty

        items = [
            {"category": k, "total_amount": v["total_amount"], "total_qty": v["total_qty"]}
            for k, v in perf.items()
        ]
        return self._quick_sort_dicts(items, "total_amount", descending=True)

    # ──────────────────────────────────────────────────────────────────────
    # 5. Order Value Analysis + CLV explanation
    # ──────────────────────────────────────────────────────────────────────

    def order_value_analysis(self, n: int = 10) -> dict:
        """
        Calculate total value per Order ID and identify top N orders.

        Customer Lifetime Value (CLV) — why it cannot be calculated
        -------------------------------------------------------------
        CLV requires a unique *customer* identifier to group all purchases
        made by the same person across time.  This dataset contains only an
        Order ID, which identifies a transaction, not a customer.

        Without a "Customer ID" (or equivalent) column, we cannot:
        * Link multiple orders to the same buyer.
        * Calculate how much a customer has spent in total (CLV).
        * Measure customer retention or repeat-purchase rate.

        What we CAN do is sum revenue per Order ID, which gives order value —
        a transaction-level metric, not a customer-level one.

        Returns
        -------
        dict:
          {
            "top_orders": list of {"order_id": str, "total_value": float},
            "clv_note": str    -- the CLV limitation explanation
          }
        """
        totals = {}

        for order in self._om.get_all_orders():
            oid = order.order_id
            totals[oid] = totals.get(oid, 0.0) + order.amount

        items = [{"order_id": k, "total_value": v} for k, v in totals.items()]
        sorted_items = self._quick_sort_dicts(items, "total_value", descending=True)

        clv_note = (
            "TRUE CLV CANNOT BE CALCULATED: This dataset has no customer "
            "identifier column (e.g., 'Customer ID'). Order ID identifies a "
            "transaction, not a person. To calculate CLV we would need a field "
            "that uniquely identifies each buyer across multiple orders."
        )

        return {
            "top_orders": sorted_items[:n],
            "clv_note":   clv_note,
        }

    # ──────────────────────────────────────────────────────────────────────
    # 6. Cancellation Analysis (Stockout Proxy)
    # ──────────────────────────────────────────────────────────────────────

    def cancellation_analysis(self) -> dict:
        """
        Analyse cancelled orders and use them as a stockout proxy.

        Methodology
        -----------
        1. Identify all orders with Status == "Cancelled".
        2. Count cancellations per SKU and per Category.
        3. Rank SKUs and Categories by cancellation count.

        Why cancellations are used as a stockout proxy
        ------------------------------------------------
        When a product consistently has high cancellation rates, one
        possible reason is that the item was out of stock at the time
        of ordering, leading to automatic or manual cancellation.

        However, cancellations do NOT prove stockouts because:
        * Customers may cancel for personal reasons (changed mind, found
          cheaper alternative).
        * Merchants may cancel due to logistics issues unrelated to stock.
        * Pricing errors or fraud prevention may trigger cancellations.
        * The dataset has no "cancellation reason" column to distinguish causes.

        Assumption: We flag SKUs where cancellation rate > 50% of their
        total orders as "high-risk" stockout candidates.

        Returns
        -------
        dict with cancellation counts, top cancelled SKUs/categories,
        and stockout assumption note.
        """
        from algorithms import linear_search_by_status

        cancelled = linear_search_by_status(self._om.get_all_orders(), "Cancelled")

        # Count by SKU
        sku_counts = {}
        cat_counts = {}

        for order in cancelled:
            sku = order.sku or "Unknown"
            cat = order.category or "Unknown"
            sku_counts[sku] = sku_counts.get(sku, 0) + 1
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

        # Sort by count descending
        top_skus = self._quick_sort_dicts(
            [{"sku": k, "cancellations": v} for k, v in sku_counts.items()],
            "cancellations", descending=True
        )[:10]

        top_cats = self._quick_sort_dicts(
            [{"category": k, "cancellations": v} for k, v in cat_counts.items()],
            "cancellations", descending=True
        )

        # Compute cancellation rate per SKU
        # (total orders per SKU from indexes)
        sku_index = self._om.get_index_by_sku()
        risk_skus = []
        for entry in top_skus:
            sku = entry["sku"]
            total = len(sku_index.get(sku, []))
            rate = (entry["cancellations"] / total * 100) if total > 0 else 0
            if rate > 50:
                risk_skus.append({"sku": sku, "cancellation_rate_%": round(rate, 1),
                                   "cancelled": entry["cancellations"], "total": total})

        note = (
            "ASSUMPTION: Cancellations used as a possible stockout indicator. "
            "High cancellation rates (>50%) may suggest inventory shortages, "
            "but can also result from customer choice, logistics issues, or "
            "pricing errors. No cancellation reason field exists in the dataset."
        )

        return {
            "total_cancelled":     len(cancelled),
            "top_cancelled_skus":  top_skus,
            "top_cancelled_cats":  top_cats,
            "high_risk_stockout_skus": risk_skus,
            "assumption_note":     note,
        }

    # ──────────────────────────────────────────────────────────────────────
    # 7. Seasonal Purchasing Patterns
    # ──────────────────────────────────────────────────────────────────────

    def seasonal_patterns(self) -> dict:
        """
        Analyse orders across months and quarters.

        Month numbering: 1=Jan, 2=Feb, ..., 12=Dec
        Quarter mapping: Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec

        Only orders with a valid parsed date are included.

        Returns
        -------
        dict:
          {
            "monthly":    { "MM-YYYY": {"total_amount": float, "order_count": int} },
            "quarterly":  { "QN-YYYY": {"total_amount": float, "order_count": int} },
            "by_category_month": { category: { month_key: total_amount } }
          }
        """
        monthly   = {}
        quarterly = {}
        cat_month = {}

        QUARTER_MAP = {1: "Q1", 2: "Q1", 3: "Q1",
                       4: "Q2", 5: "Q2", 6: "Q2",
                       7: "Q3", 8: "Q3", 9: "Q3",
                       10:"Q4", 11:"Q4", 12:"Q4"}

        for order in self._om.get_all_orders():
            if order.date is None:
                continue

            m    = order.date.month
            y    = order.date.year
            mkey = f"{m:02d}-{y}"
            qkey = f"{QUARTER_MAP[m]}-{y}"

            # Monthly aggregation
            if mkey not in monthly:
                monthly[mkey] = {"total_amount": 0.0, "order_count": 0}
            monthly[mkey]["total_amount"] += order.amount
            monthly[mkey]["order_count"]  += 1

            # Quarterly aggregation
            if qkey not in quarterly:
                quarterly[qkey] = {"total_amount": 0.0, "order_count": 0}
            quarterly[qkey]["total_amount"] += order.amount
            quarterly[qkey]["order_count"]  += 1

            # By category and month
            cat = order.category or "Unknown"
            if cat not in cat_month:
                cat_month[cat] = {}
            cat_month[cat][mkey] = cat_month[cat].get(mkey, 0.0) + order.amount

        return {
            "monthly":             monthly,
            "quarterly":           quarterly,
            "by_category_month":   cat_month,
        }

    # ──────────────────────────────────────────────────────────────────────
    # 8. Inventory Turnover Ratio (Simplified)
    # ──────────────────────────────────────────────────────────────────────

    def inventory_turnover(self) -> dict:
        """
        Calculate a simplified Inventory Turnover Ratio per SKU.

        Formula used
        ------------
        Turnover Ratio = Total Qty Sold / Average Inventory Level

        Since actual stock levels are unavailable, we use:
            Average Inventory Level ≈ Peak Monthly Qty Sold per SKU

        This proxy assumes the peak month represents a "fully stocked"
        period.  Higher turnover → product sells through its stock quickly.

        Limitations
        -----------
        * Actual beginning/ending inventory data is unavailable.
        * Peak monthly Qty is a rough proxy and may overestimate turnover
          for products with highly seasonal demand spikes.
        * Result should be interpreted as a relative ranking of SKUs, not
          an absolute inventory turnover measurement.

        Returns
        -------
        dict:
          {
            "turnover_by_sku": list of {"sku", "total_qty", "peak_monthly_qty",
                                        "turnover_ratio"},
            "limitation_note": str
          }
        """
        # Step 1: build monthly qty per SKU
        sku_monthly = {}   # { sku: { month_key: qty } }

        for order in self._om.get_all_orders():
            if order.date is None:
                continue
            sku  = order.sku or "Unknown"
            mkey = f"{order.date.month:02d}-{order.date.year}"

            if sku not in sku_monthly:
                sku_monthly[sku] = {}
            sku_monthly[sku][mkey] = sku_monthly[sku].get(mkey, 0) + order.qty

        # Step 2: calculate total qty and peak monthly qty per SKU
        results = []
        for sku, month_data in sku_monthly.items():
            total_qty    = sum(month_data.values())
            peak_monthly = max(month_data.values()) if month_data else 1

            # Avoid division by zero
            turnover = total_qty / peak_monthly if peak_monthly > 0 else 0.0

            results.append({
                "sku":              sku,
                "total_qty":        total_qty,
                "peak_monthly_qty": peak_monthly,
                "turnover_ratio":   round(turnover, 2),
            })

        # Sort by turnover ratio descending
        results = self._quick_sort_dicts(results, "turnover_ratio", descending=True)

        note = (
            "LIMITATION: Actual inventory stock levels are not in this dataset. "
            "Turnover ratio here uses peak monthly Qty sold as a proxy for "
            "average inventory. This is an approximation and should not be "
            "used for financial reporting."
        )

        return {"turnover_by_sku": results[:20], "limitation_note": note}

    # ──────────────────────────────────────────────────────────────────────
    # 9. Promotion Analysis
    # ──────────────────────────────────────────────────────────────────────

    def promotion_analysis(self) -> list:
        """
        Analyse promotion-ids to find the most widely used promotions.

        Each order can have multiple promotion IDs (comma-separated inside
        the quoted field — already parsed to a list in the Order object).

        For each promotion ID, we report:
          - Total number of orders it appears in.
          - Total sales amount across those orders.
          - Most affected categories (top 3).

        Returns
        -------
        list of dict sorted by order_count descending:
          [{"promotion_id": str, "order_count": int, "total_amount": float,
            "top_categories": list[str]}, ...]
        """
        promo_data = {}
        # { promo_id: {"order_count": int, "total_amount": float,
        #               "category_counts": {cat: int}} }

        for order in self._om.get_all_orders():
            for promo in order.promotion_ids:
                if promo not in promo_data:
                    promo_data[promo] = {
                        "order_count":    0,
                        "total_amount":   0.0,
                        "category_counts": {}
                    }
                promo_data[promo]["order_count"]  += 1
                promo_data[promo]["total_amount"] += order.amount

                cat = order.category or "Unknown"
                promo_data[promo]["category_counts"][cat] = \
                    promo_data[promo]["category_counts"].get(cat, 0) + 1

        # Build result list
        results = []
        for pid, data in promo_data.items():
            # Find top 3 categories for this promotion
            cat_items = [
                {"cat": k, "count": v}
                for k, v in data["category_counts"].items()
            ]
            cat_sorted = self._quick_sort_dicts(cat_items, "count", descending=True)
            top_cats = [item["cat"] for item in cat_sorted[:3]]

            results.append({
                "promotion_id":  pid,
                "order_count":   data["order_count"],
                "total_amount":  round(data["total_amount"], 2),
                "top_categories": top_cats,
            })

        return self._quick_sort_dicts(results, "order_count", descending=True)

    # ──────────────────────────────────────────────────────────────────────
    # Utility — algorithm selection explanations (for CLI display)
    # ──────────────────────────────────────────────────────────────────────

    def algorithm_recommendation(self) -> dict:
        """
        Return a dict of explanations for algorithm selection questions
        from the assignment.
        """
        return {
            "search_by_ship_state": (
                "Best method: Linear Search (O(n)).\n"
                "Reason: ship-state is not indexed and can have many unique values "
                "(unlike Order ID). A hash index on state could be built, but linear "
                "scan is acceptable for occasional queries. Binary search is not "
                "suitable because the data is not sorted by state."
            ),
            "top5_by_qty": (
                "Best algorithm: Heap Sort / Min-Heap (O(n log 5) = O(n)).\n"
                "Reason: We only need 5 items from n records. A min-heap of size 5 "
                "processes all n records in O(n log 5) time and O(5) space — far more "
                "efficient than sorting all n records (O(n log n))."
            ),
            "binary_and_hash_combined": (
                "Combined approach for order retrieval:\n"
                "  1. Hash lookup on Order ID → O(1) avg, retrieves matching orders.\n"
                "  2. If Order ID is not found in the hash index (cache miss), fall back "
                "to binary search on the sorted list → O(log n).\n"
                "  3. Update the hash index after retrieval for future O(1) lookups.\n"
                "This hybrid minimises both space (hash needs only frequently accessed "
                "keys) and time (binary search as a reliable fallback)."
            ),
        }

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _quick_sort_dicts(items: list, key: str, descending: bool = False) -> list:
        """
        Quick Sort on a list of dicts using a string key.

        This is a standalone implementation so analytics functions don't
        need to convert dicts to Order objects to use the algorithms module.

        Time complexity : O(n log n) average.
        """
        if len(items) <= 1:
            return items

        pivot_val = items[len(items) // 2][key]
        left   = [x for x in items if x[key] <  pivot_val]
        centre = [x for x in items if x[key] == pivot_val]
        right  = [x for x in items if x[key] >  pivot_val]

        sorted_asc = (
            Analytics._quick_sort_dicts(left,  key, descending) + centre +
            Analytics._quick_sort_dicts(right, key, descending)
        )
        return list(reversed(sorted_asc)) if descending else sorted_asc
