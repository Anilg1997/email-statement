"""Tests for the Inbound BGV Email Auto-Responder feature.

These tests verify the core logic without requiring a real IMAP/SMTP connection.
We mock the external services (imaplib, smtplib) to test the business logic.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.services.inbound_email_service import (
    InboundEmailProcessor,
    decode_mime_header,
    extract_email_address,
    get_email_body,
    detect_bgv_keywords,
    extract_account_number,
    generate_genuine_reply_html,
    BGV_KEYWORDS,
)
from app.services.email_service import EmailConfig
from app.schemas.inbound_email import (
    InboundEmailConfigSchema,
    InboundEmailConfigResponse,
    CheckInboxResponse,
    InboundEmailLogEntry,
    InboundEmailLogResponse,
)


class TestHelperFunctions:
    """Test the standalone helper functions."""

    def test_decode_mime_header_plain(self):
        result = decode_mime_header("Simple Subject")
        assert result == "Simple Subject"

    def test_decode_mime_header_empty(self):
        assert decode_mime_header("") == ""
        assert decode_mime_header(None) == ""

    def test_extract_email_address_with_angle_brackets(self):
        result = extract_email_address("John Doe <john@example.com>")
        assert result == "john@example.com"

    def test_extract_email_address_plain(self):
        result = extract_email_address("john@example.com")
        assert result == "john@example.com"

    def test_extract_email_address_from_name_only(self):
        result = extract_email_address("BGV Team bgv@verify.com")
        assert result == "bgv@verify.com"

    def test_get_email_body_simple(self):
        msg = MIMEText("Hello this is a test body")
        body = get_email_body(msg)
        assert "Hello this is a test body" in body

    def test_get_email_body_multipart(self):
        msg = MIMEMultipart("mixed")
        html_part = MIMEText("<html><body>HTML body</body></html>", "html")
        text_part = MIMEText("Plain text body", "plain")
        msg.attach(text_part)
        msg.attach(html_part)
        body = get_email_body(msg)
        assert "Plain text body" in body

    def test_get_email_body_empty(self):
        assert get_email_body(MIMEMultipart()) == ""

    def test_detect_bgv_keywords_match(self):
        text = "This is a BGV verification request for account statement"
        matched = detect_bgv_keywords(text)
        assert "bgv" in matched
        assert "verification" in matched
        assert "account statement" in matched or "bank statement" in matched

    def test_detect_bgv_keywords_no_match(self):
        text = "Hello, how are you? Meeting at 3pm."
        matched = detect_bgv_keywords(text)
        assert matched == []

    def test_detect_bgv_keywords_empty(self):
        assert detect_bgv_keywords("") == []
        assert detect_bgv_keywords(None) == []

    def test_detect_bgv_keywords_case_insensitive(self):
        text = "BACKGROUND VERIFICATION Check Required"
        matched = detect_bgv_keywords(text)
        assert "background verification" in matched

    def test_extract_account_number_with_label(self):
        text = "Account Number: 1234567890"
        result = extract_account_number(text)
        assert result == "1234567890"

    def test_extract_account_number_with_variations(self):
        text = "A/C No: 9876543210"
        result = extract_account_number(text)
        assert result == "9876543210"

    def test_extract_account_number_bare_digits(self):
        text = "Please verify account 123456789012"
        result = extract_account_number(text)
        assert result == "123456789012"

    def test_extract_account_number_short_number(self):
        text = "Account: 1234"
        result = extract_account_number(text)
        assert result is None  # Too short

    def test_extract_account_number_no_match(self):
        text = "No account details in this text"
        assert extract_account_number(text) is None

    def test_generate_genuine_reply_html(self):
        html = generate_genuine_reply_html(
            bank_name="HDFC Bank",
            account_holder="Rahul Sharma",
            account_id="1234567890",
            verification_id="BGV-TEST123",
            view_url="http://localhost:8080/api/bgv/view/BGV-TEST123",
            password="7890",
        )
        assert "VERIFICATION CONFIRMED" in html
        assert "VERIFIED GENUINE" in html
        assert "HDFC Bank" in html
        assert "Rahul Sharma" in html
        assert "1234567890" in html
        assert "BGV-TEST123" in html
        assert "7890" in html
        assert "http://localhost:8080/api/bgv/view/BGV-TEST123" in html


class TestInboundEmailProcessor:
    """Test the InboundEmailProcessor class with mocked IMAP/SMTP."""

    @pytest.fixture
    def processor(self):
        p = InboundEmailProcessor(
            imap_host="imap.gmail.com",
            imap_port=993,
            imap_username="hhrrr@borngroup.com",
            imap_password="app-password",
            use_ssl=True,
            company_email="hhrrr@borngroup.com",
            bgv_sender_filter="",
            reply_from_name="BGV Verification Service",
            include_pdf_attachment=True,
            include_verification_link=True,
        )
        smtp_cfg = EmailConfig(
            host="smtp.gmail.com",
            port=587,
            username="hhrrr@borngroup.com",
            password="smtp-password",
            use_ssl=False,
            from_name="BGV Verification Service",
        )
        p.set_smtp_config(smtp_cfg)
        return p

    def test_init(self, processor):
        assert processor.imap_host == "imap.gmail.com"
        assert processor.company_email == "hhrrr@borngroup.com"
        assert processor._smtp_config is not None
        assert processor._smtp_config.is_configured() is True

    def test_is_bgv_email_keyword_match(self, processor):
        is_bgv, keywords = processor._is_bgv_email(
            sender="bgv-team@verification-company.com",
            subject="BGV Verification Request for Account Statement",
            body="Dear Sir, Please confirm the bank statement for BGV purposes.",
        )
        assert is_bgv is True
        assert len(keywords) > 0
        assert "bgv" in keywords

    def test_is_bgv_email_no_match(self, processor):
        is_bgv, keywords = processor._is_bgv_email(
            sender="friend@example.com",
            subject="Lunch tomorrow?",
            body="Hey, want to grab lunch at 1pm?",
        )
        assert is_bgv is False
        assert keywords == []

    def test_is_bgv_email_sender_filter(self, processor):
        processor.bgv_sender_filter = "@verification-company.com"
        is_bgv, keywords = processor._is_bgv_email(
            sender="bgv-team@verification-company.com",
            subject="Regarding account statement",
            body="Please provide the statement",
        )
        assert is_bgv is True
        assert "matched sender filter" in keywords

    def test_is_bgv_email_sender_filter_no_match(self, processor):
        processor.bgv_sender_filter = "@verification-company.com"
        is_bgv, keywords = processor._is_bgv_email(
            sender="someone-else@other.com",
            subject="Regarding account statement",
            body="Please provide the statement",
        )
        assert is_bgv is False

    @pytest.mark.asyncio
    async def test_check_inbox_no_smtp(self):
        p = InboundEmailProcessor(
            imap_host="imap.gmail.com",
            imap_port=993,
            imap_username="test@test.com",
            imap_password="pass",
            use_ssl=True,
            company_email="test@test.com",
        )
        # SMTP not configured
        result = await p.check_inbox()
        assert result["status"] == "error"
        assert "SMTP not configured" in str(result["details"])

    @pytest.mark.asyncio
    async def test_check_inbox_imap_connection_failure(self, processor):
        """Test that IMAP connection failure is handled gracefully."""
        result = await processor.check_inbox()
        assert result["status"] == "error"
        # Should fail to connect to real IMAP (we're testing error handling)
        assert any("Failed to connect" in str(d) for d in result["details"])


class TestAPISchemas:
    """Test the Pydantic schemas for inbound email."""

    def test_inbound_config_schema(self):
        data = {
            "imapHost": "imap.gmail.com",
            "imapPort": 993,
            "imapUsername": "test@test.com",
            "imapPassword": "password",
            "useSsl": True,
            "companyEmail": "test@test.com",
            "bgvSenderFilter": "@bgv.com",
            "replyEnabled": True,
            "replyFromName": "BGV Service",
            "includePdfAttachment": True,
            "includeVerificationLink": True,
        }
        schema = InboundEmailConfigSchema(**data)
        assert schema.imapHost == "imap.gmail.com"
        assert schema.imapUsername == "test@test.com"
        assert schema.companyEmail == "test@test.com"

    def test_inbound_config_response(self):
        resp = InboundEmailConfigResponse(
            configured=True,
            imapHost="imap.gmail.com",
            imapPort=993,
            companyEmail="test@test.com",
        )
        assert resp.configured is True
        assert resp.imapHost == "imap.gmail.com"

    def test_check_inbox_response(self):
        resp = CheckInboxResponse(
            status="ok",
            totalEmails=10,
            bgvMatched=3,
            repliesSent=2,
            skipped=7,
            failed=1,
            details=[{"action": "summary", "totalEmails": 10}],
        )
        assert resp.status == "ok"
        assert resp.totalEmails == 10
        assert resp.bgvMatched == 3
        assert resp.repliesSent == 2

    def test_inbound_email_log_entry(self):
        entry = InboundEmailLogEntry(
            id=1,
            emailUid="12345",
            sender="bgv@test.com",
            subject="BGV Request",
            bgvStatus="processed",
            replySent=True,
        )
        assert entry.sender == "bgv@test.com"
        assert entry.bgvStatus == "processed"

    def test_inbound_email_log_response(self):
        log = InboundEmailLogEntry(
            id=1, emailUid="1", sender="a@b.com",
            subject="Test", bgvStatus="processed",
        )
        resp = InboundEmailLogResponse(
            logs=[log],
            total=1,
            stats={"totalEmails": 1, "repliesSent": 1},
        )
        assert len(resp.logs) == 1
        assert resp.total == 1
        assert resp.stats["totalEmails"] == 1


class TestBGVKeywordList:
    """Verify BGV keywords are comprehensive."""

    def test_keywords_cover_common_phrases(self):
        """Ensure all common BGV-related phrases are covered."""
        test_phrases = [
            "bgv",
            "background verification",
            "background check",
            "statement verification",
            "verify statement",
            "account verification",
            "bg verification",
            "employment verification",
            "bank verification",
        ]
        for phrase in test_phrases:
            matched = detect_bgv_keywords(phrase)
            assert phrase in matched or any(
                phrase.startswith(kw) or kw in phrase
                for kw in matched
            ), f"Keyword not found for: {phrase}"
