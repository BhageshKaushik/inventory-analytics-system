"""
order.py
========
Defines the Order class — the core data model for the system.

Each Order represents one row from the Amazon Sale Report CSV.

Design decisions
----------------
* All fields are stored as Python-native types:
    - Qty      → int   (0 if missing/invalid)
    - Amount   → float (0.0 if missing/invalid)
    - Date     → str   (kept as original string; parsed to datetime lazily)
    - B2B      → bool
* The __str__() method produces a human-readable multi-line summary.
* Only mutable business fields have setters; identifiers are read-only.
"""

from datetime import datetime


class Order:
    """
    Represents a single Amazon sales order.

    Attributes (match CSV columns)
    -------------------------------
    index           : int   — original CSV row index
    order_id        : str   — unique order identifier
    date            : str   — raw date string from CSV (e.g. "04-30-22")
    status          : str   — e.g. "Shipped", "Cancelled"
    fulfilment      : str   — "Merchant" or "Amazon"
    sales_channel   : str   — e.g. "Amazon.in"
    ship_service    : str   — "Standard", "Expedited", etc.
    style           : str   — product style code
    sku             : str   — stock keeping unit
    category        : str   — e.g. "kurta", "Set", "Western Dress"
    size            : str   — e.g. "S", "M", "XL", "3XL"
    asin            : str   — Amazon Standard Identification Number
    courier_status  : str   — e.g. "Shipped", "Unshipped", ""
    qty             : int   — quantity ordered
    currency        : str   — e.g. "INR"
    amount          : float — order value in currency units
    ship_city       : str   — destination city
    ship_state      : str   — destination state
    ship_postal     : str   — postal/zip code
    ship_country    : str   — destination country code
    promotion_ids   : list  — list of promotion identifier strings
    b2b             : bool  — True if business-to-business order
    fulfilled_by    : str   — "Easy Ship", "Merchant", etc.
    """

    # Date formats we try when parsing the date string
    _DATE_FORMATS = ["%m-%d-%y", "%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y"]

    def __init__(self, index, order_id, date, status, fulfilment,
                 sales_channel, ship_service, style, sku, category,
                 size, asin, courier_status, qty, currency, amount,
                 ship_city, ship_state, ship_postal, ship_country,
                 promotion_ids, b2b, fulfilled_by):

        # ── Immutable identifiers ─────────────────────────────────────────
        self._index = self._safe_int(index, 0)
        self._order_id = str(order_id).strip()
        self._date_raw = str(date).strip()
        self._date = self._parse_date(self._date_raw)   # datetime | None

        # ── Mutable business fields ───────────────────────────────────────
        self._status = str(status).strip()
        self._courier_status = str(courier_status).strip()
        self._qty = self._safe_int(qty, 0)
        self._amount = self._safe_float(amount, 0.0)

        # ── Descriptive / product fields ──────────────────────────────────
        self._fulfilment = str(fulfilment).strip()
        self._sales_channel = str(sales_channel).strip()
        self._ship_service = str(ship_service).strip()
        self._style = str(style).strip()
        self._sku = str(sku).strip()
        self._category = str(category).strip()
        self._size = str(size).strip()
        self._asin = str(asin).strip()
        self._currency = str(currency).strip()

        # ── Shipping / location fields ────────────────────────────────────
        self._ship_city = str(ship_city).strip().upper()
        self._ship_state = str(ship_state).strip().upper()
        self._ship_postal = str(ship_postal).strip()
        self._ship_country = str(ship_country).strip()

        # ── Promotion IDs — stored as a list ─────────────────────────────
        self._promotion_ids = self._parse_promotions(promotion_ids)

        # ── B2B flag ──────────────────────────────────────────────────────
        self._b2b = self._parse_bool(b2b)

        self._fulfilled_by = str(fulfilled_by).strip()

    # ──────────────────────────────────────────────────────────────────────
    # Properties — read-only identifiers
    # ──────────────────────────────────────────────────────────────────────

    @property
    def index(self):        return self._index

    @property
    def order_id(self):     return self._order_id

    @property
    def date_raw(self):     return self._date_raw

    @property
    def date(self):         return self._date          # datetime or None

    @property
    def fulfilment(self):   return self._fulfilment

    @property
    def sales_channel(self): return self._sales_channel

    @property
    def ship_service(self): return self._ship_service

    @property
    def style(self):        return self._style

    @property
    def sku(self):          return self._sku

    @property
    def category(self):     return self._category

    @property
    def size(self):         return self._size

    @property
    def asin(self):         return self._asin

    @property
    def currency(self):     return self._currency

    @property
    def ship_city(self):    return self._ship_city

    @property
    def ship_state(self):   return self._ship_state

    @property
    def ship_postal(self):  return self._ship_postal

    @property
    def ship_country(self): return self._ship_country

    @property
    def promotion_ids(self): return self._promotion_ids

    @property
    def b2b(self):          return self._b2b

    @property
    def fulfilled_by(self): return self._fulfilled_by

    # ──────────────────────────────────────────────────────────────────────
    # Mutable properties — these can be edited by managers
    # ──────────────────────────────────────────────────────────────────────

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Status must be a non-empty string.")
        self._status = value.strip()

    @property
    def courier_status(self):
        return self._courier_status

    @courier_status.setter
    def courier_status(self, value: str):
        self._courier_status = str(value).strip()

    @property
    def qty(self):
        return self._qty

    @qty.setter
    def qty(self, value):
        v = self._safe_int(value, -1)
        if v < 0:
            raise ValueError(f"Qty must be a non-negative integer. Got: {value!r}")
        self._qty = v

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self, value):
        v = self._safe_float(value, -1.0)
        if v < 0:
            raise ValueError(f"Amount must be a non-negative number. Got: {value!r}")
        self._amount = v

    # ──────────────────────────────────────────────────────────────────────
    # String representation
    # ──────────────────────────────────────────────────────────────────────

    def __str__(self):
        promo_str = (", ".join(self._promotion_ids[:2]) + " ..."
                     if len(self._promotion_ids) > 2
                     else ", ".join(self._promotion_ids) or "None")
        return (
            f"┌{'─'*50}\n"
            f"│ Order ID      : {self._order_id}\n"
            f"│ Date          : {self._date_raw}\n"
            f"│ Status        : {self._status}\n"
            f"│ Category      : {self._category}  |  Size: {self._size}\n"
            f"│ SKU           : {self._sku}  |  ASIN: {self._asin}\n"
            f"│ Qty           : {self._qty}  |  Amount: {self._currency} {self._amount:.2f}\n"
            f"│ Ship to       : {self._ship_city}, {self._ship_state} - {self._ship_postal}\n"
            f"│ Fulfilment    : {self._fulfilment}  |  By: {self._fulfilled_by}\n"
            f"│ Courier Status: {self._courier_status}\n"
            f"│ B2B           : {self._b2b}\n"
            f"│ Promotions    : {promo_str}\n"
            f"└{'─'*50}"
        )

    def to_dict(self):
        """Return order fields as a plain dictionary (useful for display)."""
        return {
            "index": self._index,
            "order_id": self._order_id,
            "date": self._date_raw,
            "status": self._status,
            "fulfilment": self._fulfilment,
            "sales_channel": self._sales_channel,
            "ship_service": self._ship_service,
            "style": self._style,
            "sku": self._sku,
            "category": self._category,
            "size": self._size,
            "asin": self._asin,
            "courier_status": self._courier_status,
            "qty": self._qty,
            "currency": self._currency,
            "amount": self._amount,
            "ship_city": self._ship_city,
            "ship_state": self._ship_state,
            "ship_postal": self._ship_postal,
            "ship_country": self._ship_country,
            "promotion_ids": self._promotion_ids,
            "b2b": self._b2b,
            "fulfilled_by": self._fulfilled_by,
        }

    # ──────────────────────────────────────────────────────────────────────
    # Private helpers — type coercion and parsing
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _safe_int(value, default: int) -> int:
        """Convert value to int safely; return default on failure."""
        try:
            return int(float(str(value).strip()))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _safe_float(value, default: float) -> float:
        """Convert value to float safely; return default on failure."""
        try:
            return float(str(value).strip())
        except (ValueError, TypeError):
            return default

    @classmethod
    def _parse_date(cls, date_str: str):
        """
        Try multiple date formats and return a datetime object.
        Returns None if parsing fails (date_str is kept as raw string).
        """
        date_str = date_str.strip()
        for fmt in cls._DATE_FORMATS:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_promotions(raw) -> list:
        """
        Parse the promotion-ids field.
        The field may contain multiple IDs separated by commas (inside the
        quoted value).  Returns a list of stripped, non-empty strings.
        """
        if not raw or str(raw).strip() == "":
            return []
        # At this point the outer quotes have already been stripped by the
        # CSV parser; just split on comma.
        parts = str(raw).split(",")
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _parse_bool(value) -> bool:
        """Convert common boolean string representations to Python bool."""
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("true", "1", "yes")
