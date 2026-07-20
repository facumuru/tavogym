# TAVOGYM — Qué hacer AHORA (Render + Base de datos)

Seguí estos pasos en orden. Son 3 cosas: **BD → GitHub → Render**.

---

## PASO 1 — Base de datos (Neon) ⏱ 3 min

Render **no guarda** la base de datos gratis. Usamos **Neon** (PostgreSQL gratis).

1. Abrí: **https://neon.tech**
2. **Sign up** (podés entrar con Google/GitHub)
3. **Create a project** → nombre: `tavogym`
4. En el panel, buscá **Connection string** (pestaña "Connect")
5. Copiá la que dice **Pooled connection** o **Direct** — empieza así:
   ```
   postgresql://usuario:contraseña@ep-xxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

**Pegame esa URL acá en el chat** (o guardala para el paso 3).  
Es la `DATABASE_URL`.

---

## PASO 2 — Subir el código a GitHub ⏱ 5 min

Render necesita el código en GitHub.

### Si NO tenés Git instalado (tu caso):

1. Abrí: **https://github.com/new**
2. Nombre del repo: `tavogym`
3. Marcá **Public** → **Create repository**
4. En la página del repo nuevo, clic en **"uploading an existing file"**
5. Arrastrá **todos los archivos** de la carpeta:
   ```
   C:\Users\facundomurua\Desktop\Proyecto GYM
   ```
   (menos `database.db` y `.env` si existen — no los subas)
6. Abajo: **Commit changes**

**Decime tu usuario de GitHub** cuando esté subido (ej: `facundomurua/tavogym`).

---

## PASO 3 — Claves de notificaciones ⏱ 2 min

En tu PC, abrí PowerShell en la carpeta del proyecto:

```powershell
cd "C:\Users\facundomurua\Desktop\Proyecto GYM"
python generate_vapid_keys.py
```

Copiá `VAPID_PUBLIC_KEY` y `VAPID_PRIVATE_KEY` del archivo `.env` que se crea.

---

## PASO 4 — Crear el servicio en Render ⏱ 5 min

En **https://dashboard.render.com/**:

1. Clic en **New +** → **Web Service**
2. Conectá tu cuenta de **GitHub** (si te lo pide)
3. Elegí el repo **`tavogym`**
4. Completá:

| Campo | Valor |
|-------|-------|
| Name | `tavogym` |
| Region | Oregon (US West) o el más cercano |
| Branch | `main` |
| Runtime | **Python 3** |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |
| Plan | **Free** |

5. Clic en **Advanced** → **Add Environment Variable**:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | La URL de Neon (paso 1) |
| `VAPID_PUBLIC_KEY` | Del paso 3 |
| `VAPID_PRIVATE_KEY` | Del paso 3 (toda la clave, con `-----BEGIN...`) |
| `ADMIN_PASSWORD` | Una contraseña segura para Tavo (ej: `TavoGym2026!`) |
| `SECRET_KEY` | Cualquier texto largo random (ej: `mi-clave-secreta-tavogym-2026`) |
| `VAPID_CLAIM_EMAIL` | `mailto:admin@tavogym.com` |

6. **Create Web Service**
7. Esperá 3–5 minutos hasta que diga **Live**

Tu URL será algo como:
```
https://tavogym.onrender.com
```

---

## PASO 5 — Probar

1. Abrí la URL en el celular
2. Ingresá: usuario `tavo` / contraseña la que pusiste en `ADMIN_PASSWORD`
3. Agregá a pantalla de inicio
4. Activá notificaciones

---

## ¿Qué NO hace falta?

- ❌ No me des tu contraseña de Render (no puedo entrar a tu dashboard)
- ❌ No crear base de datos en Render (usamos Neon)
- ❌ No pagar nada (plan free de Render + Neon free)

## ¿Qué SÍ necesito de vos para ayudarte?

1. La **DATABASE_URL** de Neon (paso 1)
2. Tu **usuario/repo de GitHub** (paso 2)
3. Si algo falla en Render, una captura o el mensaje de error del deploy

Con eso te guío en lo que falle.
