"""End-to-end flow verification script.

Run with the server already up:  python verify_flow.py
"""

import time
import json
import random
import string
import httpx
import asyncio
import websockets

BASE = "http://127.0.0.1:8000"
WS_BASE = "ws://127.0.0.1:8000"

SUFFIX = "".join(random.choices(string.digits, k=6))
USER_ID = f"U{SUFFIX}"
PASSWORD = "secret123"


def heading(step: str) -> None:
    print(f"\n{'='*60}\n  {step}\n{'='*60}")


def show(label: str, resp: httpx.Response) -> None:
    print(f"  [{resp.status_code}] {label}")
    print(f"  {json.dumps(resp.json(), indent=2)}")


print(f"\nTest user: {USER_ID}")

client = httpx.Client(base_url=BASE, timeout=10)

# ── 1. Health ──
heading("1. Health Check")
r = client.get("/health")
show("GET /health", r)
assert r.status_code == 200

# ── 2. Create User ──
heading("2. Create User")
r = client.post("/users", json={
    "user_id": USER_ID, "name": "Alice", "password": PASSWORD
})
show("POST /users", r)
assert r.status_code == 201

# ── 3. Duplicate User (should fail 409) ──
heading("3. Duplicate User (expect 409)")
r = client.post("/users", json={
    "user_id": USER_ID, "name": "Alice Again", "password": PASSWORD
})
show("POST /users (dup)", r)
assert r.status_code == 409

# ── 4. Login ──
heading("4. Login")
r = client.post("/auth/login", json={
    "user_id": USER_ID, "password": PASSWORD
})
show("POST /auth/login", r)
assert r.status_code == 200
token = r.json()["access_token"]
print(f"  Token: {token[:40]}...")

headers = {"Authorization": f"Bearer {token}"}

# ── 5. Login with wrong password (should fail 401) ──
heading("5. Login Wrong Password (expect 401)")
r = client.post("/auth/login", json={
    "user_id": USER_ID, "password": "wrong"
})
show("POST /auth/login (bad pw)", r)
assert r.status_code == 401

# ── 6. Get User ──
heading("6. Get User")
r = client.get(f"/users/{USER_ID}", headers=headers)
show(f"GET /users/{USER_ID}", r)
assert r.status_code == 200

# ── 7. Update User ──
heading("7. Update User")
r = client.put(f"/users/{USER_ID}", headers=headers, json={"name": "Alice Updated"})
show(f"PUT /users/{USER_ID}", r)
assert r.status_code == 200
assert r.json()["name"] == "Alice Updated"

# ── 8. Get User without auth (should fail 401) ──
heading("8. No Auth (expect 401)")
r = client.get(f"/users/{USER_ID}")
show(f"GET /users/{USER_ID} (no auth)", r)
assert r.status_code == 401

# ── 9. Ingest IoT Data ──
heading("9. Ingest IoT Data (3 points)")
timestamps = []
for i in range(3):
    ts = time.time() - (300 - i * 100)
    timestamps.append(ts)
    r = client.post("/iot/data", headers=headers, json={
        "user_id": USER_ID,
        "metric_1": 25.0 + i * 10,
        "metric_2": 80.0 + i * 20,
        "metric_3": 5.0 + i,
        "timestamp": ts,
    })
    show(f"POST /iot/data (point {i+1})", r)
    assert r.status_code == 201

# ── 10. Duplicate Ingestion (should fail 409) ──
heading("10. Duplicate Ingestion (expect 409)")
r = client.post("/iot/data", headers=headers, json={
    "user_id": USER_ID,
    "metric_1": 99.0,
    "metric_2": 99.0,
    "metric_3": 99.0,
    "timestamp": timestamps[0],
})
show("POST /iot/data (dup ts)", r)
assert r.status_code == 409

# ── 11. Validation Failures ──
heading("11. Validation Failures (expect 422)")
r = client.post("/iot/data", headers=headers, json={
    "user_id": USER_ID,
    "metric_1": 999.0,
    "metric_2": 999.0,
    "metric_3": 1.0,
    "timestamp": time.time() + 99999,
})
show("POST /iot/data (bad values)", r)
assert r.status_code == 422
body = r.json()
assert body["error"] == "VALIDATION_ERROR"
assert "details" in body
assert len(body["details"]) == 3

# ── 12. Get Latest ──
heading("12. Get Latest")
r = client.get(f"/users/{USER_ID}/iot/latest", headers=headers)
show(f"GET /users/{USER_ID}/iot/latest", r)
assert r.status_code == 200

# ── 13. Get History ──
heading("13. Get History (limit=2)")
r = client.get(f"/users/{USER_ID}/iot/history?limit=2", headers=headers)
show(f"GET /users/{USER_ID}/iot/history", r)
assert r.status_code == 200
assert len(r.json()) == 2

# ── 14. Nonexistent User Data (should fail 404) ──
heading("14. Nonexistent User (expect 404)")
r = client.get("/users/GHOST/iot/latest", headers=headers)
show("GET /users/GHOST/iot/latest", r)
assert r.status_code == 404

# ── 15. WebSocket Ingest + Subscribe ──
heading("15. WebSocket Ingest + Subscribe")


async def test_websockets():
    ws_ts = time.time() - 5

    received = []

    async def subscriber():
        uri = f"{WS_BASE}/ws/subscribe?user_id={USER_ID}&token={token}"
        async with websockets.connect(uri) as ws:
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            received.append(json.loads(msg))

    async def producer():
        await asyncio.sleep(0.5)
        uri = f"{WS_BASE}/ws/ingest?token={token}"
        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({
                "user_id": USER_ID,
                "metric_1": 77.0,
                "metric_2": 150.0,
                "metric_3": 3.14,
                "timestamp": ws_ts,
            }))
            resp = await ws.recv()
            print(f"  WS ingest response: {resp}")

    await asyncio.gather(subscriber(), producer())

    assert len(received) == 1
    event = received[0]
    print(f"  WS subscribe received: {json.dumps(event, indent=2)}")
    assert event["event"] == "NEW_DATA"
    assert event["user_id"] == USER_ID
    print("  WebSocket flow verified!")


asyncio.run(test_websockets())

# ── Done ──
heading("ALL CHECKS PASSED")
client.close()
