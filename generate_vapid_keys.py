"""Genera claves VAPID para notificaciones push web."""
import os

try:
    from py_vapid import Vapid02 as Vapid
except ImportError:
    print("Instalá dependencias: pip install py-vapid")
    raise

vapid = Vapid()
vapid.generate_keys()

private_pem = vapid.private_pem().decode() if isinstance(vapid.private_pem(), bytes) else vapid.private_pem()
public_b64 = vapid.public_key

print("=" * 50)
print("Claves VAPID generadas para TAVOGYM")
print("=" * 50)
print()
print("Agregá esto a tu archivo .env:")
print()
print(f"VAPID_PRIVATE_KEY={private_pem.strip()}")
print(f"VAPID_PUBLIC_KEY={public_b64}")
print()
print("=" * 50)

env_path = os.path.join(os.path.dirname(__file__), ".env")
if not os.path.exists(env_path):
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f"SECRET_KEY=tavogym-produccion-{os.urandom(16).hex()}\n")
        f.write(f"VAPID_PRIVATE_KEY={private_pem.strip()}\n")
        f.write(f"VAPID_PUBLIC_KEY={public_b64}\n")
        f.write("VAPID_CLAIM_EMAIL=mailto:admin@tavogym.com\n")
    print(f"Archivo .env creado en: {env_path}")
else:
    print("Para Render.com, pegá las claves en Environment Variables.")
    print("Si la clave privada tiene saltos de linea, usá \\n en Render.")
