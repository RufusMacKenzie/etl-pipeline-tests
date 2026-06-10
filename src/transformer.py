import datetime
import re

from src.constants import ROUNDING_TOLERANCE

# transformer constants
VALID_FIELDS = {
    "order_id",
    "customer_id",
    "order_date",
    "product_id",
    "quantity",
    "unit_price",
    "discount_amount",
    "order_total",
    "promo_code",
    "status",
    "previous_status",
    "last_updated",
    "email",
}

NULLABLE_FIELDS = {
    "promo_code",
    "previous_status",
}

VALID_STATUSES = {
    "Submitted",
    "Approved",
    "Shipped",
    "Fulfilled",
    "Cancelled",
    "Held for Review",
}

VALUE_RANGES = {
    "quantity": (1, None),  # min 1, no max
    "unit_price": (0.01, None),  # min 0.01, no max
    "discount_amount": (0, None),  # min 0, no max
}

VALID_STATUS_PROGRESSIONS = {
    "Submitted": {None, ""},  # first status, no previous
    "Approved": {"Submitted", "Held for Review"},
    "Shipped": {"Approved"},
    "Fulfilled": {"Shipped"},
    "Cancelled": {"Submitted", "Approved", "Held for Review"},
    "Held for Review": {"Submitted"},
}

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


# Helper functions
def _is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email)) if email else False


def _parse_date(value):
    return datetime.date.fromisoformat(value)


def _parse_datetime(value):
    return datetime.datetime.fromisoformat(value)


TYPE_MAP = {
    "order_id": int,
    "customer_id": int,
    "order_date": _parse_date,
    "quantity": int,
    "unit_price": float,
    "discount_amount": float,
    "order_total": float,
    "last_updated": _parse_datetime,
}


def _build_promo_lookup(promotions: list[dict]) -> dict:
    lookup = {}
    for promo in promotions:
        try:
            lookup[promo["promo_code"]] = {
                **promo,
                "valid_from": _parse_date(promo["valid_from"]),
                "valid_to": _parse_date(promo["valid_to"])
                if promo["valid_to"]
                else None,
            }
        except (ValueError, TypeError, KeyError) as e:
            raise ValueError(f"Invalid promotions data: {e}") from e
    return lookup


def _convert_types(record: dict) -> tuple[dict, list[str]]:
    # attempts type conversions, returns converted record + any errors
    converted = {}
    errors = []
    for field, value in record.items():
        if field is None:
            continue  # skip unnamed columns

        if field in TYPE_MAP:
            # attempt expected conversion
            try:
                converted[field] = TYPE_MAP[field](value)
            except (ValueError, TypeError):
                converted[field] = None
                type_name = TYPE_MAP[field].__name__.replace("_parse_", "")
                errors.append(f"{field} must be a valid {type_name}")
        else:
            # string field - just copy as-is
            converted[field] = value

    return converted, errors


def _check_required_fields(record: dict) -> list[str]:
    # returns list of error messages for missing required fields
    errors = []
    missing = VALID_FIELDS - record.keys()
    if missing:
        errors.append(f"Missing expected fields: {missing}")

    empty = {
        field
        for field in VALID_FIELDS - NULLABLE_FIELDS
        if record.get(field) is None or record.get(field) == ""
    }
    if empty:
        errors.append(f"Required fields are missing values: {empty}")

    return errors


def _check_value_ranges(record: dict) -> list[str]:
    # returns list of error messages for out-of-range values
    errors = []
    for field, (min_val, max_val) in VALUE_RANGES.items():
        if field not in record:
            continue
        value = record[field]
        if value is None:
            continue  # already caught by required fields check
        if min_val is not None and value < min_val:
            errors.append(f"{field}={value} is below minimum {min_val}")
        if max_val is not None and value > max_val:
            errors.append(f"{field}={value} is above maximum {max_val}")

    status = record.get("status")
    if status and status not in VALID_STATUSES:
        errors.append(f"'{status}' is not a valid status")

    order_date = record.get("order_date")
    if order_date and order_date > datetime.date.today():
        errors.append(f"order_date {order_date} cannot be in the future")

    email = record.get("email")
    if email and not _is_valid_email(email):
        errors.append(f"'{email}' is not a valid email address")

    return errors


def _check_business_rules(record: dict, promo_lookup: dict) -> list[str]:
    # returns list of error messages for business rule violations
    errors = []

    # Verify order values calculate correctly
    unit_price = record.get("unit_price")
    quantity = record.get("quantity")
    discount_amount = record.get("discount_amount")
    order_total = record.get("order_total")

    if all(v is not None for v in [unit_price, quantity, discount_amount, order_total]):
        calculated = (unit_price * quantity) - discount_amount
        if abs(calculated - order_total) > ROUNDING_TOLERANCE:
            errors.append(
                f"order total math error: expected {calculated:.2f}, got {order_total}"
            )
    else:
        errors.append(
            "cannot verify order total: one or more numeric fields failed type conversion"
        )

    # Ensure the current status came from a valid previous status
    status = record.get("status")
    if status in VALID_STATUS_PROGRESSIONS:  # only check if status is valid
        previous_status = record.get("previous_status")
        if previous_status not in VALID_STATUS_PROGRESSIONS[status]:
            errors.append(
                f"'{previous_status}' is not a valid previous status for '{status}'"
            )

    # Verify the promo code is valid and was active on the order date
    promo_code = record.get("promo_code")
    order_date = record.get("order_date")
    if promo_code and order_date:
        if promo_code in promo_lookup:
            promo_valid_from = promo_lookup.get(promo_code).get("valid_from")
            promo_valid_to = promo_lookup.get(promo_code).get("valid_to")

            if order_date < promo_valid_from:
                errors.append(
                    f"promo code '{promo_code}' was not yet valid on order date {order_date}"
                )
            elif promo_valid_to is not None and order_date > promo_valid_to:
                errors.append(
                    f"promo code '{promo_code}' had expired by order date {order_date}"
                )
        else:
            errors.append(f"promo code '{promo_code}' is not a valid promotion")

    # Verify there is a promo_code if there is a discount amount
    if discount_amount and not promo_code:
        errors.append(f"discount of {discount_amount} found with no promotion code")

    return errors


def transform(orders: list[dict], promotions: list[dict]) -> dict:
    # orchestrate the conversions and checks

    # convert list of promo records to a dict for fast lookup
    promo_lookup = _build_promo_lookup(promotions)

    valid_records = []
    invalid_records = []

    for record in orders:
        converted, errors = _convert_types(record)
        errors += _check_required_fields(converted)
        errors += _check_value_ranges(converted)
        errors += _check_business_rules(converted, promo_lookup)

        if errors:
            invalid_records.append({"record": record, "errors": errors})
        else:
            valid_records.append(converted)

    return {"valid": valid_records, "invalid": invalid_records}
