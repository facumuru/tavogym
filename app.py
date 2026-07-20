import json
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user

import database as db
from config import MONTHLY_FEE_DEFAULT, SECRET_KEY, VAPID_PUBLIC_KEY
from push_service import send_push_to_subscriptions, vapid_configured
from whitenoise import WhiteNoise

BASE_DIR = Path(__file__).resolve().parent

app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static"),
    static_url_path="/static",
    template_folder=str(BASE_DIR / "templates"),
)
app.secret_key = SECRET_KEY
app.wsgi_app = WhiteNoise(
    app.wsgi_app,
    root=str(BASE_DIR / "static"),
    prefix="/static/",
    index_file=False,
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):
    def __init__(self, data):
        if not isinstance(data, dict):
            data = dict(data)
        self.id = data["id"]
        self.username = data["username"]
        self.name = data["name"]
        self.role = data["role"]
        self.phone = data.get("phone") or ""


@login_manager.user_loader
def load_user(user_id):
    data = db.get_user_by_id(int(user_id))
    return User(data) if data else None


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            flash("Acceso solo para administradores.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


MONTH_NAMES = [
    "",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

STATUS_LABELS = {
    "open": "Abierto",
    "closed": "Cerrado",
    "late": "Llega tarde",
}

STATUS_ICONS = {
    "open": "✅",
    "closed": "🔴",
    "late": "⏰",
}


@app.context_processor
def inject_globals():
    return {
        "month_names": MONTH_NAMES,
        "status_labels": STATUS_LABELS,
        "monthly_fee_default": MONTHLY_FEE_DEFAULT,
        "vapid_public_key": VAPID_PUBLIC_KEY,
        "push_enabled": vapid_configured(),
    }


@app.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("client_dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        user_data = db.get_user_by_username(username)
        if user_data and db.verify_password(user_data, password) and user_data["active"]:
            login_user(User(user_data))
            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))
        flash("Usuario o contraseña incorrectos.", "error")

    gym_status = db.get_current_gym_status()
    return render_template("login.html", gym_status=gym_status)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


# ─── Admin routes ───────────────────────────────────────────


@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = db.get_admin_stats()
    gym_status = db.get_current_gym_status()
    clients = db.get_all_clients()
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        gym_status=gym_status,
        clients=clients[:5],
    )


@app.route("/admin/clientes")
@admin_required
def admin_clients():
    clients = db.get_all_clients()
    return render_template("admin/clients.html", clients=clients)


@app.route("/admin/clientes/nuevo", methods=["GET", "POST"])
@admin_required
def admin_new_client():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").strip()
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()

        if not all([username, password, name]):
            flash("Completá usuario, contraseña y nombre.", "error")
            return render_template("admin/new_client.html")

        if db.get_user_by_username(username):
            flash("Ese usuario ya existe.", "error")
            return render_template("admin/new_client.html")

        user_id = db.create_client(username, password, name, phone)
        flash(f"Cliente {name} registrado correctamente.", "success")
        return redirect(url_for("admin_client_detail", user_id=user_id))

    return render_template("admin/new_client.html")


@app.route("/admin/clientes/<int:user_id>")
@admin_required
def admin_client_detail(user_id):
    summary = db.get_client_summary(user_id)
    if not summary:
        flash("Cliente no encontrado.", "error")
        return redirect(url_for("admin_clients"))
    return render_template("admin/client_detail.html", summary=summary)


@app.route("/admin/clientes/<int:user_id>/cuota", methods=["POST"])
@admin_required
def admin_add_fee(user_id):
    month = int(request.form.get("month", datetime.now().month))
    year = int(request.form.get("year", datetime.now().year))
    amount = float(request.form.get("amount", MONTHLY_FEE_DEFAULT))
    notes = request.form.get("notes", "").strip()
    db.add_monthly_fee(user_id, month, year, amount, notes)
    flash("Cuota registrada.", "success")
    return redirect(url_for("admin_client_detail", user_id=user_id))


@app.route("/admin/clientes/<int:user_id>/cuota/<int:fee_id>/pagar", methods=["POST"])
@admin_required
def admin_pay_fee(user_id, fee_id):
    db.mark_monthly_paid(fee_id)
    summary = db.get_client_summary(user_id)
    name = summary["user"]["name"]
    db.create_notification(
        user_id,
        "Cuota pagada ✅",
        f"Tu cuota fue registrada como pagada. ¡Gracias, {name}!",
        "payment",
    )
    subs = db.get_client_push_subscriptions(user_id)
    send_push_to_subscriptions(subs, "Cuota pagada ✅", "Tu cuota fue registrada como pagada.", "/cliente")
    flash("Cuota marcada como pagada.", "success")
    return redirect(url_for("admin_client_detail", user_id=user_id))


@app.route("/admin/clientes/<int:user_id>/suplemento", methods=["POST"])
@admin_required
def admin_add_supplement(user_id):
    product = request.form.get("product_name", "").strip()
    amount = float(request.form.get("amount", 0))
    notes = request.form.get("notes", "").strip()

    if not product or amount <= 0:
        flash("Completá producto y monto.", "error")
        return redirect(url_for("admin_client_detail", user_id=user_id))

    db.add_supplement_debt(user_id, product, amount, notes)
    db.create_notification(
        user_id,
        "Nuevo suplemento registrado",
        f"Se registró: {product} - ${amount:,.0f}",
        "supplement",
    )
    subs = db.get_client_push_subscriptions(user_id)
    send_push_to_subscriptions(
        subs,
        "Suplemento registrado",
        f"{product} - ${amount:,.0f}",
        "/cliente/pagos",
    )
    flash("Suplemento agregado.", "success")
    return redirect(url_for("admin_client_detail", user_id=user_id))


