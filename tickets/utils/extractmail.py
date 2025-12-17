import logging
import re
from email.header import decode_header

"""Utility functions for extracting and decoding email content."""

logger = logging.getLogger(__name__)

# Decodes email header values that may be encoded in various formats.
def decode_header_value(value):
    logger.debug(f"Decoding header value: {value}")
    if not value:
        return ""
    parts = decode_header(value)
    decoded = ""
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded += part.decode(enc or "utf-8", errors="ignore")
        else:
            decoded += part
    logger.debug(f"Decoded header value: {decoded}")
    return decoded

# Removes HTML tags from the email body to extract plain text.
def strip_html_tags(html):
    logger.debug("Stripping HTML tags from email body.")
    clean = re.compile("<.*?>")
    text = re.sub(clean, "", html)
    logger.debug("HTML tags stripped.")
    return re.sub(r"\s+", " ", text).strip()

# Extracts the body of the email, handling both plain text and HTML formats.
def get_email_body(msg):
    logger.debug("Extracting email body.")
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/plain":
                return part.get_payload(decode=True).decode(errors="ignore")
            if ctype == "text/html":
                html = part.get_payload(decode=True).decode(errors="ignore")
                return strip_html_tags(html)
    else:
        return msg.get_payload(decode=True).decode(errors="ignore")
    logger.debug("Email body extracted.")
    return ""
