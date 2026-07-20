import json
import logging

from pywebpush import WebPushException, webpush

from config import VAPID_CLAIM_EMAIL, VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY

logger = logging.getLogger(__name__)


def vapid_configured():
    return bool(VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY)


def send_push_notification(subscription, title, body, url="/"):
    if not vapid_configured():
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
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_CLAIM_EMAIL},
        )
        return True
    except WebPushException as exc:
        logger.warning("Push failed: %s", exc)
        return False


def send_push_to_subscriptions(subscriptions, title, body, url="/"):
    sent = 0
    for sub in subscriptions:
        if send_push_notification(sub, title, body, url):
            sent += 1
    return sent