@app.route("/admin/clientes/<int:user_id>/suplemento/<int:debt_id>/pagar", methods=["POST"])
@admin_required
def admin_pay_supplement(user_id, debt_id):
    db.mark_supplement_paid(debt_id)
    db.create_notification(
        user_id,
        "Suplemento pagado ✅",
        "Tu pago de suplemento fue registrado. ¡Gracias!",
        "payment",
    )
    subs = db.get_client_push_subscriptions(user_id)
    send_push_to_subscriptions(subs, "Suplemento pagado ✅", "Tu pago fue registrado.", "/cliente/pagos")
    flash("Suplemento marcado como pagado.", "success")
    return redirect(url_for("admin_client_detail", user_id=user_id))


@app.route("/admin/estado", methods=["GET", "POST"])
@admin_required
def admin_gym_status():
    if request.method == "POST":
        status = request.form.get("status", "open")
        message = request.form.get("message", "").strip()

        if not message:
            defaults = {
                "open": "El gym está abierto. ¡Nos vemos!",
                "closed": "Hoy el gym permanece cerrado.",
                "late": "Hoy llego un poco más tarde al gym.",
            }
            message = defaults.get(status, "Actualización del gym.")

        db.set_gym_status(status, message)
        title = f"TAVOGYM {STATUS_ICONS.get(status, '')} {STATUS_LABELS.get(status, status)}"
        db.create_broadcast_notification(title, message, "gym_status")

        subs = db.get_all_push_subscriptions()
        sent = send_push_to_subscriptions(subs, title, message, "/cliente")
        if not vapid_configured():
            flash("Estado publicado. Push NO configurado: agregá VAPID keys en Render.", "error")
        elif sent == 0:
            flash(
                f"Estado publicado en la app. Push a 0 celulares ({len(subs)} suscriptores). "
                "Los clientes deben tocar 'Activar notificaciones' en su celular.",
                "error",
            )
        else:
            flash(f"Estado publicado. Push enviados a {sent} celular(es).", "success")
        return redirect(url_for("admin_gym_status"))

    gym_status = db.get_current_gym_status()
    return render_template("admin/gym_status.html", gym_status=gym_status)


@app.route("/admin/notificar", methods=["GET", "POST"])
@admin_required
def admin_notify():
    clients = db.get_all_clients()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        target = request.form.get("target", "all")

        if not title or not body:
            flash("Completá título y mensaje.", "error")
            return render_template("admin/notify.html", clients=clients)

        sent = 0
        if target == "all":
            db.create_broadcast_notification(title, body)
            subs = db.get_all_push_subscriptions()
            sent = send_push_to_subscriptions(subs, title, body, "/cliente")
        else:
            user_id = int(target)
            db.create_notification(user_id, title, body)
            subs = db.get_client_push_subscriptions(user_id)
            sent = send_push_to_subscriptions(subs, title, body, "/cliente")

        if not vapid_configured():
            flash("Aviso guardado en la app. Push NO configurado: agregá VAPID keys en Render.", "error")
        elif sent == 0:
            flash(
                f"Aviso guardado en la app. Push a 0 celulares ({len(subs)} suscriptores). "
                "El cliente debe activar notificaciones en su celular.",
                "error",
            )
        else:
            flash(f"Aviso enviado. Push entregados a {sent} celular(es).", "success")
        return redirect(url_for("admin_notify"))

    return render_template("admin/notify.html", clients=clients)


@app.route("/admin/deudores")
@admin_required
def admin_debtors():
    clients = db.get_all_clients()
    debtors = [
        c
        for c in clients
        if c["unpaid_months"] > 0 or c["supplement_debt"] > 0
    ]
    return render_template("admin/debtors.html", debtors=debtors)


# ─── Client routes ──────────────────────────────────────────


@app.route("/cliente")
def client_dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    if current_user.role == "admin":
        return redirect(url_for("admin_dashboard"))

    summary = db.get_client_summary(current_user.id)
    notifications = db.get_user_notifications(current_user.id, 10)
    gym_status = db.get_current_gym_status()
    return render_template(
        "client/dashboard.html",
        summary=summary,
        notifications=notifications,
        gym_status=gym_status,
    )


@app.route("/cliente/pagos")
def client_payments():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    if current_user.role == "admin":
        return redirect(url_for("admin_dashboard"))

    summary = db.get_client_summary(current_user.id)
    return render_template("client/payments.html", summary=summary)


@app.route("/cliente/notificaciones")
def client_notifications():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))

    notifications = db.get_user_notifications(current_user.id, 50)
    return render_template("client/notifications.html", notifications=notifications)


@app.route("/cliente/notificaciones/<int:notif_id>/leer", methods=["POST"])
def client_mark_read(notif_id):
    if not current_user.is_authenticated:
        return jsonify({"ok": False}), 401
    db.mark_notification_read(notif_id, current_user.id)
    return jsonify({"ok": True})


# ─── API routes (PWA) ───────────────────────────────────────


@app.route("/api/gym-status")
def api_gym_status():
    status = db.get_current_gym_status()
    return jsonify(status or {})


@app.route("/api/push/subscribe", methods=["POST"])
def api_push_subscribe():
    if not current_user.is_authenticated:
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"ok": False}), 400

    db.save_push_subscription(
        current_user.id,
        data["endpoint"],
        data["keys"]["p256dh"],
        data["keys"]["auth"],
    )
    return jsonify({"ok": True})


@app.route("/manifest.json")
def manifest():
    return app.send_static_file("manifest.json")


@app.route("/sw.js")
def service_worker():
    response = app.send_static_file("sw.js")
    response.headers["Content-Type"] = "application/javascript"
    response.headers["Service-Worker-Allowed"] = "/"
    return response


# ─── Init ───────────────────────────────────────────────────

with app.app_context():
    db.init_db()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
