"""Genera iconos simples para la PWA de TAVOGYM."""
import os
import struct
import zlib

BASE_DIR = os.path.dirname(__file__)
ICONS_DIR = os.path.join(BASE_DIR, "static", "icons")
os.makedirs(ICONS_DIR, exist_ok=True)


def create_png(size, filename):
    """Crea un PNG naranja con emoji-style usando solo stdlib."""
    width = height = size

    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    raw = b""
    orange = (255, 107, 53)
    dark = (10, 10, 10)

    cx, cy = width // 2, height // 2
    radius = int(size * 0.38)

    for y in range(height):
        raw += b"\x00"
        for x in range(width):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dist <= radius:
                raw += bytes(orange)
            elif dist <= radius + 2:
                raw += bytes((200, 80, 40))
            else:
                raw += bytes(dark)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(raw))
    png += chunk(b"IEND", b"")

    path = os.path.join(ICONS_DIR, filename)
    with open(path, "wb") as f:
        f.write(png)
    print(f"Creado: {path}")


if __name__ == "__main__":
    create_png(192, "icon-192.png")
    create_png(512, "icon-512.png")
    print("Iconos generados correctamente.")
