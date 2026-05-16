import argparse
import csv
from pathlib import Path


CALENDAR_SOURCE = "calendar.csv"
LISTINGS_SOURCE = "listings.csv"
REVIEWS_SOURCE = "reviews.csv"

CALENDAR_TARGET = "calendar_summary_pk.csv"
LISTINGS_TARGET = "listings_summary.csv"
REVIEWS_TARGET = "reviews_summary.csv"

CALENDAR_COLS = [
    "listing_id",
    "date",
    "available",
    "price",
    "adjusted_price",
    "minimum_nights",
    "maximum_nights",
]

LISTINGS_COLS = [
    "id",
    "host_id",
    "latitude",
    "longitude",
    "room_type",
    "price",
    "minimum_nights",
    "number_of_reviews",
    "last_review",
    "reviews_per_month",
    "calculated_host_listings_count",
    "availability_365",
    "number_of_reviews_ltm",
]

REVIEWS_COLS = [
    "listing_id",
    "id",
    "date",
    "reviewer_id",
]

PRICE_COLUMNS = {"price", "adjusted_price"}


def sanitize_price(raw: str) -> str:
    if raw is None:
        return ""
    value = raw.strip()
    if value == "":
        return ""
    if value.startswith("$"):
        value = value[1:]
    return value.replace(",", "")


def get_value(row: dict, column: str) -> str:
    value = row.get(column, "")
    if value is None:
        return ""
    if column in PRICE_COLUMNS:
        return sanitize_price(value)
    return value.strip() if isinstance(value, str) else str(value)


def require_columns(reader: csv.DictReader, required: list, source_name: str) -> None:
    if reader.fieldnames is None:
        raise ValueError(f"{source_name} has no header row")
    missing = [c for c in required if c not in reader.fieldnames]
    if missing:
        raise ValueError(f"{source_name} missing columns: {missing}")


def transform_calendar(source: Path, target: Path) -> int:
    written = 0
    with source.open("r", encoding="utf-8", newline="") as in_f, target.open("w", encoding="utf-8", newline="") as out_f:
        reader = csv.DictReader(in_f)
        require_columns(reader, CALENDAR_COLS, source.name)
        writer = csv.writer(out_f)
        next_id = 1
        for row in reader:
            values = [get_value(row, col) for col in CALENDAR_COLS]
            writer.writerow(values + [next_id])
            next_id += 1
            written += 1
    return written


def transform_listings(source: Path, target: Path) -> int:
    written = 0
    with source.open("r", encoding="utf-8", newline="") as in_f, target.open("w", encoding="utf-8", newline="") as out_f:
        reader = csv.DictReader(in_f)
        require_columns(reader, LISTINGS_COLS, source.name)
        writer = csv.writer(out_f)
        for row in reader:
            values = [get_value(row, col) for col in LISTINGS_COLS]
            writer.writerow(values)
            written += 1
    return written


def transform_reviews(source: Path, target: Path) -> int:
    written = 0
    skipped = 0
    with source.open("r", encoding="utf-8", newline="") as in_f, target.open("w", encoding="utf-8", newline="") as out_f:
        reader = csv.DictReader(in_f)
        require_columns(reader, REVIEWS_COLS, source.name)
        writer = csv.writer(out_f)
        for row in reader:
            values = [get_value(row, col) for col in REVIEWS_COLS]
            # Skip malformed rows where key columns are empty.
            if values[0] == "" or values[1] == "":
                skipped += 1
                continue
            writer.writerow(values)
            written += 1
    if skipped > 0:
        print(f"reviews: skipped malformed rows = {skipped}")
    return written


def maybe_remove(path: Path, overwrite: bool) -> None:
    if path.exists():
        if not overwrite:
            raise FileExistsError(
                f"Target exists: {path}. Re-run with --overwrite to replace it."
            )
        path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare Airbnb CSVs for FAAQP schema")
    parser.add_argument("--input_dir", default="./airbnb-benchmark")
    parser.add_argument("--output_dir", default="./airbnb-benchmark")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    calendar_src = input_dir / CALENDAR_SOURCE
    listings_src = input_dir / LISTINGS_SOURCE
    reviews_src = input_dir / REVIEWS_SOURCE

    calendar_dst = output_dir / CALENDAR_TARGET
    listings_dst = output_dir / LISTINGS_TARGET
    reviews_dst = output_dir / REVIEWS_TARGET

    for src in (calendar_src, listings_src, reviews_src):
        if not src.exists():
            raise FileNotFoundError(f"Missing source file: {src}")

    output_dir.mkdir(parents=True, exist_ok=True)
    maybe_remove(calendar_dst, args.overwrite)
    maybe_remove(listings_dst, args.overwrite)
    maybe_remove(reviews_dst, args.overwrite)

    calendar_count = transform_calendar(calendar_src, calendar_dst)
    listings_count = transform_listings(listings_src, listings_dst)
    reviews_count = transform_reviews(reviews_src, reviews_dst)

    print("Prepared files:")
    print(f"- {calendar_dst} rows={calendar_count}")
    print(f"- {listings_dst} rows={listings_count}")
    print(f"- {reviews_dst} rows={reviews_count}")


if __name__ == "__main__":
    main()
