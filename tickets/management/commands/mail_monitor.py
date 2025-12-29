import logging
import time
from django.core.management.base import BaseCommand
from imapclient import IMAPClient
from django.conf import settings
from email import message_from_bytes
from email.utils import parseaddr
from tickets.utils.extractmail import decode_header_value, get_email_body
from tickets.views import email_ticket_create
from django.contrib.auth import get_user_model
from account.utils.emailuser import get_or_create_user_by_email

logger = logging.getLogger(__name__)
User = get_user_model()

POLL_INTERVAL = 60  # seconds

class Command(BaseCommand):
    help = "Monitor inbox, create tickets, and send reply emails"

    account_key = "support"
    accounts = getattr(settings, "EMAIL_ACCOUNTS", {})
    config = accounts[account_key]
    host = settings.EMAIL_IMAP_HOST
    username = config["EMAIL_HOST_USER"]
    password = config["EMAIL_HOST_PASSWORD"]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting mailbox monitor..."))

        while True:
            try:
                with IMAPClient(self.host, ssl=True) as client:
                    client.login(self.username, self.password)
                    logger.info("Logged in to IMAP as %s", self.username)

                    # main polling loop for this connection
                    while True:
                        client.select_folder("INBOX", readonly=False)

                        uids = client.search(["UNSEEN"])
                        logger.debug("Found %d unseen messages", len(uids))

                        for uid in uids:
                            data = client.fetch(uid, ["RFC822"])
                            raw = data[uid][b"RFC822"]
                            msg = message_from_bytes(raw)

                            subject = decode_header_value(msg["Subject"])
                            body = get_email_body(msg)
                            sender = parseaddr(msg["From"])[1]

                            self.stdout.write("\n" + "=" * 60)
                            self.stdout.write(f"Processing email UID {uid}")
                            self.stdout.write(f"From: {sender}")
                            self.stdout.write(f"Subject: {subject}")

                            user = User.objects.filter(email__iexact=sender).first()
                            if not user:
                                user, reset_url = get_or_create_user_by_email(
                                    sender, True, self.account_key
                                )

                            ticket, email_ticket = email_ticket_create(
                                email_uid=uid,
                                sender=sender,
                                subject=subject,
                                body=body,
                                raw_email=raw.decode("utf8", errors="replace"),
                                user=User.objects.filter(email__iexact=sender).first(),
                                account_key=self.account_key,
                            )

                            # Mark as seen
                            client.add_flags(uid, [r"\Seen"])
                            logger.info("Email UID %s marked as seen.", uid)
                            self.stdout.write("=" * 60 + "\n")
                            logger.info("Processed email UID %s.", uid)

                        logger.info(
                            "Sleeping for POLL_INTERVAL - %s seconds before next check.",
                            POLL_INTERVAL,
                        )
                        time.sleep(POLL_INTERVAL)

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error: {e}"))
                logger.error("Exception in monitoring loop: %s", str(e))
                logger.info(
                    "Sleeping for POLL_INTERVAL - %s seconds after error.",
                    POLL_INTERVAL,
                )
                time.sleep(POLL_INTERVAL)
