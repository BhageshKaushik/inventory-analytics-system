"""
algorithms.py
=============
All searching, sorting, and hashing algorithms implemented from scratch.

Assignment restrictions satisfied
-----------------------------------
* Python's built-in sorted() and list.sort() are NOT used for the
  required algorithms below.
* Every function includes a docstring explaining its time complexity.

Algorithms implemented
----------------------
Search:
  1. linear_search_by_status()   — O(n)
  2. binary_search_by_order_id() — O(log n), requires sorted input
  3. hash_lookup_sku()           — O(1) average
  4. hash_lookup_city()          — O(1) average

Sort:
  5. quick_sort_by_amount()      — O(n log n) avg, O(n²) worst
  6. quick_sort_by_qty()         — O(n log n) avg, O(n²) worst
  7. merge_sort_by_date()        — O(n log n), stable
  8. merge_sort_by_date_then_id()— O(n log n), stable (multi-key)
  9. merge_sorted_by_category()  — O(n+m), merge two already-sorted lists

Utility:
 10. heap_top_n()               — O(n log k) — min-heap for top-N
"""


# ══════════════════════════════════════════════════════════════════════════════
# ── SEARCH ALGORITHMS ────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════


def linear_search_by_status(orders: list, target_status: str) -> list:
    """
    Linear Search — find all orders whose Status equals target_status.

    How it works
    ------------
    Scan every element in the list from index 0 to n-1 and collect
    matches.  No pre-processing is required.

    Time complexity  : O(n) — every record is visited once.
    Space complexity : O(k) — where k is the number of matches.

    When to use
    -----------
    * When the list is unsorted.
    * When you need ALL matches (not just one).
    * When n is small enough that O(n) is acceptable.
    * Best choice here because Status is not a unique key.

    Parameters
    ----------
    orders        : list[Order]  — the full order collection
    target_status : str          — e.g. "Cancelled", "Shipped"

    Returns
    -------
    list[Order]  — all orders with the matching status
    """
    target_status = target_status.strip().lower()
    result = []

    for order in orders:            # visit every element — O(n)
        if order.status.lower() == target_status:
            result.append(order)

    return result


def linear_search_by_field(orders: list, field: str, value: str) -> list:
    """
    Generic linear search across any string field of an Order.

    Supports: 'category', 'ship_city', 'ship_state', 'sku', 'order_id',
              'status', 'size', 'style', 'fulfilment', 'sales_channel'.

    Time complexity : O(n)
    """
    value = value.strip().lower()
    result = []

    for order in orders:
        field_value = str(getattr(order, field, "")).lower()
        if field_value == value:
            result.append(order)

    return result


def binary_search_by_order_id(sorted_orders: list, target_id: str) -> list:
    """
    Binary Search — find orders by Order ID in a sorted list.

    How it works
    ------------
    1. The list must be sorted by Order ID (lexicographically) beforehand.
    2. Examine the middle element.
    3. If it matches → found.
    4. If target < middle → search left half.
    5. If target > middle → search right half.
    6. Repeat until found or search space is empty.

    Time complexity  : O(log n) — halves the search space each step.
    Space complexity : O(1) — iterative implementation, no extra space.

    Limitation
    ----------
    Requires a sorted list.  Sorting costs O(n log n) upfront, so binary
    search is worth it only when many searches are performed on the same
    dataset (amortised cost).

    Parameters
    ----------
    sorted_orders : list[Order]  — MUST be sorted by order_id ascending
    target_id     : str          — the Order ID to find

    Returns
    -------
    list[Order]  — all orders at and around the matched position
                   (Order ID is not unique; there may be duplicates)
    """
    target_id = target_id.strip()
    low, high = 0, len(sorted_orders) - 1
    found_index = -1

    while low <= high:
        mid = (low + high) // 2
        mid_id = sorted_orders[mid].order_id

        if mid_id == target_id:
            found_index = mid
            break
        elif mid_id < target_id:
            low = mid + 1
        else:
            high = mid - 1

    if found_index == -1:
        return []

    # Collect all consecutive matches (duplicates around found_index)
    result = [sorted_orders[found_index]]

    # Expand left
    i = found_index - 1
    while i >= 0 and sorted_orders[i].order_id == target_id:
        result.append(sorted_orders[i])
        i -= 1

    # Expand right
    i = found_index + 1
    while i < len(sorted_orders) and sorted_orders[i].order_id == target_id:
        result.append(sorted_orders[i])
        i += 1

    return result


