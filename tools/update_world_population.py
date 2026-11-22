"""Rebuild the World Population demo CSV from a World Bank indicator ZIP."""

import argparse
import csv
from io import StringIO, TextIOWrapper
from pathlib import Path
from zipfile import ZipFile

DEMO = Path(__file__).resolve().parents[1] / "demo"
SNAPSHOT = DEMO / "data" / "API_SP.POP.TOTL_DS2_en_csv_v2_58181.zip"
REGION_CODES = ("WLD", "EAS", "ECS", "LCN", "MEA", "NAC", "SAS", "SSF")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "archive",
        type=Path,
        nargs="?",
        default=SNAPSHOT,
        help="World Bank SP.POP.TOTL CSV ZIP (defaults to the bundled snapshot)",
    )
    args = parser.parse_args()

    with ZipFile(args.archive) as archive:
        [data_file] = [name for name in archive.namelist() if name.startswith("API_SP.POP.TOTL_") and name.endswith(".csv")]
        with TextIOWrapper(archive.open(data_file), encoding="utf-8-sig", newline="") as source:
            # The export begins with the data source and update date above the CSV header.
            for _ in range(4):
                next(source)
            records = {row["Country Code"]: row for row in csv.DictReader(source)}

    regions = [records[code] for code in REGION_CODES]
    years = sorted(year for year in regions[0] if year.isdigit() and int(year) >= 1990 and all(row[year] for row in regions))
    if not years:
        raise ValueError("The archive has no population data for all eight series from 1990 onward")

    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["year", *(row["Country Name"] for row in regions)])
    for year in years:
        writer.writerow([year, *(int(row[year]) for row in regions)])
    (DEMO / "world_population.csv").write_text(output.getvalue(), encoding="utf-8", newline="")


if __name__ == "__main__":
    main()
