"""
csv_parser.py
=============
A fully manual, quote-aware CSV parser.

Design decisions
----------------
* Does NOT import Python's `csv` module (assignment restriction).
* Parses character-by-character using a simple state machine so that
  quoted fields containing commas (like promotion-ids) are handled
  correctly.
* Drops the trailing unnamed column (`Unnamed: 22`) automatically.
* Records every skipped row with a human-readable reason.
* Never crashes on bad input — invalid rows are logged and skipped.
"""

import os


class CSVParser:
    """
    Manual, quote-aware CSV parser.

    Usage
    -----
        parser = CSVParser()
        rows, skipped = parser.parse("data/amazon_sales.csv")

    Returns
    -------
    rows    : list of dict  — one dict per valid row, keys = headers
    skipped : list of dict  — {"row_number": int, "reason": str, "raw": str}
    """

    # Required columns for a row to be considered valid
    REQUIRED_COLUMNS = ["Order ID", "Date", "Status"]

    def parse(self, filepath: str):
        """
        Parse a CSV file and return (rows, skipped_rows).

        Parameters
        ----------
        filepath : str  Path to the CSV file.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Dataset not found: {filepath}")

        rows = []
        skipped = []
        headers = None

        with open(filepath, encoding="utf-8", errors="replace") as fh:
            for line_num, raw_line in enumerate(fh, start=1):
                # Strip the newline but preserve internal whitespace
                raw_line = raw_line.rstrip("\n").rstrip("\r")

                # Parse the raw line into a list of field strings
                fields = self._parse_line(raw_line)

                # ── First line is the header ──────────────────────────────
                if line_num == 1:
                    headers = self._normalise_headers(fields)
                    continue

                # ── Skip completely blank lines ───────────────────────────
                if not raw_line.strip():
                    continue

                # ── Build a dict from headers + fields ───────────────────
                row_dict, reason = self._build_row(headers, fields, line_num)

                if reason:
                    skipped.append({
                        "row_number": line_num,
                        "reason": reason,
                        "raw": raw_line[:120]   # truncate for readability
                    })
                    continue

                # ── Validate required columns are non-empty ───────────────
                missing = [
                    col for col in self.REQUIRED_COLUMNS
                    if not row_dict.get(col, "").strip()
                ]
                if missing:
                    skipped.append({
                        "row_number": line_num,
                        "reason": f"Missing required field(s): {missing}",
                        "raw": raw_line[:120]
                    })
                    continue

                rows.append(row_dict)

        return rows, skipped

    # ──────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────

    def _parse_line(self, line: str) -> list:
        """
        Split a CSV line into fields using a character-by-character state
        machine.  Correctly handles:
          - Quoted fields containing commas.
          - Escaped double-quotes inside quoted fields ("").
          - Empty fields.
        """
        fields = []
        current = []
        in_quotes = False

        i = 0
        while i < len(line):
            ch = line[i]

            if in_quotes:
                if ch == '"':
                    # Peek ahead: "" means an escaped quote inside a field
                    if i + 1 < len(line) and line[i + 1] == '"':
                        current.append('"')
                        i += 2
                        continue
                    else:
                        # Closing quote
                        in_quotes = False
                else:
                    current.append(ch)
            else:
                if ch == '"':
                    in_quotes = True
                elif ch == ',':
                    fields.append("".join(current))
                    current = []
                else:
                    current.append(ch)
            i += 1

        # Append the last field (no trailing comma)
        fields.append("".join(current))
        return fields

    def _normalise_headers(self, raw_headers: list) -> list:
        """
        Strip whitespace from header names and remove the trailing
        unnamed column (`Unnamed: 22`).  Returns the cleaned list.
        """
        cleaned = []
        for h in raw_headers:
            h = h.strip()
            # Drop any column whose name starts with "Unnamed:"
            if h.lower().startswith("unnamed:") or h == "":
                cleaned.append(None)   # placeholder; will be excluded
            else:
                cleaned.append(h)
        return cleaned

    def _build_row(self, headers: list, fields: list, line_num: int):
        """
        Zip headers and fields into a dict, excluding unnamed columns.

        Returns (row_dict, error_reason).
        If the field count doesn't match, we still try to map what we have
        (lenient parsing) but log a warning.
        """
        row_dict = {}
        reason = None

        # Pad fields if too short (some rows may omit trailing empty fields)
        if len(fields) < len(headers):
            fields = fields + [""] * (len(headers) - len(fields))

        for i, header in enumerate(headers):
            if header is None:
                # Skip the unnamed/dropped columns
                continue
            value = fields[i].strip() if i < len(fields) else ""
            row_dict[header] = value

        return row_dict, reason
