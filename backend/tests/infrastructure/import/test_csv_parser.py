import pytest
from pathlib import Path
from decimal import Decimal
from datetime import date
import tempfile
from src.infrastructure.import_.csv_parser import CSVParser, InvalidCSVFormatError, InvalidTransactionDataError


class TestCSVParserConsorsbank:

    def test_parse_valid_consorsbank_csv(self):
        """Parse valid Consorsbank CSV with income + expense transactions."""
        csv_content = """Buchungstag,Wertstellung,Umsatzart,Begünstigter / Auftraggeber,Verwendungszweck,Betrag,Saldo
2026-05-01,2026-05-01,UEBERWEISUNG,John Doe,Salary May,+5000.00,10000.00
2026-05-02,2026-05-02,KARTENZAHLUNG,Amazon,Laptop,−250.50,9749.50"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            f.flush()

            result = CSVParser.parse_consorsbank(Path(f.name))

        assert len(result) == 2
        assert result[0]["date"] == date(2026, 5, 1)
        assert result[0]["amount"] == Decimal("5000.00")
        assert result[0]["type"] == "INCOME"
        assert result[0]["description"] == "John Doe - Salary May"

        assert result[1]["date"] == date(2026, 5, 2)
        assert result[1]["amount"] == Decimal("250.50")
        assert result[1]["type"] == "EXPENSE"
        assert result[1]["description"] == "Amazon - Laptop"

    def test_parse_consorsbank_missing_columns(self):
        """Raise InvalidCSVFormatError if expected columns are missing."""
        csv_content = "Datum,Betrag\n2026-05-01,1000"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            f.flush()

            with pytest.raises(InvalidCSVFormatError):
                CSVParser.parse_consorsbank(Path(f.name))

    def test_parse_consorsbank_invalid_amount(self):
        """Raise InvalidTransactionDataError if amount is not parseable."""
        csv_content = """Buchungstag,Wertstellung,Umsatzart,Begünstigter / Auftraggeber,Verwendungszweck,Betrag,Saldo
2026-05-01,2026-05-01,UEBERWEISUNG,John Doe,Salary,INVALID,10000.00"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            f.flush()

            with pytest.raises(InvalidTransactionDataError):
                CSVParser.parse_consorsbank(Path(f.name))


class TestCSVParserTradeRepublic:

    def test_parse_valid_trade_republic_csv(self):
        """Parse valid Trade Republic CSV (pre-converted from PDF)."""
        csv_content = """Datum,Beschreibung,Typ,Betrag
2026-05-01,Dividend Payment,Income,+50.00
2026-05-02,Stock Purchase,Expense,−1200.00"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            f.flush()

            result = CSVParser.parse_trade_republic(Path(f.name))

        assert len(result) == 2
        assert result[0]["date"] == date(2026, 5, 1)
        assert result[0]["amount"] == Decimal("50.00")
        assert result[0]["type"] == "INCOME"
        assert result[0]["description"] == "Dividend Payment"

        assert result[1]["date"] == date(2026, 5, 2)
        assert result[1]["amount"] == Decimal("1200.00")
        assert result[1]["type"] == "EXPENSE"
        assert result[1]["description"] == "Stock Purchase"

    def test_parse_trade_republic_missing_columns(self):
        """Raise InvalidCSVFormatError if expected columns are missing."""
        csv_content = "Datum,Betrag\n2026-05-01,100"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            f.flush()

            with pytest.raises(InvalidCSVFormatError):
                CSVParser.parse_trade_republic(Path(f.name))

    def test_parse_trade_republic_invalid_amount(self):
        """Raise InvalidTransactionDataError if amount is not parseable."""
        csv_content = """Datum,Beschreibung,Typ,Betrag
2026-05-01,Payment,Income,INVALID"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_content)
            f.flush()

            with pytest.raises(InvalidTransactionDataError):
                CSVParser.parse_trade_republic(Path(f.name))
