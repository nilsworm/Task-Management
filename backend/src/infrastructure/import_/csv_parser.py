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

    @staticmethod
    def parse_consorsbank(file_path: Path) -> list[dict]:
        """Parse Consorsbank CSV export.

        Expected columns: Buchungstag, Wertstellung, Umsatzart, Begünstigter / Auftraggeber,
                         Verwendungszweck, Betrag, Saldo

        Returns: [{"date": DATE, "amount": DECIMAL, "description": str, "type": "INCOME" | "EXPENSE"}]
        """
        required_columns = [
            "Buchungstag", "Wertstellung", "Umsatzart",
            "Begünstigter / Auftraggeber", "Verwendungszweck", "Betrag", "Saldo"
        ]

        result = []

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Validate columns
            if reader.fieldnames is None or not all(col in reader.fieldnames for col in required_columns):
                raise InvalidCSVFormatError(f"Missing required columns. Expected: {required_columns}")

            for row in reader:
                try:
                    # Parse date
                    date_str = row["Buchungstag"].strip()
                    tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                    # Parse amount (handle +/− prefixes)
                    amount_str = row["Betrag"].strip().replace("+", "").replace("−", "-").replace(",", ".")
                    amount = Decimal(amount_str)

                    # Determine type based on sign
                    tx_type = "INCOME" if amount > 0 else "EXPENSE"
                    amount = abs(amount)

                    # Build description
                    description = f"{row['Begünstigter / Auftraggeber'].strip()} - {row['Verwendungszweck'].strip()}"

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
    def parse_trade_republic(file_path: Path) -> list[dict]:
        """Parse Trade Republic CSV (pre-converted from PDF via kontoauszug.jonathanpagel.com).

        Expected columns: Datum, Beschreibung, Typ, Betrag

        Returns: [{"date": DATE, "amount": DECIMAL, "description": str, "type": "INCOME" | "EXPENSE"}]
        """
        required_columns = ["Datum", "Beschreibung", "Typ", "Betrag"]

        result = []

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Validate columns
            if reader.fieldnames is None or not all(col in reader.fieldnames for col in required_columns):
                raise InvalidCSVFormatError(f"Missing required columns. Expected: {required_columns}")

            for row in reader:
                try:
                    # Parse date
                    date_str = row["Datum"].strip()
                    tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()

                    # Parse amount (handle +/− prefixes)
                    amount_str = row["Betrag"].strip().replace("+", "").replace("−", "-").replace(",", ".")
                    amount = Decimal(amount_str)

                    # Determine type based on sign (override Typ column if needed)
                    tx_type = "INCOME" if amount > 0 else "EXPENSE"
                    amount = abs(amount)

                    description = row["Beschreibung"].strip()

                    result.append({
                        "date": tx_date,
                        "amount": amount,
                        "type": tx_type,
                        "description": description,
                    })
                except (ValueError, KeyError, InvalidOperation) as e:
                    raise InvalidTransactionDataError(f"Failed to parse row: {row}") from e

        return result
