import logging
from pathlib import Path

from src.domain.cost.repository import ICostRepository
from src.infrastructure.import_.csv_parser import (
    CSVParser,
    InvalidCSVFormatError,
    InvalidTransactionDataError,
)

logger = logging.getLogger(__name__)


class ImportScheduler:
    """Schedules and executes weekly CSV imports from /imports folder.

    Scans /imports for CSV files, detects format from filename, parses via CSVParser,
    creates transactions via repository, and archives processed files.
    """

    def __init__(self, cost_repo: ICostRepository, import_folder: str | Path):
        """Initialize ImportScheduler.

        Args:
            cost_repo: Cost repository for persisting transactions
            import_folder: Path to folder containing CSV files to import
        """
        self.cost_repo = cost_repo
        self.import_folder = Path(import_folder)
        self.archive_folder = self.import_folder / "archived"

        # Ensure archive folder exists
        self.archive_folder.mkdir(parents=True, exist_ok=True)

    async def run_weekly_import(self) -> dict:
        """Scan /imports for CSVs, parse, import, archive.

        Process flow:
        1. Find all .csv files in import_folder (excluding archived/)
        2. For each CSV: detect format (consorsbank vs trade_republic) from filename
        3. Parse via CSVParser
        4. Create transactions via repository
        5. Archive successfully processed files
        6. Leave files with parsing errors in /imports for manual review

        Returns:
            {
                "status": "success",
                "imported": int,  # total transactions created
                "files": [str],   # list of archived filenames
            }
        """

        imported_count = 0
        imported_files = []

        # Find all .csv files in import_folder (excluding archived/)
        csv_files = [f for f in self.import_folder.glob("*.csv") if f.is_file()]

        for csv_file in csv_files:
            try:
                logger.info(f"Processing import file: {csv_file.name}")

                # Detect format by filename
                filename_lower = csv_file.name.lower()
                if "consorsbank" in filename_lower:
                    parsed_rows = CSVParser.parse_consorsbank(csv_file)
                    import_source = "consorsbank"
                elif "trade_republic" in filename_lower or "traderepublic" in filename_lower:
                    parsed_rows = CSVParser.parse_trade_republic(csv_file)
                    import_source = "trade_republic"
                else:
                    logger.warning(
                        f"Could not detect format for {csv_file.name} "
                        f"(expected 'consorsbank' or 'trade_republic' in filename). Skipping."
                    )
                    continue

                # Import each row
                for row in parsed_rows:
                    try:
                        await self.cost_repo.create_transaction_from_import(
                            row, import_source
                        )
                        imported_count += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to import row from {csv_file.name}: {e}"
                        )
                        # Continue with next row (graceful degradation)
                        continue

                # Archive file after successful parse (even if some rows failed import)
                archive_path = self.archive_folder / csv_file.name
                csv_file.rename(archive_path)
                imported_files.append(csv_file.name)
                logger.info(f"Archived {csv_file.name}")

            except (InvalidCSVFormatError, InvalidTransactionDataError) as e:
                logger.error(f"Failed to parse {csv_file.name}: {e}")
                # Leave file in /imports for manual review
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing {csv_file.name}: {e}")
                # Leave file in /imports for manual review
                continue

        return {
            "status": "success",
            "imported": imported_count,
            "files": imported_files,
        }
