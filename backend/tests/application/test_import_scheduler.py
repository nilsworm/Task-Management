from __future__ import annotations

import tempfile
from pathlib import Path
from decimal import Decimal
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.services.import_scheduler import ImportScheduler
from src.domain.cost.entities import Transaction
from src.domain.cost.value_objects import TransactionType
from src.infrastructure.import_.csv_parser import CSVParser, InvalidCSVFormatError


@pytest.mark.asyncio
async def test_import_scheduler_run_weekly_import_consorsbank():
    """Run weekly import: scan /imports, parse CSVs, import transactions, archive files."""

    # Create temporary import folder with test CSV
    with tempfile.TemporaryDirectory() as tmpdir:
        import_folder = Path(tmpdir)
        archive_folder = import_folder / "archived"
        archive_folder.mkdir()

        # Write test CSV
        csv_file = import_folder / "consorsbank_2026-05-01.csv"
        csv_content = """Konto
Allgemeine Informationen
Kontostand
Kontoumsätze
Buchung;Valuta;Sender / Empfänger;IBAN;BIC;Buchungstext;Verwendungszweck;Kategorie;Stichwörter;Umsatz geteilt;Betrag;Währung
01.05.2026;01.05.2026;John Doe;DE123;BIC123;UEBERWEISUNG;Salary May;n/a;n/a;n/a;5.000,00;EUR
02.05.2026;02.05.2026;Amazon;DE456;BIC456;KARTENZAHLUNG;Laptop;n/a;n/a;n/a;−250,50;EUR"""
        csv_file.write_text(csv_content)

        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.create_transaction_from_import = AsyncMock(
            side_effect=[
                Transaction.create(
                    title="John Doe - Salary May",
                    amount=Decimal("5000.00"),
                    transaction_type=TransactionType.INCOME,
                    transaction_date=date(2026, 5, 1),
                ),
                Transaction.create(
                    title="Amazon - Laptop",
                    amount=Decimal("250.50"),
                    transaction_type=TransactionType.EXPENSE,
                    transaction_date=date(2026, 5, 2),
                ),
            ]
        )

        scheduler = ImportScheduler(mock_repo, import_folder)
        result = await scheduler.run_weekly_import()

        # Verify result
        assert result["status"] == "success"
        assert result["imported"] == 2
        assert result["files"] == ["consorsbank_2026-05-01.csv"]

        # Verify CSV was archived
        assert not csv_file.exists()
        assert (archive_folder / "consorsbank_2026-05-01.csv").exists()

        # Verify repo calls
        assert mock_repo.create_transaction_from_import.call_count == 2


@pytest.mark.asyncio
async def test_import_scheduler_run_weekly_import_trade_republic():
    """Run weekly import with Trade Republic format."""

    with tempfile.TemporaryDirectory() as tmpdir:
        import_folder = Path(tmpdir)
        archive_folder = import_folder / "archived"
        archive_folder.mkdir()

        # Write test CSV
        csv_file = import_folder / "trade_republic_2026-05.csv"
        csv_content = """Datum,Beschreibung,Typ,Betrag
2026-05-01,Buy Tesla,Kauf,−500.00
2026-05-02,Dividend,Dividend,+25.00"""
        csv_file.write_text(csv_content)

        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.create_transaction_from_import = AsyncMock(
            side_effect=[
                Transaction.create(
                    title="Buy Tesla",
                    amount=Decimal("500.00"),
                    transaction_type=TransactionType.EXPENSE,
                    transaction_date=date(2026, 5, 1),
                ),
                Transaction.create(
                    title="Dividend",
                    amount=Decimal("25.00"),
                    transaction_type=TransactionType.INCOME,
                    transaction_date=date(2026, 5, 2),
                ),
            ]
        )

        scheduler = ImportScheduler(mock_repo, import_folder)
        result = await scheduler.run_weekly_import()

        # Verify result
        assert result["status"] == "success"
        assert result["imported"] == 2
        assert result["files"] == ["trade_republic_2026-05.csv"]

        # Verify CSV was archived
        assert not csv_file.exists()
        assert (archive_folder / "trade_republic_2026-05.csv").exists()


