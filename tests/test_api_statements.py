"""Tests for PDF upload and replace endpoints."""
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


class TestReplaceEndpoint:
    """Test GET /api/replace - serve uploaded PDF."""

    @pytest.mark.asyncio
    async def test_replace_without_upload(self, client):
        """Replace endpoint should fail if no PDF is uploaded."""
        response = await client.get("/api/replace?accountId=1234567890")
        assert response.status_code == 404
        assert "No uploaded PDF found" in response.text

    @pytest.mark.asyncio
    async def test_replace_missing_account_id(self, client):
        """Replace endpoint should fail without accountId."""
        response = await client.get("/api/replace")
        assert response.status_code in (400, 422)  # 422 = FastAPI validation, 400 = explicit check


class TestUploadEndpoint:
    """Test POST /api/upload and GET /api/list."""

    @pytest.mark.asyncio
    async def test_upload_and_list(self, client):
        """Upload a PDF and verify it appears in the list."""
        # Upload
        test_pdf_content = _make_valid_pdf()
        response = await client.post(
            "/api/upload",
            data={"accountId": "9999999999"},
            files={"file": ("test.pdf", test_pdf_content, "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

        # List
        response = await client.get("/api/list")
        assert response.status_code == 200
        items = response.json()
        assert any(item["accountId"] == "9999999999" for item in items)

    @pytest.mark.asyncio
    async def test_replace_with_upload(self, client):
        """After uploading, replace should serve the uploaded PDF encrypted."""
        test_pdf = _make_valid_pdf()
        await client.post(
            "/api/upload",
            data={"accountId": "8888888888"},
            files={"file": ("statement.pdf", test_pdf, "application/pdf")},
        )

        response = await client.get("/api/replace?accountId=8888888888")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 0
