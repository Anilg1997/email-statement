"""Shared configuration store for global singleton instances.

This module stores active runtime configurations to avoid circular imports
between API modules (e.g., email API importing inbound_email API and vice versa).
"""

from typing import Optional
from app.services.email_service import EmailConfig as SmtpConfigObj


# Active SMTP configuration (set by email API)
active_smtp_config: Optional[SmtpConfigObj] = None