def hash_lookup_sku(sku_index: dict, sku: str) -> list:
    """
    Hash Table Lookup — find all orders with a given SKU.

    How it works
    ------------
    The _index_by_sku dict in OrderManager is a hash table where:
      key   = SKU string
      value = list of Order objects with that SKU

    Python dict uses an open-addressing hash table internally.
    A lookup is O(1) average because:
      1. The hash function maps the key to a bucket index.
      2. We jump directly to that bucket.

    Time complexity  : O(1) average (hash table lookup)
                       O(n) worst case (all keys hash to same bucket)
    Space complexity : O(n) — the index stores references to all orders.

    Drawback of hash tables
    -----------------------
    * No ordering — cannot do range queries (e.g. "all SKUs between A and B").
    * Collision handling adds overhead in the worst case.
    * Rebuilding the index after every mutation costs O(n).

    Parameters
    ----------
    sku_index : dict  — the hash index from OrderManager
    sku       : str   — the SKU to look up

    Returns
    -------
    list[Order]
    """
    return sku_index.get(sku.strip(), [])


def hash_lookup_city(city_index: dict, city: str) -> list:
    """
    Hash Index Lookup — retrieve all orders shipped to a given city.

    Design
    ------
    The _index_by_city dict maps:
      city_name (UPPER) → list[Order]

    This allows O(1) average retrieval of all orders for MUMBAI, DELHI,
    etc. without scanning the full dataset.

    Time complexity : O(1) average

    Parameters
    ----------
    city_index : dict  — the city hash index from OrderManager
    city       : str   — city name (case-insensitive)

    Returns
    -------
    list[Order]
    """
    return city_index.get(city.strip().upper(), [])


# ══════════════════════════════════════════════════════════════════════════════
# ── SORTING ALGORITHMS ───────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════


