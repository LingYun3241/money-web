"""账目接口测试：全部运行在独立测试库 expense_tracker_test。"""

from decimal import Decimal

import pytest

from app.models import CATEGORIES

BASE_PAYLOAD = {
    "amount": "12.50",
    "category": "餐饮",
    "record_date": "2026-11-17",
    "note": "测试备注",
}


def post_record(client, **overrides):
    payload = {**BASE_PAYLOAD, **overrides}
    return client.post("/api/records", json=payload)


def get_records(client):
    response = client.get("/api/records")
    assert response.status_code == 200
    return response.json()


def get_stats(client):
    response = client.get("/api/statistics")
    assert response.status_code == 200
    return response.json()


def test_health_reports_database_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "expense-tracker"
    assert body["database"] == "ok"


def test_empty_list_and_zero_filled_statistics(client):
    assert get_records(client) == []

    stats = get_stats(client)
    assert stats["total_amount"] == "0.00"
    assert stats["total_count"] == 0
    assert [item["category"] for item in stats["categories"]] == list(CATEGORIES)
    assert all(item["amount"] == "0.00" for item in stats["categories"])


def test_create_then_list_and_statistics(client):
    response = post_record(client)
    assert response.status_code == 201
    created = response.json()
    assert isinstance(created["id"], int)
    assert created["amount"] == "12.50"
    assert created["category"] == "餐饮"
    assert created["record_date"] == "2026-11-17"
    assert created["note"] == "测试备注"

    records = get_records(client)
    assert len(records) == 1
    assert records[0] == created

    stats = get_stats(client)
    assert stats["total_amount"] == "12.50"
    assert stats["total_count"] == 1
    by_category = {item["category"]: item["amount"] for item in stats["categories"]}
    assert by_category["餐饮"] == "12.50"
    assert by_category["交通"] == "0.00"


@pytest.mark.parametrize(
    "amount",
    ["0", "-0.01", "0.001", "1.234", "abc", "100000000.00"],
    ids=["zero", "negative", "three-decimals-small", "three-decimals", "text", "too-many-digits"],
)
def test_invalid_amount_rejected(client, amount):
    response = post_record(client, amount=amount)
    assert response.status_code == 422
    assert get_records(client) == []
    assert get_stats(client)["total_count"] == 0


@pytest.mark.parametrize(
    "amount, expected",
    [("8", "8.00"), ("8.5", "8.50"), ("99999999.99", "99999999.99")],
    ids=["integer", "one-decimal", "max-value"],
)
def test_amount_normalized_to_two_decimals(client, amount, expected):
    response = post_record(client, amount=amount)
    assert response.status_code == 201
    assert response.json()["amount"] == expected


@pytest.mark.parametrize("category", ["医疗", "餐饮 ", "", "food"])
def test_invalid_category_rejected(client, category):
    response = post_record(client, category=category)
    assert response.status_code == 422
    assert get_records(client) == []


@pytest.mark.parametrize("record_date", ["2026-13-01", "2026-02-30", "2026/11/17", ""])
def test_invalid_date_rejected(client, record_date):
    response = post_record(client, record_date=record_date)
    assert response.status_code == 422
    assert get_records(client) == []


def test_empty_and_omitted_note_allowed(client):
    response = post_record(client, note="")
    assert response.status_code == 201
    assert response.json()["note"] == ""

    payload = {key: value for key, value in BASE_PAYLOAD.items() if key != "note"}
    response = client.post("/api/records", json=payload)
    assert response.status_code == 201
    assert response.json()["note"] == ""


def test_note_length_boundary(client):
    response = post_record(client, note="备" * 255)
    assert response.status_code == 201
    assert response.json()["note"] == "备" * 255

    response = post_record(client, note="备" * 256)
    assert response.status_code == 422
    assert len(get_records(client)) == 1


def test_unknown_field_rejected(client):
    response = post_record(client, unexpected="x")
    assert response.status_code == 422
    assert get_records(client) == []


def test_missing_required_field_rejected(client):
    response = client.post(
        "/api/records",
        json={"category": "餐饮", "record_date": "2026-11-17"},
    )
    assert response.status_code == 422
    assert get_records(client) == []


def test_list_order_is_date_then_id_descending(client):
    assert post_record(client, category="餐饮", record_date="2026-11-16").status_code == 201
    assert post_record(client, category="交通", record_date="2026-11-17").status_code == 201
    assert post_record(client, category="购物", record_date="2026-11-17").status_code == 201

    records = get_records(client)
    assert [item["category"] for item in records] == ["购物", "交通", "餐饮"]


def test_statistics_cover_all_six_categories(client):
    amounts = ["1", "2", "3", "4", "5", "6"]
    for category, amount in zip(CATEGORIES, amounts):
        assert post_record(client, category=category, amount=amount).status_code == 201

    stats = get_stats(client)
    assert stats["total_amount"] == "21.00"
    assert stats["total_count"] == 6
    assert [item["category"] for item in stats["categories"]] == list(CATEGORIES)
    assert [item["amount"] for item in stats["categories"]] == [
        "1.00",
        "2.00",
        "3.00",
        "4.00",
        "5.00",
        "6.00",
    ]


def test_delete_record_and_repeat_delete_returns_404(client):
    created = post_record(client).json()
    record_id = created["id"]

    response = client.delete(f"/api/records/{record_id}")
    assert response.status_code == 204
    assert response.content == b""
    assert get_records(client) == []
    assert get_stats(client)["total_count"] == 0

    response = client.delete(f"/api/records/{record_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "记录不存在"


def test_delete_missing_id_returns_404(client):
    response = client.delete("/api/records/999999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "记录不存在"


def test_delete_only_removes_target_row(client):
    first = post_record(client, category="餐饮", amount="10").json()
    second = post_record(client, category="交通", amount="20").json()

    assert client.delete(f"/api/records/{first['id']}").status_code == 204

    records = get_records(client)
    assert len(records) == 1
    assert records[0]["id"] == second["id"]
    stats = get_stats(client)
    assert stats["total_amount"] == "20.00"
    assert stats["total_count"] == 1


def test_note_with_sql_special_characters_is_stored_literally(client):
    note = "x'); DELETE FROM records; -- 测试🧪"
    response = post_record(client, note=note)
    assert response.status_code == 201
    assert response.json()["note"] == note

    records = get_records(client)
    assert len(records) == 1
    assert records[0]["note"] == note
    assert get_stats(client)["total_count"] == 1


def test_statistics_total_matches_decimal_sum(client):
    assert post_record(client, amount="0.10").status_code == 201
    assert post_record(client, amount="0.20").status_code == 201

    stats = get_stats(client)
    assert Decimal(stats["total_amount"]) == Decimal("0.30")
    assert stats["total_amount"] == "0.30"
