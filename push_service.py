import json
import logging
import os
import tempfile

from pywebpush import WebPushException, webpush

from config import BASE_DIR, VAPID_CLAIM_EMAIL, VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY

logger = logging.getLogger(__name__)

_vapid_key_path = None


def _prepare_vapid_key_file():
    global _vapid_key_path
    if _vapid_key_path and os.path.exists(_vapid_key_path):
        return _vapid_key_path

    if not VAPID_PRIVATE_KEY:
        return None

    key_path = BASE_DIR / ".vapid_private.pem"
    key_path.write_text(VAPID_PRIVATE_KEY.strip() + "\n", encoding="utf-8")
    _vapid_key_path = str(key_path)
    return _vapid_key_path


def vapid_configured():
    return bool(VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY)


def send_push_notification(subscription, title, body, url="/"):
    if not vapid_configured():
        return False

    key_file = _prepare_vapid_key_file()
    if not key_file:
        return False

    payload = json.dumps({"title": title, "body": body, "url": url})

    try:
        webpush(
            subscription_info={
                "endpoint": subscription["endpoint"],
                "keys": {
                    "p256dh": subscription["p256dh"],
                    "auth": subscription["auth"],
                },
            },
            data=payload,
            vapid_private_key=key_file,
            vapid_claims={"sub": VAPID_CLAIM_EMAIL},
        )
        return True
    except WebPushException as exc:
        logger.warning("Push failed: %s", exc)
        return False
    except Exception as exc:
        logger.warning("Push error: %s", exc)
        return False


def send_push_to_subscriptions(subscriptions, title, body, url="/"):
    sent = 0
    for sub in subscriptions:
        if send_push_notification(sub, title, body, url):
            sent += 1
    return sent
