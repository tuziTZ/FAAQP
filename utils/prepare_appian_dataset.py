import argparse
import csv
from datetime import date, datetime
from pathlib import Path


EPOCH_DATE = date(1970, 1, 1)
NULL_VARCHAR_SENTINEL = "__NULL__"

APPian_TABLES = [
    {
        "source": "addressview.csv",
        "target": "addressview.csv",
        "columns": [
            ("address_id", "bigint"),
            ("address_street", "varchar"),
            ("address_city", "varchar"),
            ("address_state", "varchar"),
            ("address_zip", "integer"),
            ("address_zipPrefix", "integer"),
            ("address_customerId", "bigint"),
            ("address_valuation", "bigint"),
            ("address_zone", "smallint"),
            ("address_rating", "double"),
            ("address_lastSupportSession", "timestamp"),
            ("address_occupancyDate", "date"),
            ("address_supportTime", "time"),
        ],
    },
    {
        "source": "categoryview.csv",
        "target": "categoryview.csv",
        "columns": [
            ("category_name", "varchar"),
            ("category_shortName", "varchar"),
            ("category_perishable", "boolean"),
            ("category_seasonal", "boolean"),
            ("category_demandScore", "smallint"),
            ("category_valuation", "bigint"),
            ("category_warehouseSqft", "integer"),
            ("category_warehouseClosing", "time"),
            ("category_regulationProbability", "double"),
            ("category_auditDate", "date"),
            ("category_auditDeadline", "timestamp"),
        ],
    },
    {
        "source": "creditcardview.csv",
        "target": "creditcardview.csv",
        "columns": [
            ("creditCard_number", "varchar"),
            ("creditCard_holder", "varchar"),
            ("creditCard_expirationDate", "date"),
            ("creditCard_customerId", "bigint"),
            ("creditCard_zip", "integer"),
            ("creditCard_cvv", "smallint"),
            ("creditCard_lastChargeAmount", "double"),
            ("creditCard_lastChargeTimestamp", "timestamp"),
            ("creditCard_lastChargeTime", "time"),
        ],
    },
    {
        "source": "customerview.csv",
        "target": "customerview.csv",
        "columns": [
            ("customer_id", "bigint"),
            ("customer_name", "varchar"),
            ("customer_registrationDate", "date"),
            ("customer_priority", "smallint"),
            ("customer_age", "integer"),
            ("customer_onboardGroup", "bigint"),
            ("customer_balance", "double"),
            ("customer_lastLogin", "timestamp"),
            ("customer_alertTime", "time"),
            ("customer_customerId", "bigint"),
        ],
    },
    {
        "source": "orderview.csv",
        "target": "orderview.csv",
        "columns": [
            ("order_id", "bigint"),
            ("order_destination", "varchar"),
            ("order_placedOn", "timestamp"),
            ("order_isExpeditedShipped", "boolean"),
            ("order_subShipments", "integer"),
            ("order_serverId", "smallint"),
            ("order_slaProbability", "double"),
            ("order_shipBy", "date"),
            ("order_inspectionTime", "time"),
            ("order_customerId", "bigint"),
            ("order_creditCardNumber", "varchar"),
        ],
    },
    {
        "source": "orderitemview.csv",
        "target": "orderitemview.csv",
        "columns": [
            ("orderItem_id", "bigint"),
            ("orderItem_supplierState", "varchar"),
            ("orderItem_productId", "bigint"),
            ("orderItem_quantity", "integer"),
            ("orderItem_sku", "smallint"),
            ("orderItem_productGroup", "bigint"),
            ("orderItem_weight", "double"),
            ("orderItem_alertAt", "time"),
            ("orderItem_discountExpiration", "timestamp"),
            ("orderItem_checkoutBy", "date"),
            ("orderItem_orderId", "bigint"),
        ],
    },
    {
        "source": "productview.csv",
        "target": "productview.csv",
        "columns": [
            ("product_id", "bigint"),
            ("product_name", "varchar"),
            ("product_price", "double"),
            ("product_categoryName", "varchar"),
            ("product_likes", "bigint"),
            ("product_inventory", "integer"),
            ("product_backorderThreshold", "smallint"),
            ("product_inventoryLastChecked", "timestamp"),
            ("product_inventoryLastOrderedOn", "date"),
            ("product_inventoryAlertAt", "time"),
        ],
    },
    {
        "source": "taxrecordview.csv",
        "target": "taxrecordview.csv",
        "columns": [
            ("taxRecord_id", "bigint"),
            ("taxRecord_state", "varchar"),
            ("taxRecord_value", "double"),
            ("taxRecord_rate", "double"),
            ("taxRecord_constructionDate", "date"),
            ("taxRecord_bracket", "smallint"),
            ("taxRecord_ein", "integer"),
            ("taxRecord_bracketThreshold", "bigint"),
            ("taxRecord_lastPayment", "timestamp"),
            ("taxRecord_scheduledPaymentTime", "time"),
            ("taxRecord_addressId", "bigint"),
        ],
    },
]


def require_columns(reader: csv.DictReader, required_columns, source_name: str) -> None:
    if reader.fieldnames is None:
        raise ValueError(f"{source_name} has no header row")
    missing = [column for column, _ in required_columns if column not in reader.fieldnames]
    if missing:
        raise ValueError(f"{source_name} missing columns: {missing}")