@pytest.mark.asyncio
async def test_import_scheduler_handles_multiple_files():
    """Import multiple CSV files in one run."""

    with tempfile.TemporaryDirectory() as tmpdir:
        import_folder = Path(tmpdir)
        archive_folder = import_folder / "archived"
        archive_folder.mkdir()

        # Write two CSVs
        consors_file = import_folder / "consorsbank_2026-05.csv"
        consors_content = """Konto
Allgemeine Informationen
Kontostand
Kontoumsätze
Buchung;Valuta;Sender / Empfänger;IBAN;BIC;Buchungstext;Verwendungszweck;Kategorie;Stichwörter;Umsatz geteilt;Betrag;Währung
01.05.2026;01.05.2026;John;DE123;BIC123;UEBERWEISUNG;Test;n/a;n/a;n/a;1.000,00;EUR"""
        consors_file.write_text(consors_content)

        tr_file = import_folder / "traderepublic_2026-05.csv"
        tr_content = """Datum,Beschreibung,Typ,Betrag
2026-05-02,Test,Buy,−100.00"""
        tr_file.write_text(tr_content)

        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.create_transaction_from_import = AsyncMock(
            side_effect=[
                Transaction.create(
                    title="John - Test",
                    amount=Decimal("1000.00"),
                    transaction_type=TransactionType.INCOME,
                    transaction_date=date(2026, 5, 1),
                ),
                Transaction.create(
                    title="Test",
                    amount=Decimal("100.00"),
                    transaction_type=TransactionType.EXPENSE,
                    transaction_date=date(2026, 5, 2),
                ),
            ]
        )

        scheduler = ImportScheduler(mock_repo, import_folder)
        result = await scheduler.run_weekly_import()

        # Verify result
        assert result["status"] == "success"
        assert result["imported"] == 2
        assert sorted(result["files"]) == sorted(
            ["consorsbank_2026-05.csv", "traderepublic_2026-05.csv"]
        )

        # Verify both CSVs were archived
        assert not consors_file.exists()
        assert not tr_file.exists()
        assert (archive_folder / "consorsbank_2026-05.csv").exists()
        assert (archive_folder / "traderepublic_2026-05.csv").exists()


@pytest.mark.asyncio
async def test_import_scheduler_graceful_error_handling():
    """Files with parsing errors stay in /imports; import continues for valid files."""

    with tempfile.TemporaryDirectory() as tmpdir:
        import_folder = Path(tmpdir)
        archive_folder = import_folder / "archived"
        archive_folder.mkdir()

        # Valid CSV
        valid_file = import_folder / "consorsbank_valid.csv"
        valid_content = """Konto
Allgemeine Informationen
Kontostand
Kontoumsätze
Buchung;Valuta;Sender / Empfänger;IBAN;BIC;Buchungstext;Verwendungszweck;Kategorie;Stichwörter;Umsatz geteilt;Betrag;Währung
01.05.2026;01.05.2026;Test;DE123;BIC123;UEBERWEISUNG;Test;n/a;n/a;n/a;500,00;EUR"""
        valid_file.write_text(valid_content)

        # Invalid CSV (missing columns)
        invalid_file = import_folder / "invalid.csv"
        invalid_content = "col1,col2\nvalue1,value2"
        invalid_file.write_text(invalid_content)

        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.create_transaction_from_import = AsyncMock(
            return_value=Transaction.create(
                title="Test - Test",
                amount=Decimal("500.00"),
                transaction_type=TransactionType.INCOME,
                transaction_date=date(2026, 5, 1),
            )
        )

        scheduler = ImportScheduler(mock_repo, import_folder)
        result = await scheduler.run_weekly_import()

        # Verify: only valid file imported
        assert result["status"] == "success"
        assert result["imported"] == 1
        assert result["files"] == ["consorsbank_valid.csv"]

        # Valid file archived, invalid stays
        assert not valid_file.exists()
        assert invalid_file.exists()
        assert (archive_folder / "consorsbank_valid.csv").exists()


@pytest.mark.asyncio
async def test_import_scheduler_empty_folder():
    """Empty /imports folder returns success with 0 imported."""

    with tempfile.TemporaryDirectory() as tmpdir:
        import_folder = Path(tmpdir)
        archive_folder = import_folder / "archived"
        archive_folder.mkdir()

        mock_repo = AsyncMock()

        scheduler = ImportScheduler(mock_repo, import_folder)
        result = await scheduler.run_weekly_import()

        assert result["status"] == "success"
        assert result["imported"] == 0
        assert result["files"] == []


