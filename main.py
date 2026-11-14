"""
main.py
=======
Entry point for the Integrated Inventory and Analytics System.

Provides a full Command-Line Interface with:
  - Login / Logout
  - Manager Dashboard (full access)
  - Junior Manager Dashboard (read-only analytics + limited search/sort)
  - Input validation and error handling throughout

Run with:
    python3 main.py
"""

import os
import sys

from order_manager  import OrderManager
from user_manager   import UserManager, ROLE_MANAGER, ROLE_JUNIOR_MANAGER
from analytics      import Analytics
from visualisation  import Visualisation
from algorithms     import (
    linear_search_by_status,
    linear_search_by_field,
    binary_search_by_order_id,
    hash_lookup_sku,
    hash_lookup_city,
    quick_sort_by_amount,
    quick_sort_by_qty,
    merge_sort_by_date,
    prepare_sorted_for_binary_search,
    heap_top_n,
)

# ── ANSI colour helpers (work in macOS Terminal / iTerm) ──────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
MAGENTA= "\033[95m"
WHITE  = "\033[97m"
DIM    = "\033[2m"


def colour(text, code):
    return f"{code}{text}{RESET}"


# ══════════════════════════════════════════════════════════════════════════════
# ── CLI class ─────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

class CLI:
    """
    Main CLI controller.

    Attributes
    ----------
    om   : OrderManager  — order data store
    um   : UserManager   — authentication / RBAC
    anal : Analytics     — analytical engine
    vis  : Visualisation — chart generator
    _sorted_for_binary : list | None — cached sorted list for binary search
    """

    def __init__(self):
        self.om   = OrderManager()
        self.um   = UserManager()
        self.anal = None   # created after orders are loaded
        self.vis  = None
        self._sorted_for_binary = None

    # ──────────────────────────────────────────────────────────────────────
    # Startup
    # ──────────────────────────────────────────────────────────────────────

    def run(self):
        """Main entry point — load data then enter the login loop."""
        self._clear()
        self._print_banner()
        self._load_data()
        self.anal = Analytics(self.om)
        self.vis  = Visualisation(self.anal)
        self._login_menu()

    def _load_data(self):
        """Load the CSV dataset."""
        path = os.path.join("data", "amazon_sales.csv")
        print(colour(f"\n  Loading dataset from: {path}", DIM))
        self.om.load_csv(path)
        skipped = self.om.get_skipped_rows()
        print(colour(f"  ✔  {self.om.order_count():,} orders loaded.", GREEN))
        if skipped:
            print(colour(f"  ⚠  {len(skipped):,} rows skipped (malformed/incomplete).", YELLOW))
        print()

    # ──────────────────────────────────────────────────────────────────────
    # Login menu
    # ──────────────────────────────────────────────────────────────────────

    def _login_menu(self):
        while True:
            self._print_header("MAIN MENU")
            print(f"  {colour('1.', CYAN)} Login")
            print(f"  {colour('2.', CYAN)} Exit")
            print()
            choice = self._input("Enter choice").strip()

            if choice == "1":
                self._do_login()
            elif choice == "2":
                self._exit()
            else:
                self._error("Invalid choice. Enter 1 or 2.")

    def _do_login(self):
        print()
        username = self._input("Username").strip()
        password = self._input_password("Password")

        user = self.um.login(username, password)
        if user is None:
            self._error("Invalid credentials. Please try again.")
            return

        print(colour(f"\n  ✔  Welcome, {user.username}! Role: {user.role}", GREEN))
        self._pause()

        if user.role == ROLE_MANAGER:
            self._manager_dashboard()
        elif user.role == ROLE_JUNIOR_MANAGER:
            self._junior_dashboard()
        else:
            self._error(f"Unknown role: {user.role}")
            self.um.logout()

    # ──────────────────────────────────────────────────────────────────────
    # Manager Dashboard
    # ──────────────────────────────────────────────────────────────────────

    def _manager_dashboard(self):
        while True:
            self._clear()
            user = self.um.get_current_user()
            self._print_header(f"MANAGER DASHBOARD  |  {user.username}")
            opts = [
                ("1",  "View All Orders"),
                ("2",  "Add New Order"),
                ("3",  "Edit Order"),
                ("4",  "Delete Order"),
                ("5",  "Search Orders"),
                ("6",  "Sort Orders"),
                ("7",  "Sales Analytics"),
                ("8",  "Inventory Analysis"),
                ("9",  "Promotion Analysis"),
                ("10", "View / Generate Charts"),
                ("11", "View Skipped Rows"),
                ("12", "Logout"),
            ]
            self._print_menu(opts)
            choice = self._input("Enter choice").strip()

            actions = {
                "1":  self._view_all_orders,
                "2":  self._add_order,
                "3":  self._edit_order,
                "4":  self._delete_order,
                "5":  self._search_menu,
                "6":  self._sort_menu,
                "7":  self._analytics_menu,
                "8":  self._inventory_menu,
                "9":  self._promotion_menu,
                "10": self._charts_menu,
                "11": self._view_skipped,
                "12": self._logout,
            }

            if choice in actions:
                actions[choice]()
                if choice == "12":
                    break
            else:
                self._error("Invalid choice.")

    # ──────────────────────────────────────────────────────────────────────
    # Junior Manager Dashboard
    # ──────────────────────────────────────────────────────────────────────

    def _junior_dashboard(self):
        while True:
            self._clear()
            user = self.um.get_current_user()
            self._print_header(f"JUNIOR MANAGER DASHBOARD  |  {user.username}")
            opts = [
                ("1",  "Search Orders"),
                ("2",  "Sort Orders"),
                ("3",  "Sales Analytics"),
                ("4",  "Inventory Analysis"),
                ("5",  "Promotion Analysis"),
                ("6",  "View All Orders (first 50)"),
                ("7",  "Logout"),
            ]
            self._print_menu(opts)
            choice = self._input("Enter choice").strip()

            actions = {
                "1": self._search_menu,
                "2": self._junior_sort_menu,
                "3": self._analytics_menu,
                "4": self._inventory_menu,
                "5": self._promotion_menu,
                "6": self._view_all_orders,
                "7": self._logout,
            }

            if choice in actions:
                actions[choice]()
                if choice == "7":
                    break
            else:
                self._error("Invalid choice.")

    # ──────────────────────────────────────────────────────────────────────
    # CRUD — View
    # ──────────────────────────────────────────────────────────────────────

    def _view_all_orders(self):
        self._clear()
        self._print_header("ALL ORDERS  (first 50)")
        orders = self.om.view_all_orders(limit=50)
        if not orders:
            print(colour("  No orders found.", YELLOW))
        else:
            for o in orders:
                print(o)
        print(colour(f"\n  Total orders in system: {self.om.order_count():,}", CYAN))
        self._pause()

    # ──────────────────────────────────────────────────────────────────────
    # CRUD — Add
    # ──────────────────────────────────────────────────────────────────────

    def _add_order(self):
        try:
            self.um.require_role("add_order")
        except PermissionError as e:
            self._error(str(e))
            return

        self._clear()
        self._print_header("ADD NEW ORDER")
        print(colour("  Fill in the following fields (press Enter to leave optional fields blank):\n", DIM))

        try:
            order_id      = self._input_required("Order ID")
            date          = self._input_required("Date (MM-DD-YY)")
            status        = self._input_required("Status")
            fulfilment    = self._input("Fulfilment")
            sales_channel = self._input("Sales Channel")
            ship_service  = self._input("Ship Service Level")
            style         = self._input("Style")
            sku           = self._input("SKU")
            category      = self._input("Category")
            size          = self._input("Size")
            asin          = self._input("ASIN")
            courier_status= self._input("Courier Status")
            qty_str       = self._input("Quantity")
            currency      = self._input("Currency (default INR)") or "INR"
            amount_str    = self._input("Amount")
            ship_city     = self._input("Ship City")
            ship_state    = self._input("Ship State")
            ship_postal   = self._input("Ship Postal Code")
            ship_country  = self._input("Ship Country (default IN)") or "IN"
            promotion_ids = self._input("Promotion IDs (comma-separated, or leave blank)")
            b2b_str       = self._input("B2B? (true/false)")
            fulfilled_by  = self._input("Fulfilled By")

            qty    = int(float(qty_str))    if qty_str    else 0
            amount = float(amount_str)      if amount_str else 0.0

        except (ValueError, KeyboardInterrupt):
            self._error("Invalid input. Order not added.")
            return

        new_order = self.om.add_order(
            order_id=order_id, date=date, status=status,
            fulfilment=fulfilment, sales_channel=sales_channel,
            ship_service=ship_service, style=style, sku=sku,
            category=category, size=size, asin=asin,
            courier_status=courier_status, qty=qty, currency=currency,
            amount=amount, ship_city=ship_city, ship_state=ship_state,
            ship_postal=ship_postal, ship_country=ship_country,
            promotion_ids=promotion_ids, b2b=b2b_str,
            fulfilled_by=fulfilled_by,
        )
        print(colour(f"\n  ✔  Order added successfully!", GREEN))
        print(new_order)
        self._sorted_for_binary = None   # invalidate binary search cache
        self._pause()

    # ──────────────────────────────────────────────────────────────────────
    # CRUD — Edit
    # ──────────────────────────────────────────────────────────────────────

    def _edit_order(self):
        try:
            self.um.require_role("edit_order")
        except PermissionError as e:
            self._error(str(e))
            return

        self._clear()
        self._print_header("EDIT ORDER")
        order_id = self._input_required("Enter Order ID to edit")

        existing = self.om.get_by_order_id(order_id)
        if not existing:
            self._error(f"No orders found with ID '{order_id}'.")
            self._pause()
            return

        print(colour(f"\n  Found {len(existing)} order(s):\n", CYAN))
        for o in existing:
            print(o)

        print(colour("\n  Editable fields: status, courier_status, qty, amount", DIM))
        print(colour("  Leave a field blank to skip it.\n", DIM))

        kwargs = {}
        status = self._input("New Status")
        if status:
            kwargs["status"] = status

        c_status = self._input("New Courier Status")
        if c_status:
            kwargs["courier_status"] = c_status

        qty_str = self._input("New Qty")
        if qty_str:
            try:
                kwargs["qty"] = int(float(qty_str))
            except ValueError:
                self._error(f"Invalid qty: {qty_str!r}. Skipping.")

        amt_str = self._input("New Amount")
        if amt_str:
            try:
                kwargs["amount"] = float(amt_str)
            except ValueError:
                self._error(f"Invalid amount: {amt_str!r}. Skipping.")

        if not kwargs:
            print(colour("  No changes made.", YELLOW))
        else:
            success = self.om.edit_order(order_id, **kwargs)
            if success:
                print(colour(f"\n  ✔  Order(s) updated.", GREEN))
                for o in self.om.get_by_order_id(order_id):
                    print(o)
            else:
                self._error("Update failed.")

        self._sorted_for_binary = None   # invalidate cache
        self._pause()

    # ──────────────────────────────────────────────────────────────────────
    # CRUD — Delete
    # ──────────────────────────────────────────────────────────────────────

    def _delete_order(self):
        try:
            self.um.require_role("delete_order")
        except PermissionError as e:
            self._error(str(e))
            return

        self._clear()
        self._print_header("DELETE ORDER")
        order_id = self._input_required("Enter Order ID to delete")

        existing = self.om.get_by_order_id(order_id)
        if not existing:
            self._error(f"No orders found with ID '{order_id}'.")
            self._pause()
            return

        print(colour(f"\n  Found {len(existing)} order(s) with ID '{order_id}':", YELLOW))
        for o in existing:
            print(o)

        confirm = self._input(colour(f"\n  Permanently delete {len(existing)} order(s)? (yes/no)", RED))
        if confirm.strip().lower() == "yes":
            count = self.om.delete_order(order_id)
            print(colour(f"\n  ✔  Deleted {count} order(s).", GREEN))
            self._sorted_for_binary = None
        else:
            print(colour("  Deletion cancelled.", YELLOW))

        self._pause()

    # ──────────────────────────────────────────────────────────────────────
    # Search Menu
    # ──────────────────────────────────────────────────────────────────────

    def _search_menu(self):
        while True:
            self._clear()
            self._print_header("SEARCH ORDERS")
            user = self.um.get_current_user()
            is_manager = (user.role == ROLE_MANAGER)

            opts = [
                ("1", "Search by Order ID       (Hash Lookup — O(1))"),
                ("2", "Search by Status         (Linear Search — O(n))"),
                ("3", "Search by Category       (Linear Search — O(n))"),
                ("4", "Search by Ship City      (Hash Lookup — O(1))"),
                ("5", "Search by SKU            (Hash Lookup — O(1))"),
                ("6", "Binary Search by Order ID (requires sorting first)"),
            ]
            if is_manager:
                opts.append(("7", "Search by Ship State  (Linear Search — O(n))"))
            opts.append(("0", "Back"))

            self._print_menu(opts)
            choice = self._input("Enter choice").strip()

            if choice == "0":
                break
            elif choice == "1":
                self._search_by_order_id_hash()
            elif choice == "2":
                self._search_by_status()
            elif choice == "3":
                self._search_by_field("category", "Category")
            elif choice == "4":
                self._search_by_city_hash()
            elif choice == "5":
                self._search_by_sku_hash()
            elif choice == "6":
                self._binary_search_menu()
            elif choice == "7" and is_manager:
                self._search_by_field("ship_state", "Ship State")
            else:
                self._error("Invalid choice.")

    def _search_by_order_id_hash(self):
        self._clear()
        self._print_header("HASH LOOKUP — Order ID")
        self._show_algo_note("Hash Index", "O(1) average", "Direct dictionary lookup by Order ID key.")
        order_id = self._input_required("Enter Order ID")
        results  = self.om.get_by_order_id(order_id)
        self._display_search_results(results, f"Order ID = '{order_id}'")

    def _search_by_status(self):
        self._clear()
        self._print_header("LINEAR SEARCH — Status")
        self._show_algo_note("Linear Search", "O(n)",
                             "Every order is checked. Best for unindexed, non-unique fields.")
        status  = self._input_required("Enter Status (e.g. Cancelled, Shipped)")
        results = linear_search_by_status(self.om.get_all_orders(), status)
        self._display_search_results(results, f"Status = '{status}'")

    def _search_by_field(self, attr: str, label: str):
        self._clear()
        self._print_header(f"LINEAR SEARCH — {label}")
        self._show_algo_note("Linear Search", "O(n)", f"Scanning all orders for matching {label}.")
        value   = self._input_required(f"Enter {label}")
        results = linear_search_by_field(self.om.get_all_orders(), attr, value)
        self._display_search_results(results, f"{label} = '{value}'")

    def _search_by_city_hash(self):
        self._clear()
        self._print_header("HASH LOOKUP — Ship City")
        self._show_algo_note("Hash Index", "O(1) average", "City hash index built at startup.")
        city    = self._input_required("Enter City (e.g. MUMBAI, DELHI)")
        results = hash_lookup_city(self.om.get_index_by_city(), city)
        self._display_search_results(results, f"Ship City = '{city.upper()}'")

    def _search_by_sku_hash(self):
        self._clear()
        self._print_header("HASH LOOKUP — SKU")
        self._show_algo_note("Hash Index", "O(1) average", "SKU hash index built at startup.")
        sku     = self._input_required("Enter SKU")
        results = hash_lookup_sku(self.om.get_index_by_sku(), sku)
        self._display_search_results(results, f"SKU = '{sku}'")

    def _binary_search_menu(self):
        self._clear()
        self._print_header("BINARY SEARCH — Order ID")
        self._show_algo_note("Binary Search", "O(log n)",
                             "List must be sorted by Order ID first. Halves search space each step.")

        if self._sorted_for_binary is None:
            print(colour("  Sorting orders by Order ID for binary search (one-time setup)...", DIM))
            self._sorted_for_binary = prepare_sorted_for_binary_search(
                self.om.get_all_orders()
            )
            print(colour(f"  ✔  {len(self._sorted_for_binary):,} orders sorted.", GREEN))

        order_id = self._input_required("Enter Order ID to find")
        results  = binary_search_by_order_id(self._sorted_for_binary, order_id)
        self._display_search_results(results, f"Order ID = '{order_id}' (Binary Search)")

    def _display_search_results(self, results: list, description: str):
        print()
        if not results:
            print(colour(f"  No results found for: {description}", YELLOW))
        else:
            print(colour(f"  Found {len(results):,} result(s) for: {description}\n", GREEN))
            # Show at most 20 results to avoid flooding the terminal
            for o in results[:20]:
                print(o)
            if len(results) > 20:
                print(colour(f"  ... and {len(results)-20:,} more.", DIM))
        self._pause()

    # ──────────────────────────────────────────────────────────────────────
    # Sort Menus
    # ──────────────────────────────────────────────────────────────────────

    def _sort_menu(self):
        """Full sort menu for managers."""
        while True:
            self._clear()
            self._print_header("SORT ORDERS")
            opts = [
                ("1", "Sort by Amount  — Descending (Quick Sort)"),
                ("2", "Sort by Qty     — Descending (Quick Sort)"),
                ("3", "Sort by Date    — Ascending  (Merge Sort, stable)"),
                ("4", "Sort by Date then Order ID   (Stable Multi-key Merge Sort)"),
                ("0", "Back"),
            ]
            self._print_menu(opts)
            choice = self._input("Enter choice").strip()

            if choice == "0":
                break
            elif choice == "1":
                self._run_sort("Amount ↓ (Quick Sort)", lambda:
                    list(reversed(quick_sort_by_amount(self.om.get_all_orders()))))
            elif choice == "2":
                self._run_sort("Qty ↓ (Quick Sort)", lambda:
                    list(reversed(quick_sort_by_qty(self.om.get_all_orders()))))
            elif choice == "3":
                self._run_sort("Date ↑ (Merge Sort)", lambda:
                    merge_sort_by_date(self.om.get_all_orders()))
            elif choice == "4":
                from algorithms import merge_sort_by_date_then_id
                self._run_sort("Date ↑ then Order ID ↑ (Stable Multi-key)", lambda:
                    merge_sort_by_date_then_id(self.om.get_all_orders()))
            else:
                self._error("Invalid choice.")

    def _junior_sort_menu(self):
        """Restricted sort menu for junior managers."""
        while True:
            self._clear()
            self._print_header("SORT ORDERS")
            opts = [
                ("1", "Sort by Date   — Ascending  (Merge Sort)"),
                ("2", "Sort by Amount — Descending (Quick Sort)"),
                ("3", "Sort by Qty    — Descending (Quick Sort)"),
                ("0", "Back"),
            ]
            self._print_menu(opts)
            choice = self._input("Enter choice").strip()

            if choice == "0":
                break
            elif choice == "1":
                self._run_sort("Date ↑ (Merge Sort)", lambda:
                    merge_sort_by_date(self.om.get_all_orders()))
            elif choice == "2":
                self._run_sort("Amount ↓ (Quick Sort)", lambda:
                    list(reversed(quick_sort_by_amount(self.om.get_all_orders()))))
            elif choice == "3":
                self._run_sort("Qty ↓ (Quick Sort)", lambda:
                    list(reversed(quick_sort_by_qty(self.om.get_all_orders()))))
            else:
                self._error("Invalid choice.")

    def _run_sort(self, label: str, sort_fn):
        self._clear()
        self._print_header(f"SORTED: {label}")
        print(colour("  Sorting... (this may take a moment for large datasets)", DIM))
        try:
            sorted_orders = sort_fn()
            print(colour(f"\n  ✔  Sorted {len(sorted_orders):,} orders by {label}\n", GREEN))
            # Display first 30
            for o in sorted_orders[:30]:
                print(o)
            if len(sorted_orders) > 30:
                print(colour(f"\n  ... and {len(sorted_orders)-30:,} more orders.", DIM))
        except Exception as e:
            self._error(f"Sort failed: {e}")
        self._pause()

    # ──────────────────────────────────────────────────────────────────────
    # Analytics Menu
    # ──────────────────────────────────────────────────────────────────────

    def _analytics_menu(self):
        while True:
            self._clear()
            self._print_header("SALES ANALYTICS")
            opts = [
                ("1",  "Top N Products by Revenue"),
                ("2",  "Top N Products by Quantity"),
                ("3",  "Sales by City"),
                ("4",  "Sales by State"),
                ("5",  "Order Status Distribution"),
                ("6",  "Category Performance"),
                ("7",  "Top N Orders by Value  (+ CLV explanation)"),
                ("8",  "Seasonal Sales Patterns"),
                ("9",  "Algorithm Recommendations"),
                ("0",  "Back"),
            ]
            self._print_menu(opts)
            choice = self._input("Enter choice").strip()

            if choice == "0":
                break
            elif choice == "1":
                self._show_top_n_amount()
            elif choice == "2":
                self._show_top_n_qty()
            elif choice == "3":
                self._show_sales_by_city()
            elif choice == "4":
                self._show_sales_by_state()
            elif choice == "5":
                self._show_status_distribution()
            elif choice == "6":
                self._show_category_performance()
            elif choice == "7":
                self._show_order_value_analysis()
            elif choice == "8":
                self._show_seasonal_patterns()
            elif choice == "9":
                self._show_algo_recommendations()
            else:
                self._error("Invalid choice.")

    def _show_top_n_amount(self):
        self._clear()
        self._print_header("TOP N PRODUCTS — By Revenue")
        n = self._input_int("Enter N (e.g. 10)", default=10)
        results = self.anal.top_n_by_amount(n)
        print(colour(f"\n  Top {n} SKUs by Total Sales Amount:\n", CYAN))
        for i, r in enumerate(results, 1):
            print(f"  {i:>3}. {r['sku']:<35}  ₹{r['total_amount']:>14,.2f}")
        self._pause()

    def _show_top_n_qty(self):
        self._clear()
        self._print_header("TOP N PRODUCTS — By Quantity")
        n = self._input_int("Enter N (e.g. 10)", default=10)
        results = self.anal.top_n_by_qty(n)
        print(colour(f"\n  Top {n} SKUs by Total Quantity Sold:\n", CYAN))
        for i, r in enumerate(results, 1):
            print(f"  {i:>3}. {r['sku']:<35}  {r['total_qty']:>10,} units")
        self._pause()

    def _show_sales_by_city(self):
        self._clear()
        self._print_header("SALES BY CITY")
        city = self._input_required("Enter city name (e.g. MUMBAI)")
        result = self.anal.sales_by_city(city)
        print(colour(f"\n  Results for city: {result['city']}\n", CYAN))
        print(f"  Total Sales Amount : ₹{result['total_amount']:,.2f}")
        print(f"  Number of Orders   : {result['order_count']:,}")
        self._pause()

    def _show_sales_by_state(self):
        self._clear()
        self._print_header("SALES BY STATE")
        state = self._input_required("Enter state name (e.g. MAHARASHTRA)")
        result = self.anal.sales_by_state(state)
        print(colour(f"\n  Results for state: {result['state']}\n", CYAN))
        print(f"  Total Sales Amount : ₹{result['total_amount']:,.2f}")
        print(f"  Number of Orders   : {result['order_count']:,}")
        self._pause()

    def _show_status_distribution(self):
        self._clear()
        self._print_header("ORDER STATUS DISTRIBUTION")
        dist = self.anal.order_status_distribution()
        total = sum(dist.values())
        print(colour(f"\n  Total Orders: {total:,}\n", CYAN))
        # Sort by count descending
        for status, count in sorted(dist.items(), key=lambda x: x[1], reverse=True):
            pct = count / total * 100 if total > 0 else 0
            bar = "█" * int(pct / 2)
            print(f"  {status:<40} {count:>8,}  ({pct:5.1f}%)  {colour(bar, CYAN)}")
        self._pause()

    def _show_category_performance(self):
        self._clear()
        self._print_header("CATEGORY PERFORMANCE")
        results = self.anal.category_performance()
        print(colour(f"\n  {'Category':<30}  {'Total Amount':>18}  {'Total Qty':>12}\n", CYAN))
        for r in results:
            print(f"  {r['category']:<30}  ₹{r['total_amount']:>16,.2f}  {r['total_qty']:>12,}")
        self._pause()

    def _show_order_value_analysis(self):
        self._clear()
        self._print_header("ORDER VALUE ANALYSIS")
        n = self._input_int("Show top N orders by value", default=10)
        result = self.anal.order_value_analysis(n)

        print(colour(f"\n  Top {n} Orders by Total Value:\n", CYAN))
        for i, r in enumerate(result["top_orders"], 1):
            print(f"  {i:>3}. {r['order_id']:<35}  ₹{r['total_value']:>14,.2f}")

        print(colour("\n  ─── Customer Lifetime Value (CLV) Note ───\n", YELLOW))
        print(colour("  " + result["clv_note"], DIM))
        self._pause()

    def _show_seasonal_patterns(self):
        self._clear()
        self._print_header("SEASONAL SALES PATTERNS")
        data = self.anal.seasonal_patterns()

        print(colour("\n  Monthly Sales:\n", CYAN))
        monthly = data["monthly"]
        def month_key(k):
            p = k.split("-"); return (int(p[1]), int(p[0]))
        for mk in sorted(monthly.keys(), key=month_key):
            m = monthly[mk]
            print(f"  {mk}   ₹{m['total_amount']:>14,.2f}   Orders: {m['order_count']:>6,}")

        print(colour("\n  Quarterly Sales:\n", CYAN))
        for qk, qv in sorted(data["quarterly"].items()):
            print(f"  {qk}   ₹{qv['total_amount']:>14,.2f}   Orders: {qv['order_count']:>6,}")

        self._pause()

    def _show_algo_recommendations(self):
        self._clear()
        self._print_header("ALGORITHM RECOMMENDATIONS")
        recs = self.anal.algorithm_recommendation()
        for title, explanation in recs.items():
            print(colour(f"\n  ■ {title.replace('_', ' ').title()}", YELLOW))
            for line in explanation.split("\n"):
                print(f"    {line}")
        self._pause()

    # ──────────────────────────────────────────────────────────────────────
    # Inventory Menu
    # ──────────────────────────────────────────────────────────────────────

    def _inventory_menu(self):
        while True:
            self._clear()
            self._print_header("INVENTORY ANALYSIS")
            opts = [
                ("1", "Cancellation Analysis  (Stockout Proxy)"),
                ("2", "Inventory Turnover Ratio  (Simplified)"),
                ("0", "Back"),
            ]
            self._print_menu(opts)
            choice = self._input("Enter choice").strip()

            if choice == "0":
                break
            elif choice == "1":
                self._show_cancellation_analysis()
            elif choice == "2":
                self._show_inventory_turnover()
            else:
                self._error("Invalid choice.")

    def _show_cancellation_analysis(self):
        self._clear()
        self._print_header("CANCELLATION ANALYSIS")
        result = self.anal.cancellation_analysis()

        print(colour(f"\n  Total Cancelled Orders: {result['total_cancelled']:,}\n", CYAN))

        print(colour("  Top 10 Cancelled SKUs:\n", YELLOW))
        for i, r in enumerate(result["top_cancelled_skus"], 1):
            print(f"  {i:>3}. {r['sku']:<35}  Cancellations: {r['cancellations']:>6,}")

        print(colour("\n  Cancellations by Category:\n", YELLOW))
        for r in result["top_cancelled_cats"]:
            print(f"  {r['category']:<30}  {r['cancellations']:>6,}")

        if result["high_risk_stockout_skus"]:
            print(colour("\n  High-Risk Stockout SKUs (>50% cancellation rate):\n", RED))
            for r in result["high_risk_stockout_skus"]:
                print(f"  {r['sku']:<35}  Rate: {r['cancellation_rate_%']}%  "
                      f"({r['cancelled']}/{r['total']})")

        print(colour("\n  ─── Stockout Proxy Assumption ───\n", YELLOW))
        print(colour("  " + result["assumption_note"], DIM))
        self._pause()

    def _show_inventory_turnover(self):
        self._clear()
        self._print_header("INVENTORY TURNOVER RATIO  (Simplified)")
        result = self.anal.inventory_turnover()

        print(colour("\n  Top 20 SKUs by Inventory Turnover Ratio:\n", CYAN))
        print(colour(f"  {'SKU':<35}  {'Total Qty':>10}  {'Peak/Mo':>8}  {'Turnover':>10}", DIM))
        print("  " + "─" * 68)
        for r in result["turnover_by_sku"]:
            print(f"  {r['sku']:<35}  {r['total_qty']:>10,}  "
                  f"{r['peak_monthly_qty']:>8,}  {r['turnover_ratio']:>10.2f}x")

        print(colour("\n  ─── Limitation Note ───\n", YELLOW))
        print(colour("  " + result["limitation_note"], DIM))
        self._pause()

    # ──────────────────────────────────────────────────────────────────────
    # Promotion Menu
    # ──────────────────────────────────────────────────────────────────────

    def _promotion_menu(self):
        self._clear()
        self._print_header("PROMOTION ANALYSIS")
        n = self._input_int("Show top N promotions", default=10)
        results = self.anal.promotion_analysis()[:n]

        if not results:
            print(colour("  No promotion data found.", YELLOW))
        else:
            print(colour(f"\n  Top {n} Promotions by Order Count:\n", CYAN))
            for i, r in enumerate(results, 1):
                cats = ", ".join(r["top_categories"]) if r["top_categories"] else "N/A"
                pid  = r["promotion_id"][:60] + "..." if len(r["promotion_id"]) > 60 else r["promotion_id"]
                print(f"  {i:>3}. Orders: {r['order_count']:>6,}  "
                      f"Amount: ₹{r['total_amount']:>12,.2f}")
                print(f"       Top Categories: {cats}")
                print(f"       Promotion: {colour(pid, DIM)}")
                print()

        self._pause()

    # ──────────────────────────────────────────────────────────────────────
    # Charts Menu
    # ──────────────────────────────────────────────────────────────────────

    def _charts_menu(self):
        try:
            self.um.require_role("view_charts")
        except PermissionError as e:
            self._error(str(e))
            return

        while True:
            self._clear()
            self._print_header("CHARTS & REPORTS")
            opts = [
                ("1", "Generate ALL Charts"),
                ("2", "Sales by State      (Bar Chart)"),
                ("3", "Order Status        (Pie Chart)"),
                ("4", "Sales by Category   (Bar Chart)"),
                ("5", "Monthly Sales Trend (Line Chart)"),
                ("0", "Back"),
            ]
            self._print_menu(opts)
            print(colour(f"  Charts saved to: {os.path.abspath('reports/')}\n", DIM))
            choice = self._input("Enter choice").strip()

            if choice == "0":
                break
            elif choice == "1":
                paths = self.vis.generate_all_charts()
                print(colour(f"\n  ✔  {len(paths)} chart(s) saved.", GREEN))
                for p in paths:
                    print(colour(f"     {os.path.abspath(p)}", DIM))
            elif choice == "2":
                p = self.vis.bar_sales_by_state()
                print(colour(f"\n  ✔  Saved: {os.path.abspath(p)}", GREEN))
            elif choice == "3":
                p = self.vis.pie_order_status()
                print(colour(f"\n  ✔  Saved: {os.path.abspath(p)}", GREEN))
            elif choice == "4":
                p = self.vis.bar_sales_by_category()
                print(colour(f"\n  ✔  Saved: {os.path.abspath(p)}", GREEN))
            elif choice == "5":
                p = self.vis.line_monthly_sales()
                print(colour(f"\n  ✔  Saved: {os.path.abspath(p)}", GREEN))
            else:
                self._error("Invalid choice.")
            if choice != "0":
                self._pause()

    # ──────────────────────────────────────────────────────────────────────
    # Skipped Rows Viewer
    # ──────────────────────────────────────────────────────────────────────

    def _view_skipped(self):
        self._clear()
        self._print_header("SKIPPED / INVALID ROWS")
        skipped = self.om.get_skipped_rows()
        if not skipped:
            print(colour("  No rows were skipped — dataset is clean!", GREEN))
        else:
            print(colour(f"  {len(skipped):,} rows skipped during CSV parsing:\n", YELLOW))
            for s in skipped[:50]:
                print(f"  Row {s['row_number']:>6}: {colour(s['reason'], RED)}")
                print(f"           {colour(s['raw'], DIM)}")
                print()
            if len(skipped) > 50:
                print(colour(f"  ... and {len(skipped)-50:,} more.", DIM))
        self._pause()

    # ──────────────────────────────────────────────────────────────────────
    # Logout / Exit
    # ──────────────────────────────────────────────────────────────────────

    def _logout(self):
        self.um.logout()
        self._sorted_for_binary = None
        print(colour("\n  You have been logged out.", GREEN))
        self._pause()

    def _exit(self):
        self._clear()
        print(colour("\n  Thank you for using the Integrated Inventory & Analytics System.", CYAN))
        print(colour("  Goodbye!\n", GREEN))
        sys.exit(0)

    # ──────────────────────────────────────────────────────────────────────
    # UI helpers
    # ──────────────────────────────────────────────────────────────────────

    def _print_banner(self):
        banner = f"""
{colour('  ╔══════════════════════════════════════════════════════╗', CYAN)}
{colour('  ║                                                      ║', CYAN)}
{colour('  ║    INTEGRATED INVENTORY & ANALYTICS SYSTEM           ║', CYAN + BOLD)}
{colour('  ║    Amazon Sale Report — Academic Project             ║', CYAN)}
{colour('  ║                                                      ║', CYAN)}
{colour('  ╚══════════════════════════════════════════════════════╝', CYAN)}
{colour('  Default accounts:', DIM)}
{colour('    Manager       : admin   / manager123', DIM)}
{colour('    Junior Manager: junior  / junior123', DIM)}
"""
        print(banner)

    def _print_header(self, title: str):
        width = 54
        pad   = max(0, (width - len(title)) // 2)
        print(colour("  " + "═" * width, CYAN))
        print(colour("  " + " " * pad + title, BOLD + WHITE))
        print(colour("  " + "═" * width, CYAN))
        print()

    def _print_menu(self, options: list):
        for num, label in options:
            if num == "0":
                print(f"  {colour(num + '.', DIM)}  {colour(label, DIM)}")
            else:
                print(f"  {colour(num + '.', CYAN)}  {label}")
        print()

    def _show_algo_note(self, name: str, complexity: str, note: str):
        print(colour(f"  Algorithm: {name}  |  Complexity: {complexity}", MAGENTA))
        print(colour(f"  {note}\n", DIM))

    def _input(self, prompt: str) -> str:
        try:
            return input(f"  {colour('›', CYAN)} {prompt}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return ""

    def _input_required(self, prompt: str) -> str:
        while True:
            value = self._input(prompt)
            if value:
                return value
            print(colour("  This field is required.", RED))

    def _input_password(self, prompt: str) -> str:
        """Read password without echoing characters."""
        try:
            import getpass
            return getpass.getpass(f"  {colour('›', CYAN)} {prompt}: ")
        except Exception:
            return self._input(prompt)

    def _input_int(self, prompt: str, default: int = 10) -> int:
        raw = self._input(f"{prompt} [default {default}]")
        if not raw:
            return default
        try:
            v = int(raw)
            return v if v > 0 else default
        except ValueError:
            self._error(f"Invalid number. Using default: {default}.")
            return default

    def _error(self, message: str):
        print(colour(f"\n  ✗  {message}", RED))

    def _pause(self):
        try:
            input(colour("\n  Press Enter to continue...", DIM))
        except (EOFError, KeyboardInterrupt):
            pass

    @staticmethod
    def _clear():
        os.system("clear" if os.name == "posix" else "cls")


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    cli = CLI()
    cli.run()
