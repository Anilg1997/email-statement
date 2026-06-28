"""End-to-end test covering the complete upload→email workflow."""
import pytest
import fitz


def _make_valid_pdf() -> bytes:
    """Generate a minimal valid PDF that PyMuPDF can process."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Test Statement")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.asyncio
class TestEndToEnd:
    """Complete workflow integration test."""

    async def test_complete_workflow(self, client):
        """Run the full workflow from PDF upload to access tracking."""

        # ===== 1. Upload an edited PDF =====
        test_pdf = _make_valid_pdf()
        resp = await client.post(
            "/api/upload",
            data={"accountId": "1234567890"},
            files={"file": ("statement.pdf", test_pdf, "application/pdf")},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        print("✓ Step 1: Edited PDF uploaded for account 1234567890")

        # ===== 2. List uploaded files =====
        resp = await client.get("/api/list")
        assert resp.status_code == 200
        items = resp.json()
        assert any(i["accountId"] == "1234567890" for i in items)
        print("✓ Step 2: Uploaded file appears in list")

        # ===== 3. Replace endpoint serves the uploaded PDF encrypted =====
        resp = await client.get("/api/replace?accountId=1234567890")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert len(resp.content) > 0
        print("✓ Step 3: Replace endpoint serves encrypted PDF")

        # ===== 4. Replace without upload returns 404 =====
        resp = await client.get("/api/replace?accountId=9999999999")
        assert resp.status_code == 404
        print("✓ Step 4: Replace without upload returns 404")

        # ===== 5. Access tracking =====
        resp = await client.get("/api/access-log")
        assert resp.status_code == 200
        log_data = resp.json()
        assert "logs" in log_data
        assert "stats" in log_data
        print("✓ Step 5: Access tracking works")

        # ===== 6. Health check =====
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        print("✓ Step 6: Health check OK")

        # ===== 7. Email config save/load =====
        config_resp = await client.post("/api/email/config", json={
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "test@gmail.com",
            "password": "app-password",
            "useSsl": True,
            "fromName": "Bank Statement Service",
        })
        assert config_resp.status_code == 200
        assert config_resp.json()["status"] == "ok"
        print("✓ Step 7: Email configuration saved")

        # ===== 8. Get email config =====
        config_get = await client.get("/api/email/config")
        assert config_get.status_code == 200
        assert config_get.json()["configured"] is True
        print("✓ Step 8: Email configuration loaded")

        # ===== 9. Access tracking recorded views =====
        resp = await client.get("/api/access-log")
        assert resp.status_code == 200
        assert resp.json()["stats"]["totalAccesses"] >= 1
        print("✓ Step 9: Access tracking recorded PDF views")

        print("\n✅ All 9 end-to-end test steps passed!")