def quick_sort_by_amount(orders: list) -> list:
    """
    Quick Sort — sort orders by Amount (ascending).

    How it works
    ------------
    1. Choose a pivot element (we use the middle element to avoid worst
       case on already-sorted input).
    2. Partition: elements < pivot go left, elements > pivot go right,
       elements == pivot go centre.
    3. Recursively sort left and right partitions.
    4. Combine: left + centre + right.

    Time complexity
    ---------------
    Average case : O(n log n) — pivot splits list roughly in half each time.
    Worst case   : O(n²)      — occurs when the pivot is always the
                                smallest or largest element (e.g. already
                                sorted list with naive pivot selection).
    Space        : O(log n) recursion stack (average).

    Why Quick Sort?
    ---------------
    Fast in practice for large datasets due to good cache performance.
    Our middle-pivot selection reduces worst-case likelihood.

    Note: Quick Sort is NOT stable (equal elements may change relative order).

    Parameters
    ----------
    orders : list[Order]  — the list to sort (not modified in-place)

    Returns
    -------
    list[Order]  — sorted by amount ascending
    """
    if len(orders) <= 1:
        return orders

    pivot = orders[len(orders) // 2].amount
    left   = [o for o in orders if o.amount <  pivot]
    centre = [o for o in orders if o.amount == pivot]
    right  = [o for o in orders if o.amount >  pivot]

    return quick_sort_by_amount(left) + centre + quick_sort_by_amount(right)


def quick_sort_by_qty(orders: list) -> list:
    """
    Quick Sort — sort orders by Qty (ascending).

    Same algorithm as quick_sort_by_amount but keyed on Qty.

    Time complexity : O(n log n) average, O(n²) worst case.
    """
    if len(orders) <= 1:
        return orders

    pivot = orders[len(orders) // 2].qty
    left   = [o for o in orders if o.qty <  pivot]
    centre = [o for o in orders if o.qty == pivot]
    right  = [o for o in orders if o.qty >  pivot]

    return quick_sort_by_qty(left) + centre + quick_sort_by_qty(right)


def _merge(left: list, right: list, key_fn) -> list:
    """
    Internal helper: merge two sorted lists using key_fn for comparison.
    This is the merge step of Merge Sort.

    Why Merge Sort is STABLE
    ------------------------
    When left[i] and right[j] have equal keys, we always pick left[i]
    first (the `<=` condition below).  This preserves the original
    relative order of equal elements — the definition of stability.

    Stability matters when sorting by multiple keys sequentially:
    e.g. first sort by Order ID, then by Date.  After the Date sort,
    rows with the same Date remain in Order-ID order because the
    algorithm is stable.

    Time complexity : O(n + m) — linear in the sizes of both halves.
    """
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        # `<=` ensures stability: left wins ties
        if key_fn(left[i]) <= key_fn(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    # Append remaining elements
    result.extend(left[i:])
    result.extend(right[j:])
    return result


def merge_sort(orders: list, key_fn) -> list:
    """
    Generic stable Merge Sort.

    How it works
    ------------
    1. Divide the list into two halves.
    2. Recursively sort each half.
    3. Merge the two sorted halves back together.

    Time complexity  : O(n log n) — always (no worst case like Quick Sort).
    Space complexity : O(n) — needs auxiliary space for the merge step.

    When to prefer Merge Sort over Quick Sort
    -----------------------------------------
    * When stability is required (preserving order of equal elements).
    * When worst-case O(n²) is unacceptable.
    * When sorting linked lists (no random access needed).
    * Trade-off: uses more memory than Quick Sort.

    Parameters
    ----------
    orders : list[Order]
    key_fn : callable  — takes an Order, returns a comparable value

    Returns
    -------
    list[Order]  — sorted ascending by key_fn
    """
    if len(orders) <= 1:
        return orders

    mid = len(orders) // 2
    left  = merge_sort(orders[:mid],  key_fn)
    right = merge_sort(orders[mid:], key_fn)

    return _merge(left, right, key_fn)


def merge_sort_by_date(orders: list) -> list:
    """
    Merge Sort — sort orders by Date (ascending, None dates go last).

    Uses a comparable date key: datetime objects sort naturally.
    Rows with unparseable dates (date=None) are placed at the end.

    Time complexity : O(n log n), stable.
    """
    # Key: datetime objects are comparable; None → push to end
    def date_key(order):
        if order.date is None:
            # Large sentinel value: year 9999 pushes None-date rows last
            from datetime import datetime
            return datetime(9999, 12, 31)
        return order.date

    return merge_sort(orders, date_key)


def merge_sort_by_date_then_id(orders: list) -> list:
    """
    Multi-key stable sort: primary=Date, secondary=Order ID.

    Explanation
    -----------
    Because Merge Sort is stable, we can achieve a two-key sort by
    running two passes:
      Pass 1: Sort by Order ID (secondary key).
      Pass 2: Sort by Date (primary key).

    After pass 2, rows with the same Date remain in Order-ID order
    from pass 1.  This works ONLY because the sort is stable.

    Time complexity : O(n log n) × 2 passes = O(n log n) overall.
    """
    # Pass 1: sort by Order ID (secondary key)
    step1 = merge_sort(orders, lambda o: o.order_id)
    # Pass 2: stable sort by Date (primary key)
    step2 = merge_sort_by_date(step1)
    return step2


def merge_two_sorted_lists_by_category(list_a: list, list_b: list) -> list:
    """
    Merge two already-sorted (by Category) lists into one sorted list.

    Use case
    --------
    If you have sorted results from two separate queries (e.g. MUMBAI
    orders and DELHI orders, both already sorted by category), this
    merges them in O(n + m) — faster than re-sorting O((n+m) log(n+m)).

    Time complexity : O(n + m)
    """
    return _merge(list_a, list_b, lambda o: o.category.lower())


def sort_by_date_ascending(orders: list) -> list:
    """Convenience wrapper: sort orders by Date ascending (Merge Sort)."""
    return merge_sort_by_date(orders)


def sort_by_amount_descending(orders: list) -> list:
    """Sort orders by Amount descending using Quick Sort then reverse."""
    return list(reversed(quick_sort_by_amount(orders)))


def sort_by_qty_descending(orders: list) -> list:
    """Sort orders by Qty descending using Quick Sort then reverse."""
    return list(reversed(quick_sort_by_qty(orders)))


# ══════════════════════════════════════════════════════════════════════════════
# ── HEAP / TOP-N ─────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════


def heap_top_n(orders: list, n: int, key_fn) -> list:
    """
    Heap Sort-based Top-N selection — find the N orders with the highest
    value according to key_fn.

    How it works (Min-Heap approach)
    ---------------------------------
    1. Maintain a min-heap of size k (at most N elements).
    2. For each order:
       a. If heap size < N: push the order.
       b. Else if order's key > heap minimum: replace the minimum.
    3. After processing all orders, the heap contains the top-N.
    4. Sort the heap descending to return in ranked order.

    Why a min-heap for top-N?
    -------------------------
    The smallest element in the heap is always at the root.
    When a new element beats the root (current minimum of our top-N),
    we replace the root and re-heapify.  This keeps the heap size at N
    without storing all n elements.

    Time complexity  : O(n log k)  — n insertions, each O(log k) heapify.
    Space complexity : O(k)        — heap holds at most k=N elements.

    Comparison: Heap Sort vs Merge Sort space
    -----------------------------------------
    Heap Sort  : O(1) extra space (in-place, though our version uses O(k)).
    Merge Sort : O(n) extra space (auxiliary arrays for merge step).
    → Heap is more memory-efficient when only the top-N is needed.

    Parameters
    ----------
    orders : list[Order]
    n      : int        — how many top results to return
    key_fn : callable   — extracts the numeric key from an Order

    Returns
    -------
    list[Order]  — top N orders, sorted descending by key_fn
    """
    if n <= 0:
        return []

    heap = []   # list of (key_value, order)

    for order in orders:
        key_val = key_fn(order)

        if len(heap) < n:
            # Heap not full yet — just add
            heap.append((key_val, order))
            _heapify_up(heap, len(heap) - 1)
        elif key_val > heap[0][0]:
            # New element beats the current minimum — replace root
            heap[0] = (key_val, order)
            _heapify_down(heap, 0, len(heap))

    # Extract results sorted descending
    # (We use a simple insertion sort on the small heap — O(k²) but k is tiny)
    for i in range(len(heap) - 1, 0, -1):
        heap[0], heap[i] = heap[i], heap[0]
        _heapify_down(heap, 0, i)

    # After in-place heap sort, heap is ascending → reverse for descending
    return [item[1] for item in reversed(heap)]


def _heapify_up(heap: list, idx: int):
    """Bubble element at idx up to restore min-heap property."""
    while idx > 0:
        parent = (idx - 1) // 2
        if heap[idx][0] < heap[parent][0]:
            heap[idx], heap[parent] = heap[parent], heap[idx]
            idx = parent
        else:
            break


def _heapify_down(heap: list, idx: int, size: int):
    """Sink element at idx down to restore min-heap property."""
    while True:
        smallest = idx
        left  = 2 * idx + 1
        right = 2 * idx + 2

        if left  < size and heap[left][0]  < heap[smallest][0]:
            smallest = left
        if right < size and heap[right][0] < heap[smallest][0]:
            smallest = right

        if smallest != idx:
            heap[idx], heap[smallest] = heap[smallest], heap[idx]
            idx = smallest
        else:
            break


# ══════════════════════════════════════════════════════════════════════════════
# ── HELPER: prepare sorted list for binary search ────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def prepare_sorted_for_binary_search(orders: list) -> list:
    """
    Sort orders by Order ID using Merge Sort so binary search can be used.

    Why we sort before binary search
    ----------------------------------
    Binary search requires the data to be sorted.  Here we use Merge Sort
    (stable, O(n log n)) to produce a sorted copy without modifying the
    original list.

    Returns a NEW sorted list (original is unchanged).
    """
    return merge_sort(orders, lambda o: o.order_id)
