"""Tests for BGV verification endpoints."""
import pytest


class TestBGVEndpoints:
    """Test BGV verification link generation and portal viewer."""

    @pytest.mark.asyncio
    async def test_store_statement(self, client):
        """Store a statement for BGV (in-memory)."""
        payload = {
            "bankName": "HDFC Bank",
            "accountNumber": "1234567890",
            "accountHolder": "Test User",
            "period": "January 2026",
            "transactions": [],
        }
        response = await client.post("/api/bgv/store-statement", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_generate_verification_link(self, client):
        """Generate a BGV verification link."""
        response = await client.post("/api/bgv/generate-link", json={
            "accountId": "1234567890",
            "bankName": "HDFC Bank",
            "accountHolder": "Test User",
            "mode": "portal",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "viewUrl" in data
        assert "password" in data
        assert data["password"] == "7890"  # Last 4 digits

    @pytest.mark.asyncio
    async def test_view_verification_link(self, client):
        """View a verification link (bank portal page)."""
        # First store statement data
        await client.post("/api/bgv/store-statement", json={
            "bankName": "ICICI Bank",
            "accountNumber": "5555555555",
            "accountHolder": "Portal Test",
            "period": "February 2026",
            "transactions": [],
        })

        # Generate link
        link_resp = await client.post("/api/bgv/generate-link", json={
            "accountId": "5555555555",
            "bankName": "ICICI Bank",
            "accountHolder": "Portal Test",
            "mode": "portal",
        })
        verification_id = link_resp.json()["verificationId"]

        # View portal
        response = await client.get(f"/api/bgv/view/{verification_id}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        body = response.text
        assert "ICICI Bank" in body
        assert "Portal Test" in body
        assert "5555" in body  # Last 4 digits as password

    @pytest.mark.asyncio
    async def test_invalid_verification_link(self, client):
        """Viewing an invalid link should return 404."""
        response = await client.get("/api/bgv/view/INVALID-ID")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_verification_links(self, client):
        """List all verification links."""
        # Generate a link
        await client.post("/api/bgv/generate-link", json={
            "accountId": "1111111111",
            "bankName": "SBI",
            "accountHolder": "List Test",
            "mode": "portal",
        })

        # List links
        response = await client.get("/api/bgv/links")
        assert response.status_code == 200
        links = response.json()
        assert len(links) >= 1
        assert any(l["accountId"] == "1111111111" for l in links)

    @pytest.mark.asyncio
    async def test_email_template(self, client):
        """Generate an email template."""
        response = await client.post("/api/bgv/email-template", json={
            "accountId": "1234567890",
            "bankName": "HDFC Bank",
            "accountHolder": "Test User",
            "toEmail": "bgv@verification.com",
            "verificationId": "BGV-TEST123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "htmlContent" in data
        assert "HDFC Bank" in data["htmlContent"]
        assert "Test User" in data["htmlContent"]
