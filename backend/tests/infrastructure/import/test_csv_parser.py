import pytest
from pathlib import Path
from decimal import Decimal
from datetime import date
import tempfile
from src.infrastructure.import_.csv_parser import CSVParser, InvalidCSVFormatError, InvalidTransactionDataError


class TestCSVParserConsorsbank:

    def test_parse_valid_consorsbank_csv(self):
        """Parse valid Consorsbank CSV with income + expense transactions."""
        csv_content = """Konto
Allgemeine Informationen
Kontostand
Kontoumsätze
Buchung;Valuta;Sender / Empfänger;IBAN;BIC;Buchungstext;Verwendungszweck;Kategorie;Stichwörter;Umsatz geteilt;Betrag;Währung
01.05.2026;01.05.2026;John Doe;DE123;BIC123;UEBERWEISUNG;Salary May;n/a;n/a;n/a;5.000,00;EUR
02.05.2026;02.05.2026;Amazon;DE456;BIC456;KARTENZAHLUNG;Laptop;n/a;n/a;n/a;−250,50;EUR"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=True, encoding='utf-8') as f:
            f.write(csv_content)
            f.flush()

            result = CSVParser.parse_consorsbank(Path(f.name))

        assert len(result) == 2
        assert result[0]["date"] == date(2026, 5, 1)
        assert result[0]["amount"] == Decimal("5000.00")
        assert result[0]["type"] == "INCOME"
        assert result[0]["description"] == "John Doe"

        assert result[1]["date"] == date(2026, 5, 2)
        assert result[1]["amount"] == Decimal("250.50")
        assert result[1]["type"] == "EXPENSE"
        assert result[1]["description"] == "Amazon"

    def test_parse_consorsbank_missing_columns(self):
        """Raise InvalidCSVFormatError if expected columns are missing."""
        csv_content = "Buchung;Betrag\n01.05.2026;1000"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=True, encoding='utf-8') as f:
            f.write(csv_content)
            f.flush()

            with pytest.raises(InvalidCSVFormatError):
                CSVParser.parse_consorsbank(Path(f.name))

    def test_parse_consorsbank_invalid_amount(self):
        """Raise InvalidTransactionDataError if amount is not parseable."""
        csv_content = """Konto
Allgemeine Informationen
Kontostand
Kontoumsätze
Buchung;Valuta;Sender / Empfänger;IBAN;BIC;Buchungstext;Verwendungszweck;Kategorie;Stichwörter;Umsatz geteilt;Betrag;Währung
01.05.2026;01.05.2026;John Doe;DE123;BIC123;UEBERWEISUNG;Salary;n/a;n/a;n/a;INVALID;EUR"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=True, encoding='utf-8') as f:
            f.write(csv_content)
            f.flush()

            with pytest.raises(InvalidTransactionDataError):
                CSVParser.parse_consorsbank(Path(f.name))


TR_HEADER = '"datetime","date","account_type","category","type","asset_class","name","symbol","shares","price","amount","fee","tax","currency","original_amount","original_currency","fx_rate","description","transaction_id","counterparty_name","counterparty_iban","payment_reference","mcc_code"'

OWN_CONSORSBANK_IBAN = "DE80760300800270566776"


