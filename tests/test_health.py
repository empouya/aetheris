from app.main import app
from httpx import ASGITransport, AsyncClient


async def test_health_endpoint_returns_success_response() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]

    payload = response.json()

    assert payload == {
        "success": True,
        "data": {
            "status": "ok",
            "service": "aetheris-api",
        },
        "meta": {},
    }


async def test_health_endpoint_uses_incoming_request_id() -> None:
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/health", headers={"X-Request-ID": "test-request-id"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-id"
