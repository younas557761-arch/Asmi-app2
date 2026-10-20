def _mk_student(c, n):
    r = c.post(
        "/api/v1/students",
        json={"admission_number": f"ADM-{n}", "first_name": f"Student{n}"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _mk_invoice(c, sid, title="Monthly Fee", amount=5000):
    r = c.post(
        "/api/v1/fees/invoices",
        json={
            "student_id": sid,
            "title": title,
            "items": [{"description": "Tuition", "amount": amount}],
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_invoice_and_partial_payment_flow(owner_client):
    c = owner_client
    sid = _mk_student(c, 1)
    inv = _mk_invoice(c, sid)
    assert inv["total"] == 5000 and inv["status"] == "unpaid" and inv["balance"] == 5000

    # partial payment
    r = c.post(
        "/api/v1/fees/payments",
        json={"student_id": sid, "invoice_id": inv["id"], "amount": 2000, "method": "cash"},
    )
    assert r.status_code == 201, r.text

    r = c.get(f"/api/v1/fees/invoices/{inv['id']}")
    assert r.json()["paid"] == 2000
    assert r.json()["balance"] == 3000
    assert r.json()["status"] == "partial"

    # overpayment rejected
    r = c.post(
        "/api/v1/fees/payments",
        json={"student_id": sid, "invoice_id": inv["id"], "amount": 9999},
    )
    assert r.status_code == 422

    # full payment closes the invoice
    c.post(
        "/api/v1/fees/payments",
        json={"student_id": sid, "invoice_id": inv["id"], "amount": 3000},
    )
    r = c.get(f"/api/v1/fees/invoices/{inv['id']}")
    assert r.json()["status"] == "paid" and r.json()["balance"] == 0


def test_waiver_covers_balance(owner_client):
    c = owner_client
    sid = _mk_student(c, 2)
    inv = _mk_invoice(c, sid, amount=1000)
    r = c.post(
        "/api/v1/fees/adjustments",
        json={"student_id": sid, "invoice_id": inv["id"], "kind": "waiver", "amount": 1000, "reason": "Staff child"},
    )
    assert r.status_code == 201, r.text
    r = c.get(f"/api/v1/fees/invoices/{inv['id']}")
    assert r.json()["waived"] == 1000 and r.json()["status"] == "paid"


def test_balances_report(owner_client):
    c = owner_client
    sid1 = _mk_student(c, 3)
    sid2 = _mk_student(c, 4)
    _mk_invoice(c, sid1, amount=5000)
    c.post(
        "/api/v1/fees/payments",
        json={"student_id": sid1, "amount": 2000},
    )
    rows = c.get("/api/v1/fees/balances").json()["items"]
    by_id = {r["student_id"]: r for r in rows}
    assert by_id[sid1]["balance"] == 3000
    assert by_id[sid2]["balance"] == 0


def test_ledger_is_append_only(owner_client):
    c = owner_client
    sid = _mk_student(c, 5)
    _mk_invoice(c, sid, amount=500)
    c.post("/api/v1/fees/payments", json={"student_id": sid, "amount": 500})
    payments = c.get(f"/api/v1/fees/payments?student_id={sid}").json()["items"]
    pid = payments[0]["id"]
    # no update or delete endpoints exist for ledger entries
    assert c.patch(f"/api/v1/fees/payments/{pid}", json={"amount": 1}).status_code == 405
    assert c.delete(f"/api/v1/fees/payments/{pid}").status_code == 405


def test_fees_cross_school_isolated(owner_client, other_owner_client):
    sid = _mk_student(owner_client, 6)
    inv = _mk_invoice(owner_client, sid)
    assert other_owner_client.get("/api/v1/fees/invoices").json()["total"] == 0
    r = other_owner_client.post(
        "/api/v1/fees/payments",
        json={"student_id": sid, "invoice_id": inv["id"], "amount": 100},
    )
    assert r.status_code == 404
