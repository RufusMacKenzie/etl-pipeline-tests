import copy
import pytest
import pytest_check as check

from src.transformer import transform

MOCK_ORDER = {
    "order_id": "1001",
    "customer_id": "501",
    "order_date": "2025-01-15",
    "product_id": "SKU-TEST001",
    "quantity": "1",
    "unit_price": "100.00",
    "discount_amount": "0.00",
    "order_total": "100.00",
    "promo_code": "",
    "status": "Fulfilled",
    "previous_status": "Shipped",
    "last_updated": "2025-01-20 10:00:00",
    "email": "test@example.com",
}

MOCK_PROMOTIONS = [
    {
        "promo_code": "TEST10",
        "description": "Test promo",
        "discount_type": "percent",
        "discount_value": "10.0",
        "valid_from": "2025-01-01",
        "valid_to": "",
    },
    {
        "promo_code": "BOGO",
        "description": "Test promo",
        "discount_type": "percent",
        "discount_value": "50.0",
        "valid_from": "2025-02-01",
        "valid_to": "",
    },
]


def test_good_order_and_good_promotion():
    order = copy.deepcopy(MOCK_ORDER)
    promotions = copy.deepcopy(MOCK_PROMOTIONS)

    result = transform([order], promotions)
    assert len(result["invalid"]) == 0
    assert len(result["valid"]) == 1


def test_malformed_date_in_promotion_valid_to_raises_error():
    order = copy.deepcopy(MOCK_ORDER)
    bad_promotions = copy.deepcopy(MOCK_PROMOTIONS)
    bad_promotions[0]["valid_to"] = "205-03-04"

    with pytest.raises(ValueError):
        transform([order], bad_promotions)


def test_malformed_date_in_promotion_valid_from_raises_error():
    order = copy.deepcopy(MOCK_ORDER)
    bad_promotions = copy.deepcopy(MOCK_PROMOTIONS)
    bad_promotions[0]["valid_from"] = "2025-13-04"

    with pytest.raises(ValueError):
        transform([order], bad_promotions)


@pytest.mark.parametrize(
    "promo_code",
    [
        None,
        "",
    ],
)
def test_missing_promo_code_in_promotion_raises_error(promo_code):
    order = copy.deepcopy(MOCK_ORDER)
    bad_promotions = copy.deepcopy(MOCK_PROMOTIONS)
    bad_promotions[0]["promo_code"] = promo_code

    with pytest.raises(ValueError):
        transform([order], bad_promotions)


def test_promotion_valid_from_none_raises_error():
    order = copy.deepcopy(MOCK_ORDER)
    bad_promotions = copy.deepcopy(MOCK_PROMOTIONS)
    bad_promotions[0]["valid_from"] = None

    with pytest.raises(ValueError):
        transform([order], bad_promotions)


def test_promotion_valid_to_before_valid_from_raises_error():
    order = copy.deepcopy(MOCK_ORDER)
    bad_promotions = copy.deepcopy(MOCK_PROMOTIONS)
    bad_promotions[0]["valid_from"] = "2025-12-31"
    bad_promotions[0]["valid_to"] = "2025-12-15"

    with pytest.raises(ValueError):
        transform([order], bad_promotions)


def test_negative_quantity():
    order = copy.deepcopy(MOCK_ORDER)
    order["quantity"] = "-1"
    promotions = copy.deepcopy(MOCK_PROMOTIONS)

    result = transform([order], promotions)
    assert len(result["invalid"]) == 1
    assert len(result["valid"]) == 0


def test_order_with_promo_used_before_promo_valid_from():
    order = copy.deepcopy(MOCK_ORDER)
    order["order_date"] = "2025-11-22"
    order["promo_code"] = "TEST10"
    promotions = copy.deepcopy(MOCK_PROMOTIONS)
    promotions[0]["promo_code"] = "TEST10"
    promotions[0]["valid_from"] = "2025-11-30"

    result = transform([order], promotions)
    assert len(result["invalid"]) == 1
    assert len(result["valid"]) == 0


def test_order_with_promo_used_after_promo_valid_to():
    order = copy.deepcopy(MOCK_ORDER)
    order["order_date"] = "2025-11-22"
    order["promo_code"] = "TEST10"
    promotions = copy.deepcopy(MOCK_PROMOTIONS)
    promotions[0]["promo_code"] = "TEST10"
    promotions[0]["valid_to"] = "2025-11-01"

    result = transform([order], promotions)
    assert len(result["invalid"]) == 1
    assert len(result["valid"]) == 0
