"""Genera claves VAPID para notificaciones push web."""
import os

from py_vapid import Vapid02 as Vapid
from py_vapid.utils import b64urlencode

vapid = Vapid()
vapid.generate_keys()

private_pem = vapid.private_pem()
if isinstance(private_pem, bytes):
    private_pem = private_pem.decode()

private_one_line = private_pem.strip().replace("\n", "\\n")

numbers = vapid.public_key.public_numbers()
public_raw = b"\x04" + numbers.x.to_bytes(32, "big") + numbers.y.to_bytes(32, "big")
public_b64 = b64urlencode(public_raw)

print("=" * 50)
print("Claves VAPID para TAVOGYM")
print("=" * 50)
print()
print("Render -> Environment (copiar tal cual):")
print()
print(f"VAPID_PUBLIC_KEY={public_b64}")
print(f"VAPID_PRIVATE_KEY={private_one_line}")
print("VAPID_CLAIM_EMAIL=mailto:admin@tavogym.com")
print()
print("=" * 50)

env_path = os.path.join(os.path.dirname(__file__), ".env")
with open(env_path, "w", encoding="utf-8") as f:
    f.write(f"SECRET_KEY=tavogym-produccion-{os.urandom(16).hex()}\n")
    f.write(f"VAPID_PRIVATE_KEY={private_one_line}\n")
    f.write(f"VAPID_PUBLIC_KEY={public_b64}\n")
    f.write("VAPID_CLAIM_EMAIL=mailto:admin@tavogym.com\n")
print(f".env actualizado: {env_path}")