def normalize_boolean(value: str) -> str:
    lowered = value.strip().lower()
    if lowered == "true":
        return "1"
    if lowered == "false":
        return "0"
    raise ValueError(f"Unsupported boolean value: {value}")


def normalize_date(value: str) -> str:
    parsed = date.fromisoformat(value.strip())
    return str((parsed - EPOCH_DATE).days)


def normalize_time(value: str) -> str:
    parsed = datetime.strptime(value.strip(), "%H:%M:%S").time()
    return str(parsed.hour * 3600 + parsed.minute * 60 + parsed.second)


def normalize_timestamp(value: str) -> str:
    raw_value = value.strip()
    if "." not in raw_value:
        raw_value = raw_value + ".0"
    parsed = datetime.strptime(raw_value, "%Y-%m-%d %H:%M:%S.%f")
    return str(int(parsed.timestamp()))


def normalize_credit_card_number(value: str) -> str:
    return value


def load_category_mapping(input_dir: Path) -> dict:
    category_file = input_dir / "categoryview.csv"
    mapping = {}
    with category_file.open("r", encoding="utf-8", newline="") as in_f:
        reader = csv.DictReader(in_f)
        require_columns(reader, [("category_name", "varchar")], category_file.name)
        next_id = 1
        for row in reader:
            category_name = row.get("category_name", "")
            if category_name is None:
                continue
            normalized_name = category_name.strip()
            if normalized_name == "":
                continue
            if normalized_name not in mapping:
                mapping[normalized_name] = str(next_id)
                next_id += 1
    return mapping


def load_credit_card_mapping(input_dir: Path) -> dict:
    mapping = {}
    next_id = 1
    for file_name, column_name in [
        ("creditcardview.csv", "creditCard_number"),
        ("orderview.csv", "order_creditCardNumber"),
    ]:
        source_file = input_dir / file_name
        with source_file.open("r", encoding="utf-8", newline="") as in_f:
            reader = csv.DictReader(in_f)
            require_columns(reader, [(column_name, "varchar")], source_file.name)
            for row in reader:
                raw_value = row.get(column_name, "")
                if raw_value is None:
                    continue
                normalized_value = raw_value.strip()
                if normalized_value == "":
                    continue
                if normalized_value not in mapping:
                    mapping[normalized_value] = str(next_id)
                    next_id += 1
    return mapping


def normalize_value(
    value: str,
    column_type: str,
    column_name: str,
    category_mapping: dict,
    credit_card_mapping: dict,
) -> str:
    if value is None:
        if column_type == "varchar":
            return NULL_VARCHAR_SENTINEL
        return ""

    stripped = value.strip()
    if stripped == "":
        if column_type == "varchar":
            return NULL_VARCHAR_SENTINEL
        return ""

    if column_name in {"creditCard_number", "order_creditCardNumber"}:
        return credit_card_mapping[stripped]
    if column_name in {"category_name", "product_categoryName"}:
        return category_mapping[stripped]
    if column_type == "boolean":
        return normalize_boolean(stripped)
    if column_type == "date":
        return normalize_date(stripped)
    if column_type == "time":
        return normalize_time(stripped)
    if column_type == "timestamp":
        return normalize_timestamp(stripped)
    return stripped


def maybe_remove(path: Path, overwrite: bool) -> None:
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"Target exists: {path}. Re-run with --overwrite to replace it.")
        path.unlink()


def transform_table(
    input_dir: Path,
    output_dir: Path,
    table_spec: dict,
    category_mapping: dict,
    credit_card_mapping: dict,
) -> int:
    source = input_dir / table_spec["source"]
    target = output_dir / table_spec["target"]

    if not source.exists():
        raise FileNotFoundError(f"Missing source file: {source}")

    maybe_remove(target, overwrite=True)

    written = 0
    with source.open("r", encoding="utf-8", newline="") as in_f, target.open(
        "w", encoding="utf-8", newline=""
    ) as out_f:
        reader = csv.DictReader(in_f)
        require_columns(reader, table_spec["columns"], source.name)
        writer = csv.writer(out_f)

        for row in reader:
            normalized_row = [
                normalize_value(
                    row.get(column_name, ""),
                    column_type,
                    column_name,
                    category_mapping,
                    credit_card_mapping,
                )
                for column_name, column_type in table_spec["columns"]
            ]
            writer.writerow(normalized_row)
            written += 1

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare Appian CSVs for FAAQP schema")
    parser.add_argument("--input_dir", default="./appian-benchmark")
    parser.add_argument("--output_dir", default="./appian-benchmark/prepared")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Missing input directory: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    category_mapping = load_category_mapping(input_dir)
    credit_card_mapping = load_credit_card_mapping(input_dir)

    if not args.overwrite:
        for table_spec in APPian_TABLES:
            target = output_dir / table_spec["target"]
            if target.exists():
                raise FileExistsError(f"Target exists: {target}. Re-run with --overwrite to replace it.")

    counts = {}
    for table_spec in APPian_TABLES:
        if args.overwrite:
            maybe_remove(output_dir / table_spec["target"], overwrite=True)
        counts[table_spec["target"]] = transform_table(
            input_dir,
            output_dir,
            table_spec,
            category_mapping,
            credit_card_mapping,
        )

    print("Prepared files:")
    for file_name, row_count in counts.items():
        print(f"- {output_dir / file_name} rows={row_count}")


if __name__ == "__main__":
    main()
