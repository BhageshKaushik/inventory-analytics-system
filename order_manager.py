"""
order_manager.py
================
Manages the collection of Order objects.

Responsibilities
----------------
* Load orders from the CSV via CSVParser.
* Maintain an in-memory list of Order objects.
* Maintain two secondary indexes for fast lookup:
    - _index_by_order_id : dict  { order_id  → list[Order] }
    - _index_by_sku      : dict  { sku        → list[Order] }
    - _index_by_city     : dict  { ship_city  → list[Order] }
* Provide CRUD: add, edit, delete, view.
* Rebuild indexes after every mutation.
* Never crash — log and report errors gracefully.
"""

import os
from csv_parser import CSVParser
from order import Order


class OrderManager:
    """
    Central manager for all Order objects.

    Data structures used
    --------------------
    _orders          : list[Order]           — primary store (ordered)
    _index_by_order_id : dict[str, list]    — hash index on Order ID
    _index_by_sku      : dict[str, list]    — hash index on SKU
    _index_by_city     : dict[str, list]    — hash index on ship-city
    _skipped_rows      : list[dict]         — rows that were skipped during load
    """

    CSV_PATH = os.path.join("data", "amazon_sales.csv")

    def __init__(self):
        self._orders = []
        self._index_by_order_id = {}
        self._index_by_sku = {}
        self._index_by_city = {}
        self._skipped_rows = []
        self._next_id = 1       # auto-increment for manually added orders

    # ──────────────────────────────────────────────────────────────────────
    # Loading
    # ──────────────────────────────────────────────────────────────────────

    def load_csv(self, filepath: str = None):
        """
        Parse the CSV and populate the order list and indexes.

        Parameters
        ----------
        filepath : str  (optional) — override the default CSV_PATH.
        """
        path = filepath or self.CSV_PATH
        print(f"[OrderManager] Loading dataset from: {path}")

        try:
            parser = CSVParser()
            rows, skipped = parser.parse(path)
        except FileNotFoundError as e:
            print(f"[ERROR] {e}")
            return
        except Exception as e:
            print(f"[ERROR] Unexpected error while parsing CSV: {e}")
            return

        self._skipped_rows = skipped
        self._orders = []

        for row in rows:
            try:
                order = self._row_to_order(row)
                self._orders.append(order)
            except Exception as e:
                self._skipped_rows.append({
                    "row_number": row.get("index", "?"),
                    "reason": f"Order construction failed: {e}",
                    "raw": str(row)[:120]
                })

        # Build indexes after all orders are loaded
        self._rebuild_indexes()

        print(f"[OrderManager] Loaded {len(self._orders):,} orders.")
        if self._skipped_rows:
            print(f"[OrderManager] Skipped {len(self._skipped_rows):,} invalid rows.")

    def _row_to_order(self, row: dict) -> Order:
        """Construct an Order from a parsed CSV row dictionary."""
        return Order(
            index          = row.get("index", 0),
            order_id       = row.get("Order ID", ""),
            date           = row.get("Date", ""),
            status         = row.get("Status", ""),
            fulfilment     = row.get("Fulfilment", ""),
            sales_channel  = row.get("Sales Channel", ""),
            ship_service   = row.get("ship-service-level", ""),
            style          = row.get("Style", ""),
            sku            = row.get("SKU", ""),
            category       = row.get("Category", ""),
            size           = row.get("Size", ""),
            asin           = row.get("ASIN", ""),
            courier_status = row.get("Courier Status", ""),
            qty            = row.get("Qty", 0),
            currency       = row.get("currency", "INR"),
            amount         = row.get("Amount", 0.0),
            ship_city      = row.get("ship-city", ""),
            ship_state     = row.get("ship-state", ""),
            ship_postal    = row.get("ship-postal-code", ""),
            ship_country   = row.get("ship-country", ""),
            promotion_ids  = row.get("promotion-ids", ""),
            b2b            = row.get("B2B", "False"),
            fulfilled_by   = row.get("fulfilled-by", ""),
        )

    # ──────────────────────────────────────────────────────────────────────
    # Index management
    # ──────────────────────────────────────────────────────────────────────

    def _rebuild_indexes(self):
        """Rebuild all secondary indexes from scratch."""
        self._index_by_order_id = {}
        self._index_by_sku = {}
        self._index_by_city = {}

        for order in self._orders:
            # Order ID index
            oid = order.order_id
            if oid not in self._index_by_order_id:
                self._index_by_order_id[oid] = []
            self._index_by_order_id[oid].append(order)

            # SKU index
            sku = order.sku
            if sku not in self._index_by_sku:
                self._index_by_sku[sku] = []
            self._index_by_sku[sku].append(order)

            # City index
            city = order.ship_city
            if city not in self._index_by_city:
                self._index_by_city[city] = []
            self._index_by_city[city].append(order)

    def _add_to_indexes(self, order: Order):
        """Add a single order to all indexes (used after add_order)."""
        for idx, key in [
            (self._index_by_order_id, order.order_id),
            (self._index_by_sku,      order.sku),
            (self._index_by_city,     order.ship_city),
        ]:
            if key not in idx:
                idx[key] = []
            idx[key].append(order)

    def _remove_from_indexes(self, order: Order):
        """Remove a single order from all indexes (used after delete_order)."""
        for idx, key in [
            (self._index_by_order_id, order.order_id),
            (self._index_by_sku,      order.sku),
            (self._index_by_city,     order.ship_city),
        ]:
            if key in idx:
                try:
                    idx[key].remove(order)
                except ValueError:
                    pass
                if not idx[key]:        # clean up empty lists
                    del idx[key]

    # ──────────────────────────────────────────────────────────────────────
    # CRUD — Create
    # ──────────────────────────────────────────────────────────────────────

    def add_order(self, order_id, date, status, fulfilment, sales_channel,
                  ship_service, style, sku, category, size, asin,
                  courier_status, qty, currency, amount,
                  ship_city, ship_state, ship_postal, ship_country,
                  promotion_ids, b2b, fulfilled_by) -> Order:
        """
        Create a new Order and append it to the collection.
        Returns the newly created Order.
        """
        new_order = Order(
            index          = self._next_id,
            order_id       = order_id,
            date           = date,
            status         = status,
            fulfilment     = fulfilment,
            sales_channel  = sales_channel,
            ship_service   = ship_service,
            style          = style,
            sku            = sku,
            category       = category,
            size           = size,
            asin           = asin,
            courier_status = courier_status,
            qty            = qty,
            currency       = currency,
            amount         = amount,
            ship_city      = ship_city,
            ship_state     = ship_state,
            ship_postal    = ship_postal,
            ship_country   = ship_country,
            promotion_ids  = promotion_ids,
            b2b            = b2b,
            fulfilled_by   = fulfilled_by,
        )
        self._next_id += 1
        self._orders.append(new_order)
        self._add_to_indexes(new_order)
        return new_order

    # ──────────────────────────────────────────────────────────────────────
    # CRUD — Read
    # ──────────────────────────────────────────────────────────────────────

    def view_all_orders(self, limit: int = 50) -> list:
        """Return up to `limit` orders (default 50 to avoid flooding the CLI)."""
        return self._orders[:limit]

    def get_all_orders(self) -> list:
        """Return the full list of all orders (use for analytics)."""
        return self._orders

    def order_count(self) -> int:
        """Return total number of orders loaded."""
        return len(self._orders)

    def get_skipped_rows(self) -> list:
        """Return the list of skipped row reports."""
        return self._skipped_rows

    def get_by_order_id(self, order_id: str) -> list:
        """Hash-index lookup: return all orders with the given Order ID."""
        return self._index_by_order_id.get(order_id.strip(), [])

    def get_by_sku(self, sku: str) -> list:
        """Hash-index lookup: return all orders with the given SKU."""
        return self._index_by_sku.get(sku.strip(), [])

    def get_by_city(self, city: str) -> list:
        """Hash-index lookup: return all orders shipped to the given city."""
        return self._index_by_city.get(city.strip().upper(), [])

    def get_index_by_order_id(self) -> dict:
        """Expose the Order ID index (used by algorithms module)."""
        return self._index_by_order_id

    def get_index_by_sku(self) -> dict:
        """Expose the SKU index (used by algorithms module)."""
        return self._index_by_sku

    def get_index_by_city(self) -> dict:
        """Expose the city index (used by algorithms module)."""
        return self._index_by_city

    # ──────────────────────────────────────────────────────────────────────
    # CRUD — Update
    # ──────────────────────────────────────────────────────────────────────

    def edit_order(self, order_id: str, **kwargs) -> bool:
        """
        Edit mutable fields of an order identified by order_id.

        Accepted keyword arguments
        --------------------------
        status, courier_status, qty, amount

        Returns True if at least one order was updated, False otherwise.
        """
        targets = self.get_by_order_id(order_id)
        if not targets:
            print(f"[OrderManager] Order ID '{order_id}' not found.")
            return False

        editable_fields = {"status", "courier_status", "qty", "amount"}
        updated = False

        for order in targets:
            for field, value in kwargs.items():
                if field not in editable_fields:
                    print(f"[WARNING] Field '{field}' is not editable. Skipping.")
                    continue
                try:
                    setattr(order, field, value)
                    updated = True
                except (ValueError, AttributeError) as e:
                    print(f"[ERROR] Could not set {field}={value!r}: {e}")

        return updated

    # ──────────────────────────────────────────────────────────────────────
    # CRUD — Delete
    # ──────────────────────────────────────────────────────────────────────

    def delete_order(self, order_id: str) -> int:
        """
        Delete all orders with the given Order ID.
        Returns the number of orders deleted.
        """
        targets = self.get_by_order_id(order_id)
        if not targets:
            print(f"[OrderManager] Order ID '{order_id}' not found.")
            return 0

        count = 0
        for order in list(targets):   # iterate a copy
            self._remove_from_indexes(order)
            self._orders.remove(order)
            count += 1

        print(f"[OrderManager] Deleted {count} order(s) with ID '{order_id}'.")
        return count
