import csv
from pathlib import Path
from decimal import Decimal, InvalidOperation
from datetime import datetime


class InvalidCSVFormatError(Exception):
    """Raised when CSV format is invalid (missing expected columns)."""
    pass


class InvalidTransactionDataError(Exception):
    """Raised when individual row data cannot be parsed."""
    pass


class CSVParser:
    _TR_SKIP_TYPES: frozenset[str] = frozenset({"FREE_RECEIPT", "CUSTOMER_INPAYMENT"})

    @staticmethod
    def parse_consorsbank(file_path: Path) -> list[dict]:
        """Parse Consorsbank CSV export (semicolon-delimited, German format).

        Expected columns: Buchung, Sender / Empfänger, Betrag, Währung
        Skips metadata headers until "Kontoumsätze" section.

        Returns: [{"date": DATE, "amount": DECIMAL, "description": str, "type": "INCOME" | "EXPENSE"}]
        """
        required_columns = ["Buchung", "Sender / Empfänger", "Betrag", "Währung"]

        result = []

        with open(file_path, 'r', encoding='utf-8') as f:
            # Skip metadata headers until we find "Kontoumsätze" (transaction section)
            for line in f:
                if line.strip() == "Kontoumsätze":
                    break

            # Next line is the header row
            reader = csv.DictReader(f, delimiter=';')

            # Validate columns (fieldnames include whitespace from CSV)
            if reader.fieldnames is None:
                raise InvalidCSVFormatError("No header row found")

            # Strip whitespace from field names for matching
            fieldnames_stripped = [col.strip() if col else col for col in reader.fieldnames]
            if not all(col in fieldnames_stripped for col in required_columns):
                raise InvalidCSVFormatError(f"Missing required columns. Expected: {required_columns}")

            for row in reader:
                try:
                    # Get column value and strip whitespace (fieldnames may have trailing spaces)
                    buchung_val = row.get("Buchung ", "") or row.get("Buchung", "")
                    if not buchung_val.strip():
                        continue

                    # Parse date (DD.MM.YYYY format)
                    date_str = buchung_val.strip()
                    tx_date = datetime.strptime(date_str, "%d.%m.%Y").date()

                    # Parse amount (German format: 1.234,56 or -1.234,56)
                    betrag_val = row.get("Betrag", "").strip()
                    amount_str = betrag_val.replace(".", "").replace(",", ".").replace("−", "-")
                    amount = Decimal(amount_str)

                    # Determine type based on sign
                    tx_type = "INCOME" if amount > 0 else "EXPENSE"
                    amount = abs(amount)

                    # Build description from sender/empfänger
                    description = (row.get("Sender / Empfänger", "") or row.get("Sender / Empfänger", "")).strip()

                    result.append({
                        "date": tx_date,
                        "amount": amount,
                        "type": tx_type,
                        "description": description,
                    })
                except (ValueError, KeyError, InvalidOperation) as e:
                    raise InvalidTransactionDataError(f"Failed to parse row: {row}") from e

        return result

    @staticmethod
    def parse_trade_republic(
        file_path: Path,
        own_account_ibans: list[str] | None = None,
    ) -> list[dict]:
        """Parse Trade Republic CSV export (Transaktionsexport.csv).

        Skips FREE_RECEIPT (no cash), CUSTOMER_INPAYMENT (own-account top-up),
        and TRANSFER_INBOUND from own accounts to avoid double-counting.
        BUY transactions become type STOCK (neutral, visible in analytics).

        Returns: [{"date": DATE, "amount": DECIMAL, "description": str, "type": str}]
        """
        required_columns = ["date", "type", "name", "amount", "counterparty_iban"]
        own_ibans: set[str] = set(own_account_ibans or [])
        result = []

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None or not all(col in reader.fieldnames for col in required_columns):
                raise InvalidCSVFormatError(f"Missing required columns. Expected: {required_columns}")

            for row in reader:
                tx_type_raw = row["type"].strip()

                if tx_type_raw in CSVParser._TR_SKIP_TYPES:
                    continue

                if tx_type_raw == "TRANSFER_INBOUND":
                    counterparty = row.get("counterparty_iban", "").strip()
                    if not own_ibans or counterparty in own_ibans:
                        continue

                try:
                    tx_date = datetime.strptime(row["date"].strip(), "%Y-%m-%d").date()

                    amount_str = row["amount"].strip()
                    if not amount_str:
                        continue
                    amount = Decimal(amount_str)

                    if tx_type_raw == "BUY":
                        tx_type = "STOCK"
                        amount = abs(amount)
                    elif amount >= 0:
                        tx_type = "INCOME"
                    else:
                        tx_type = "EXPENSE"
                        amount = abs(amount)

                    name = row["name"].strip()
                    description = name if name else tx_type_raw

                    result.append({
                        "date": tx_date,
                        "amount": amount,
                        "type": tx_type,
                        "description": description,
                    })
                except (ValueError, KeyError, InvalidOperation) as e:
                    raise InvalidTransactionDataError(f"Failed to parse row: {row}") from e

        return result
