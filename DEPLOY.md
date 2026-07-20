# Desplegar TAVOGYM en Render (acceso desde cualquier lugar)

Con la app en **Render**, Tavo puede publicar el estado del gym desde el local y vos recibís la notificación en tu casa. No hace falta estar en la misma WiFi.

## ¿Cómo funcionan las notificaciones?

```
Tavo publica "Gym abierto" en su celular
        ↓
Servidor TAVOGYM en Render (internet)
        ↓
Servidores de Google/Apple (Web Push)
        ↓
Tu celular en casa recibe la notificación 🔔
```

Las notificaciones **no dependen de la red del gym**. Funcionan por internet, igual que WhatsApp o Instagram.

---

## Paso 1: Base de datos gratis (Neon)

Render no guarda SQLite de forma permanente. Usamos **Neon** (PostgreSQL gratis):

1. Entrá a [https://neon.tech](https://neon.tech) y creá una cuenta gratis
2. Creá un proyecto nuevo (ej: `tavogym`)
3. Copiá la **Connection string** (empieza con `postgresql://...`)

---

## Paso 2: Claves para notificaciones push

En tu PC, dentro de la carpeta del proyecto:

```bash
python generate_vapid_keys.py
```

Copiá `VAPID_PUBLIC_KEY` y `VAPID_PRIVATE_KEY` del archivo `.env` que se genera.

---

## Paso 3: Subir el código a GitHub

1. Creá un repositorio en GitHub (ej: `tavogym`)
2. Subí la carpeta `Proyecto GYM`:

```bash
cd "C:\Users\facundomurua\Desktop\Proyecto GYM"
git init
git add .
git commit -m "TAVOGYM app"
git remote add origin https://github.com/TU-USUARIO/tavogym.git
git push -u origin main
```

---

## Paso 4: Crear el servicio en Render

1. Entrá a [https://render.com](https://render.com) y registrate (gratis)
2. **New → Blueprint**
3. Conectá tu repositorio de GitHub
4. Render detectará el archivo `render.yaml` automáticamente
5. Completá estas variables de entorno cuando te las pida:

| Variable | Valor |
|----------|-------|
| `DATABASE_URL` | La connection string de Neon |
| `VAPID_PUBLIC_KEY` | Del paso 2 |
| `VAPID_PRIVATE_KEY` | Del paso 2 (incluye las líneas `-----BEGIN...`) |
| `ADMIN_PASSWORD` | Una contraseña segura para Tavo |
| `SECRET_KEY` | Render la genera sola |

6. Clic en **Apply** y esperá 2-3 minutos

Tu app quedará en una URL como:
```
https://tavogym.onrender.com
```

---

## Paso 5: Configurar celulares

### Tavo (admin)
1. Abrí `https://tavogym.onrender.com` en Chrome
2. Ingresá con `tavo` y tu `ADMIN_PASSWORD`
3. Menú → **Agregar a pantalla de inicio**

### Clientes
1. Tavo los registra desde el panel admin
2. Les pasa usuario y contraseña
3. Entran a la misma URL desde su celular
4. **Agregar a pantalla de inicio**
5. Tocan **Activar notificaciones** cuando aparezca el aviso

---

## Notas importantes

### Plan gratis de Render
- El servidor **se duerme** después de ~15 min sin uso
- La primera visita puede tardar **30-60 segundos** en cargar (se despierta solo)
- Para un gym de barrio suele alcanzar; si molesta, el plan pago cuesta ~USD 7/mes

### HTTPS incluido
Render incluye HTTPS automático. Es **obligatorio** para que funcionen las notificaciones push en celulares.

### Cambiar contraseña de Tavo
En Render → tu servicio → **Environment** → editá `ADMIN_PASSWORD` → redeploy.

> La contraseña solo aplica al crear el admin la primera vez. Si ya existe, hay que cambiarla desde la base de datos o borrar el usuario admin en Neon.

### URL para compartir
Compartí este link con todos los clientes:
```
https://TU-APP.onrender.com
```

Guardalo en WhatsApp, en un cartel del gym, etc.

---

## Resumen rápido

| Dónde | Qué pasa |
|-------|----------|
| Tavo en el gym | Publica estado → servidor Render |
| Vos en tu casa | Recibís notificación push al instante |
| Cualquier cliente | Ve cuotas, deudas y avisos desde su celular |

**Localhost = solo tu PC. Render = todo el mundo con internet.**
