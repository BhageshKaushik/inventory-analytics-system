# Integrated Inventory and Analytics System

An academic Python project that loads the Amazon Sale Report dataset and provides
inventory management, role-based access control, manual search/sort algorithms,
sales analytics, and Matplotlib visualisations — all via a Command-Line Interface.

---

## Project Objectives

- Store and manage Amazon order data in memory using Python lists and dicts.
- Authenticate users with SHA-256 hashed passwords and enforce role-based permissions.
- Implement search, sorting, and hashing algorithms manually (no built-in `sorted()`).
- Perform eleven categories of sales and inventory analytics without Pandas or NumPy.
- Generate professional charts saved to the `reports/` folder.
- Provide a complete, navigable CLI.

---

## Technology Stack

| Component        | Technology                      |
|------------------|---------------------------------|
| Language         | Python 3.11+                    |
| IDE              | Visual Studio Code              |
| OS               | macOS (Apple Silicon / Intel)   |
| Data Storage     | Python lists, dicts, sets       |
| Visualisation    | Matplotlib                      |
| Input Dataset    | Amazon Sale Report CSV          |
| Interface        | Command-Line Interface (CLI)    |

**Strict restrictions honoured:**
- No Pandas, NumPy, SQL, or third-party analysis libraries.
- No Python `csv` module — custom quote-aware parser implemented.
- All search, sort, and aggregation algorithms hand-coded.

---

## Project Folder Structure

```
inventory_analytics/
│
├── data/
│   └── amazon_sales.csv          ← Amazon Sale Report dataset
│
├── reports/                      ← Saved chart PNGs (auto-created)
│
├── csv_parser.py                 ← Manual quote-aware CSV parser
├── order.py                      ← Order class (data model)
├── order_manager.py              ← CRUD + hash indexes
├── user_manager.py               ← Auth, RBAC, session management
├── algorithms.py                 ← All search/sort/hash algorithms
├── analytics.py                  ← All 11 analytical functions
├── visualisation.py              ← 4 Matplotlib charts
├── main.py                       ← CLI entry point
├── README.md
└── requirements.txt
```

---

## Dataset Description

**File:** `data/amazon_sales.csv`  
**Source:** Amazon Sale Report (Kaggle)  
**Rows:** ~128,975 orders  
**Size:** ~66 MB  

| Column             | Description                                |
|--------------------|--------------------------------------------|
| index              | Row number in original CSV                 |
| Order ID           | Unique transaction identifier              |
| Date               | Order date (MM-DD-YY format)               |
| Status             | e.g. Shipped, Cancelled, Pending           |
| Fulfilment         | Merchant or Amazon                         |
| Sales Channel      | e.g. Amazon.in                             |
| ship-service-level | Standard or Expedited                      |
| Style              | Product style code                         |
| SKU                | Stock Keeping Unit                         |
| Category           | Product category (kurta, Set, Blouse, ...) |
| Size               | Product size                               |
| ASIN               | Amazon Standard Identification Number      |
| Courier Status     | e.g. Shipped, Unshipped                    |
| Qty                | Quantity ordered                           |
| currency           | INR                                        |
| Amount             | Order value                                |
| ship-city          | Destination city                           |
| ship-state         | Destination state                          |
| ship-postal-code   | Postal code                                |
| ship-country       | Country code (IN)                          |
| promotion-ids      | Comma-separated promotion identifiers      |
| B2B                | Business-to-Business flag (True/False)     |
| fulfilled-by       | Easy Ship, Merchant, etc.                  |
| Unnamed: 22        | Trailing empty column — dropped on parse   |

---

## Installation Instructions (macOS)

### 1. Create a virtual environment

```bash
python3 -m venv venv
```

### 2. Activate the environment

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python3 main.py
```

---

## Default Login Credentials

| Username | Password    | Role           |
|----------|-------------|----------------|
| admin    | manager123  | Manager        |
| junior   | junior123   | Junior Manager |

---

## Features

### Order Management
- Load 128,000+ orders from CSV on startup.
- View all orders (paginated to 50).
- Add new orders with full field entry.
- Edit mutable fields: Status, Courier Status, Qty, Amount.
- Delete orders by Order ID.

### Search
| Method              | Algorithm       | Complexity    |
|---------------------|-----------------|---------------|
| By Order ID         | Hash Index      | O(1) avg      |
| By Status           | Linear Search   | O(n)          |
| By Category         | Linear Search   | O(n)          |
| By Ship City        | Hash Index      | O(1) avg      |
| By SKU              | Hash Index      | O(1) avg      |
| By Order ID (exact) | Binary Search   | O(log n)      |
| By Ship State       | Linear Search   | O(n)          |

### Sorting
| Method                     | Algorithm              | Complexity       |
|----------------------------|------------------------|------------------|
| By Amount (descending)     | Quick Sort             | O(n log n) avg   |
| By Qty (descending)        | Quick Sort             | O(n log n) avg   |
| By Date (ascending)        | Merge Sort (stable)    | O(n log n)       |
| By Date then Order ID      | Stable Multi-key Merge | O(n log n)       |

### Analytics
1. Top N products by Revenue.
2. Top N products by Quantity.
3. Sales by City (hash lookup).
4. Sales by State (linear scan).
5. Order Status distribution.
6. Category Performance (Amount + Qty).
7. Order Value Analysis + CLV explanation.
8. Cancellation Analysis (Stockout Proxy).
9. Seasonal Purchasing Patterns (monthly + quarterly).
10. Inventory Turnover Ratio (simplified).
11. Promotion Analysis.

### Visualisation
All charts saved to `reports/`:
1. `sales_by_state.png`     — Horizontal bar chart.
2. `order_status_pie.png`   — Pie chart.
3. `sales_by_category.png`  — Vertical bar chart.
4. `monthly_sales_trend.png`— Line chart with order volume overlay.

---

## User Roles

### Manager
Full access — CRUD, search, sort, analytics, charts.

### Junior Manager
Read-only access:
- Search by Order ID, Status, Category, City.
- Sort by Date, Amount, Qty.
- All analytics and inventory analysis.
- Cannot add, edit, or delete orders.

---

## Algorithms and Complexities

| Algorithm       | Use Case                       | Time Complexity       | Space Complexity |
|-----------------|--------------------------------|-----------------------|------------------|
| Linear Search   | Status / Category / State      | O(n)                  | O(k)             |
| Binary Search   | Order ID (sorted input)        | O(log n)              | O(1)             |
| Hash Lookup     | Order ID / SKU / City          | O(1) avg              | O(n)             |
| Quick Sort      | Amount / Qty                   | O(n log n) avg        | O(log n)         |
| Merge Sort      | Date / multi-key (stable)      | O(n log n)            | O(n)             |
| Heap Top-N      | Top N orders                   | O(n log k)            | O(k)             |

---

## Limitations and Assumptions

1. **CLV cannot be calculated** — The dataset has no customer identifier. Order ID is transaction-scoped.
2. **Inventory Turnover** — Uses peak monthly Qty as a proxy for average inventory (actual stock levels unavailable).
3. **Stockout Proxy** — Cancellations are used as a stockout indicator but do not prove stockouts.
4. **Date parsing** — Orders with unparseable dates are still loaded; date-based features skip them.
5. **In-memory storage** — All data lives in RAM. Restarting the application discards manual edits.
6. **Seed users** — `admin` and `junior` are created at startup for demonstration.
