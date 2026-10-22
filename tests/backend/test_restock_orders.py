"""
Tests for restock order endpoints and the demand forecast cost fields.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def clear_restock_orders():
    """Restock orders live in memory; isolate each test."""
    main.restock_orders.clear()
    yield
    main.restock_orders.clear()


def make_item(sku="WDG-001", quantity=10, unit_cost=42.5, lead_time_days=14):
    return {
        "item_sku": sku,
        "item_name": f"Item {sku}",
        "quantity": quantity,
        "unit_cost": unit_cost,
        "lead_time_days": lead_time_days,
    }


class TestDemandCostFields:
    def test_demand_includes_cost_and_lead_time(self, client):
        response = client.get("/api/demand")
        assert response.status_code == 200
        for forecast in response.json():
            assert forecast["unit_cost"] > 0
            assert forecast["supplier"]
            assert forecast["lead_time_days"] > 0


class TestCreateRestockOrder:
    def test_create_valid_order(self, client):
        payload = {
            "budget": 1000,
            "items": [make_item("A", 10, 10.0, 5), make_item("B", 5, 20.0, 12)],
        }
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 201
        order = response.json()
        assert order["order_number"] == "RST-0001"
        assert order["status"] == "Submitted"
        assert order["total_cost"] == 200.0
        assert order["lead_time_days"] == 12
        assert order["expected_delivery"] >= order["submitted_date"]

    def test_empty_items_rejected(self, client):
        response = client.post("/api/restock-orders", json={"budget": 100, "items": []})
        assert response.status_code == 400

    def test_non_positive_quantity_rejected(self, client):
        payload = {"budget": 100, "items": [make_item(quantity=0)]}
        assert client.post("/api/restock-orders", json=payload).status_code == 400

    def test_over_budget_rejected(self, client):
        payload = {"budget": 100, "items": [make_item(quantity=10, unit_cost=50.0)]}
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 400
        assert "budget" in response.json()["detail"].lower()

    def test_exact_budget_allowed(self, client):
        payload = {"budget": 100, "items": [make_item(quantity=10, unit_cost=10.0)]}
        assert client.post("/api/restock-orders", json=payload).status_code == 201

    def test_invalid_body_rejected(self, client):
        assert client.post("/api/restock-orders", json={"budget": 100}).status_code == 422


class TestListRestockOrders:
    def test_empty_list(self, client):
        response = client.get("/api/restock-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_newest_first(self, client):
        for _ in range(2):
            client.post("/api/restock-orders", json={"budget": 500, "items": [make_item()]})
        orders = client.get("/api/restock-orders").json()
        assert [o["order_number"] for o in orders] == ["RST-0002", "RST-0001"]