class TestCSVParserTradeRepublic:

    def test_card_expense_interest_dividend_saveback_become_correct_types(self):
        csv_content = f"""{TR_HEADER}
"2026-05-01T10:00:00Z","2026-05-01","DEFAULT","CASH","CARD_TRANSACTION","","Lidl sagt Danke","","","","-13.120000","","","EUR","","","","TR Card Transaction","id1","","","",""
"2026-05-02T10:00:00Z","2026-05-02","DEFAULT","CASH","INTEREST_PAYMENT","","","","","","0.680000","","-0.18","EUR","","","","Interest payment","id2","","","",""
"2026-05-03T10:00:00Z","2026-05-03","DEFAULT","CASH","DIVIDEND","STOCK","Nike (B)","US6541061031","10.0","","3.300000","","-0.85","EUR","","","","Cash Dividend","id3","","","",""
"2026-05-04T10:00:00Z","2026-05-04","DEFAULT","CASH","BENEFITS_SAVEBACK","FUND","Core MSCI World","IE00B4L5Y983","","","1.250000","","","EUR","","","","Your Saveback","id4","","","",""
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=True, encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            result = CSVParser.parse_trade_republic(Path(f.name))

        assert len(result) == 4
        assert result[0] == {"date": date(2026, 5, 1), "amount": Decimal("13.120000"), "type": "EXPENSE", "description": "Lidl sagt Danke"}
        assert result[1] == {"date": date(2026, 5, 2), "amount": Decimal("0.680000"), "type": "INCOME", "description": "INTEREST_PAYMENT"}
        assert result[2] == {"date": date(2026, 5, 3), "amount": Decimal("3.300000"), "type": "INCOME", "description": "Nike (B)"}
        assert result[3] == {"date": date(2026, 5, 4), "amount": Decimal("1.250000"), "type": "INCOME", "description": "Core MSCI World"}

    def test_buy_becomes_stock_type(self):
        csv_content = f"""{TR_HEADER}
"2026-05-01T10:00:00Z","2026-05-01","DEFAULT","TRADING","BUY","FUND","Core MSCI World USD (Acc)","IE00B4L5Y983","1.808168","96.783000","-175.000000","","","EUR","","","","Savings plan execution IE00B4L5Y983","id1","","","",""
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=True, encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            result = CSVParser.parse_trade_republic(Path(f.name))

        assert len(result) == 1
        assert result[0]["type"] == "STOCK"
        assert result[0]["amount"] == Decimal("175.000000")
        assert result[0]["description"] == "Core MSCI World USD (Acc)"

    def test_transfer_inbound_from_own_iban_is_skipped(self):
        csv_content = f"""{TR_HEADER}
"2026-04-30T02:00:00Z","2026-04-30","DEFAULT","CASH","TRANSFER_INBOUND","","Nils Worm","","","","1500.000000","","","EUR","","","","Incoming transfer from Nils Worm ({OWN_CONSORSBANK_IBAN})","id1","Nils Worm","{OWN_CONSORSBANK_IBAN}","",""
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=True, encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            result = CSVParser.parse_trade_republic(
                Path(f.name), own_account_ibans=[OWN_CONSORSBANK_IBAN]
            )

        assert result == []

    def test_free_receipt_and_inpayment_are_skipped(self):
        csv_content = f"""{TR_HEADER}
"2026-05-01T10:00:00Z","2026-05-01","DEFAULT","DELIVERY","FREE_RECEIPT","FUND","Core MSCI World","IE00B4L5Y983","12.0","","","","","","","","","FREE_RECEIPT","id1","","","",""
"2026-05-02T10:00:00Z","2026-05-02","DEFAULT","CASH","CUSTOMER_INPAYMENT","","","","","","175.000000","","","EUR","","","","Direct Debit Top up with {OWN_CONSORSBANK_IBAN}","id2","","","",""
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=True, encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            result = CSVParser.parse_trade_republic(Path(f.name))

        assert result == []

    def test_missing_columns_raises_invalid_format_error(self):
        csv_content = '"date","name"\n"2026-05-01","test"'
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=True, encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            with pytest.raises(InvalidCSVFormatError):
                CSVParser.parse_trade_republic(Path(f.name))

    def test_invalid_amount_raises_invalid_transaction_data_error(self):
        csv_content = f"""{TR_HEADER}
"2026-05-01T10:00:00Z","2026-05-01","DEFAULT","CASH","CARD_TRANSACTION","","Shop","","","","INVALID","","","EUR","","","","TR Card Transaction","id1","","","",""
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=True, encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            with pytest.raises(InvalidTransactionDataError):
                CSVParser.parse_trade_republic(Path(f.name))
