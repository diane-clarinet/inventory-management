"""
Tests for the tasks and purchase order endpoints.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def reset_state():
    """Tasks and purchase orders live in memory; isolate each test."""
    original_pos = list(main.purchase_orders)
    main.tasks.clear()
    yield
    main.tasks.clear()
    main.purchase_orders[:] = original_pos


def make_task(title="Check stock", priority="high", due="2025-12-01"):
    return {"title": title, "priority": priority, "dueDate": due}


def make_po(backlog_item_id="1", quantity=100, unit_cost=2.5):
    return {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Supply",
        "quantity": quantity,
        "unit_cost": unit_cost,
        "expected_delivery_date": "2025-12-15",
        "notes": "rush",
    }


class TestTasks:
    def test_empty_list(self, client):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        response = client.post("/api/tasks", json=make_task())
        assert response.status_code == 201
        task = response.json()
        assert task["title"] == "Check stock"
        assert task["status"] == "pending"
        assert task["id"] >= main.TASK_ID_START

    def test_blank_title_rejected(self, client):
        assert client.post("/api/tasks", json=make_task(title="   ")).status_code == 400

    def test_newest_first(self, client):
        client.post("/api/tasks", json=make_task("first"))
        client.post("/api/tasks", json=make_task("second"))
        titles = [t["title"] for t in client.get("/api/tasks").json()]
        assert titles == ["second", "first"]

    def test_toggle_task(self, client):
        task_id = client.post("/api/tasks", json=make_task()).json()["id"]
        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "completed"
        assert client.patch(f"/api/tasks/{task_id}").json()["status"] == "pending"

    def test_delete_task(self, client):
        task_id = client.post("/api/tasks", json=make_task()).json()["id"]
        assert client.delete(f"/api/tasks/{task_id}").status_code == 200
        assert client.get("/api/tasks").json() == []

    def test_unknown_task_404(self, client):
        assert client.patch("/api/tasks/999999").status_code == 404
        assert client.delete("/api/tasks/999999").status_code == 404


class TestPurchaseOrders:
    def test_create_and_fetch(self, client):
        response = client.post("/api/purchase-orders", json=make_po())
        assert response.status_code == 201
        po = response.json()
        assert po["status"] == "Pending"
        assert po["backlog_item_id"] == "1"

        fetched = client.get("/api/purchase-orders/1")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == po["id"]

    def test_backlog_reports_purchase_order(self, client):
        po_id = client.post("/api/purchase-orders", json=make_po("1")).json()["id"]
        backlog = {b["id"]: b for b in client.get("/api/backlog").json()}
        assert backlog["1"]["has_purchase_order"] is True
        assert backlog["1"]["purchase_order_id"] == po_id
        assert backlog["2"]["purchase_order_id"] is None

    def test_unknown_backlog_item_404(self, client):
        assert client.post("/api/purchase-orders", json=make_po("nope")).status_code == 404

    def test_duplicate_rejected(self, client):
        client.post("/api/purchase-orders", json=make_po())
        assert client.post("/api/purchase-orders", json=make_po()).status_code == 409

    def test_non_positive_quantity_rejected(self, client):
        assert client.post("/api/purchase-orders", json=make_po(quantity=0)).status_code == 400

    def test_get_missing_404(self, client):
        assert client.get("/api/purchase-orders/1").status_code == 404
