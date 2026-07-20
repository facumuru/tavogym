# TAVOGYM - Sistema de gestión para gym de barrio

App web para **TAVOGYM** que reemplaza los estados de WhatsApp por notificaciones profesionales en el celular, y permite controlar cuotas y suplementos de cada cliente de forma privada.

## ¿Qué resuelve?

| Problema actual (WhatsApp) | Solución TAVOGYM |
|---|---|
| Estados de horario que no todos ven | Notificación push al celular de cada cliente |
| Lista de deudores pública en estados | Control privado solo visible para Tavo |
| Sin historial de pagos | Cada cliente ve sus cuotas y suplementos |
| Comunicación informal | Avisos directos y profesionales |

## Funcionalidades

### Para Tavo (Admin)
- Publicar estado del gym: **Abierto**, **Cerrado** o **Llego tarde**
- Notificar a todos los clientes con un toque
- Registrar clientes con usuario y contraseña
- Control de cuotas mensuales por cliente
- Control de suplementos (proteína, creatina, etc.)
- Ver quién debe (lista privada de deudores)
- Enviar avisos individuales o masivos

### Para los clientes
- Ver si el gym está abierto, cerrado o si Tavo llega tarde
- Recibir notificaciones en el celular
- Consultar cuotas pendientes y pagadas
- Ver historial de suplementos
- Instalar la app en el celular (PWA)

## Instalación

### Requisitos
- Python 3.10 o superior
- pip

### Pasos

1. **Instalar dependencias**
```bash
cd "C:\Users\facundomurua\Desktop\Proyecto GYM"
pip install -r requirements.txt
```

2. **Generar iconos**
```bash
python generate_icons.py
```

3. **Generar claves para notificaciones push**
```bash
pip install py-vapid
python generate_vapid_keys.py
```

4. **Iniciar la app**
```bash
python app.py
```

5. **Abrir en el navegador**
```
http://localhost:5000
```

### Credenciales iniciales (Admin)
- **Usuario:** `tavo`
- **Contraseña:** `tavogym2024`

> Cambiá la contraseña después del primer ingreso editando la base de datos o creando un script.

## Uso desde el celular

1. Abrí `http://[IP-DE-TU-PC]:5000` desde el celular (misma red WiFi)
2. Ingresá con tu usuario
3. En Chrome/Safari: **Agregar a pantalla de inicio**
4. Tocá **Activar notificaciones** cuando aparezca el aviso

> Para que las notificaciones push funcionen en producción, la app debe estar en **HTTPS**. Para pruebas locales funciona en `localhost`.

## Estructura del proyecto

```
Proyecto GYM/
├── app.py              # Aplicación principal Flask
├── config.py           # Configuración
├── database.py         # Base de datos SQLite
├── push_service.py     # Servicio de notificaciones push
├── requirements.txt    # Dependencias Python
├── generate_vapid_keys.py
├── generate_icons.py
├── database.db         # (se crea al iniciar)
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   ├── js/push.js
│   ├── sw.js           # Service Worker (PWA)
│   └── manifest.json
└── templates/
    ├── admin/          # Panel de Tavo
    └── client/         # Panel de clientes
```

## Flujo de trabajo recomendado

1. **Mañana:** Tavo publica el estado del gym → todos reciben notificación
2. **Cuando llega un cliente nuevo:** Tavo lo registra desde "Nuevo cliente"
3. **Fin de mes:** Tavo carga las cuotas y ve quién debe en "Deudas"
4. **Cuando pagan:** Tavo marca como pagado → el cliente recibe confirmación
5. **Suplementos:** Tavo registra la compra → el cliente ve su deuda actualizada

## Despliegue en internet (Render)

Para que los clientes accedan **desde su casa** y reciban notificaciones estés donde estés, leé la guía completa:

👉 **[DEPLOY.md](DEPLOY.md)** — paso a paso para subir a Render + Neon (gratis)

Resumen: localhost solo funciona en tu red WiFi. En Render la app queda en una URL pública (`https://tavogym.onrender.com`) y las notificaciones llegan por internet, no por la red del gym.

## Despliegue local (solo pruebas)

## Tecnologías

- **Python + Flask** — Backend simple y confiable
- **SQLite** — Base de datos sin configuración
- **PWA** — Instalable en celular como app nativa
- **Web Push API** — Notificaciones reales al celular

---

Hecho para **TAVOGYM** 💪