@pytest.mark.asyncio
async def test_import_scheduler_creates_archive_folder_if_missing():
    """Scheduler creates /archived folder if it doesn't exist."""

    with tempfile.TemporaryDirectory() as tmpdir:
        import_folder = Path(tmpdir)

        csv_file = import_folder / "consorsbank_2026-05.csv"
        csv_content = """Konto
Allgemeine Informationen
Kontostand
Kontoumsätze
Buchung;Valuta;Sender / Empfänger;IBAN;BIC;Buchungstext;Verwendungszweck;Kategorie;Stichwörter;Umsatz geteilt;Betrag;Währung
01.05.2026;01.05.2026;Test;DE123;BIC123;UEBERWEISUNG;Test;n/a;n/a;n/a;100,00;EUR"""
        csv_file.write_text(csv_content)

        # Don't create archive folder; scheduler should create it
        mock_repo = AsyncMock()
        mock_repo.create_transaction_from_import = AsyncMock(
            return_value=Transaction.create(
                title="Test - Test",
                amount=Decimal("100.00"),
                transaction_type=TransactionType.INCOME,
                transaction_date=date(2026, 5, 1),
            )
        )

        scheduler = ImportScheduler(mock_repo, import_folder)
        result = await scheduler.run_weekly_import()

        # Archive folder should have been created
        archive_folder = import_folder / "archived"
        assert archive_folder.exists()
        assert result["status"] == "success"
        assert (archive_folder / "consorsbank_2026-05.csv").exists()


@pytest.mark.asyncio
async def test_import_scheduler_skips_files_with_undetectable_format():
    """Files not matching consorsbank/trade_republic pattern are skipped."""

    with tempfile.TemporaryDirectory() as tmpdir:
        import_folder = Path(tmpdir)
        archive_folder = import_folder / "archived"
        archive_folder.mkdir()

        # Unknown format file
        unknown_file = import_folder / "unknown_format.csv"
        unknown_content = "col1,col2\nval1,val2"
        unknown_file.write_text(unknown_content)

        mock_repo = AsyncMock()

        scheduler = ImportScheduler(mock_repo, import_folder)
        result = await scheduler.run_weekly_import()

        # File should stay in /imports (not archived)
        assert result["status"] == "success"
        assert result["imported"] == 0
        assert result["files"] == []
        assert unknown_file.exists()
        assert not (archive_folder / "unknown_format.csv").exists()


@pytest.mark.asyncio
async def test_import_scheduler_continues_on_individual_row_errors():
    """If one row fails, scheduler continues importing remaining rows."""

    with tempfile.TemporaryDirectory() as tmpdir:
        import_folder = Path(tmpdir)
        archive_folder = import_folder / "archived"
        archive_folder.mkdir()

        csv_file = import_folder / "consorsbank_partial.csv"
        csv_content = """Konto
Allgemeine Informationen
Kontostand
Kontoumsätze
Buchung;Valuta;Sender / Empfänger;IBAN;BIC;Buchungstext;Verwendungszweck;Kategorie;Stichwörter;Umsatz geteilt;Betrag;Währung
01.05.2026;01.05.2026;Test1;DE123;BIC123;UEBERWEISUNG;Test;n/a;n/a;n/a;500,00;EUR
02.05.2026;02.05.2026;Test2;DE123;BIC123;UEBERWEISUNG;Test;n/a;n/a;n/a;100,00;EUR
03.05.2026;03.05.2026;Test3;DE123;BIC123;UEBERWEISUNG;Test;n/a;n/a;n/a;200,00;EUR"""
        csv_file.write_text(csv_content)

        # Mock repo: first succeeds, second fails, third succeeds
        mock_repo = AsyncMock()
        mock_repo.create_transaction_from_import = AsyncMock(
            side_effect=[
                Transaction.create(
                    title="Test1 - Test",
                    amount=Decimal("500.00"),
                    transaction_type=TransactionType.INCOME,
                    transaction_date=date(2026, 5, 1),
                ),
                Exception("DB error"),
                Transaction.create(
                    title="Test3 - Test",
                    amount=Decimal("200.00"),
                    transaction_type=TransactionType.INCOME,
                    transaction_date=date(2026, 5, 3),
                ),
            ]
        )

        scheduler = ImportScheduler(mock_repo, import_folder)
        result = await scheduler.run_weekly_import()

        # File was still archived (parsing succeeded), but only 2 of 3 rows imported successfully
        assert result["status"] == "success"
        assert result["imported"] == 2  # One succeeded, one failed, one succeeded
        assert result["files"] == ["consorsbank_partial.csv"]
        assert not csv_file.exists()
        assert (archive_folder / "consorsbank_partial.csv").exists()
