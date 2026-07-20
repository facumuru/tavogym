import sqlite3
from contextlib import contextmanager
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from config import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    DATABASE,
    DATABASE_URL,
    MONTHLY_FEE_DEFAULT,
    RESET_ADMIN,
)

USE_POSTGRES = bool(DATABASE_URL)


def _sql(query):
    return query.replace("?", "%s") if USE_POSTGRES else query


def get_connection():
    if USE_POSTGRES:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


class _CursorWrapper:
    def __init__(self, cursor, is_postgres):
        self._cursor = cursor
        self._is_postgres = is_postgres

    def fetchone(self):
        row = self._cursor.fetchone()
        return row_to_dict(row)

    def fetchall(self):
        return [row_to_dict(r) for r in self._cursor.fetchall()]


class _ConnectionWrapper:
    def __init__(self, conn):
        self._conn = conn
        self._is_postgres = USE_POSTGRES

    def execute(self, query, params=()):
        sql = _sql(query)
        if self._is_postgres:
            cur = self._conn.cursor()
            cur.execute(sql, params)
            return _CursorWrapper(cur, True)
        cur = self._conn.execute(sql, params)
        return _CursorWrapper(cur, False)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


@contextmanager
def get_db():
    conn = _ConnectionWrapper(get_connection())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _now_sql():
    return "NOW()" if USE_POSTGRES else "datetime('now', 'localtime')"


def init_db():
    with get_db() as conn:
        if USE_POSTGRES:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'client')),
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS monthly_fees (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    amount DOUBLE PRECISION NOT NULL,
                    paid INTEGER NOT NULL DEFAULT 0,
                    paid_at TIMESTAMP,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    UNIQUE(user_id, month, year)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS supplement_debts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    product_name TEXT NOT NULL,
                    amount DOUBLE PRECISION NOT NULL,
                    paid INTEGER NOT NULL DEFAULT 0,
                    paid_at TIMESTAMP,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gym_status (
                    id SERIAL PRIMARY KEY,
                    status TEXT NOT NULL CHECK(status IN ('open', 'closed', 'late')),
                    message TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    type TEXT NOT NULL DEFAULT 'general',
                    read INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS push_subscriptions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    endpoint TEXT NOT NULL UNIQUE,
                    p256dh TEXT NOT NULL,
                    auth TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )
        else:
            conn._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'client')),
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS monthly_fees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    paid INTEGER NOT NULL DEFAULT 0,
                    paid_at TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(user_id, month, year)
                );

                CREATE TABLE IF NOT EXISTS supplement_debts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    paid INTEGER NOT NULL DEFAULT 0,
                    paid_at TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS gym_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT NOT NULL CHECK(status IN ('open', 'closed', 'late')),
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                );

                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    type TEXT NOT NULL DEFAULT 'general',
                    read INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS push_subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    endpoint TEXT NOT NULL UNIQUE,
                    p256dh TEXT NOT NULL,
                    auth TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """
            )

        admin = conn.execute(
            "SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,)
        ).fetchone()
        password_hash = generate_password_hash(ADMIN_PASSWORD)
        if not admin:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, name, phone, role)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    ADMIN_USERNAME,
                    password_hash,
                    "Tavo - Profesor",
                    "",
                    "admin",
                ),
            )
        elif RESET_ADMIN:
            conn.execute(
                """
                UPDATE users SET password_hash = ?
                WHERE username = ? AND role = 'admin'
                """,
                (password_hash, ADMIN_USERNAME),
            )


def row_to_dict(row):
    if row is None:
        return None
    if isinstance(row, dict):
        data = dict(row)
    else:
        data = dict(row)
    for key, value in data.items():
        if hasattr(value, "isoformat"):
            data[key] = value.strftime("%Y-%m-%d %H:%M:%S")
    return data


def get_user_by_id(user_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_dict(row) if row else None


def get_user_by_username(username):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    return row_to_dict(row) if row else None


def verify_password(user, password):
    return check_password_hash(user["password_hash"], password)


def get_all_clients():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT u.*,
                (SELECT COUNT(*) FROM monthly_fees mf
                 WHERE mf.user_id = u.id AND mf.paid = 0) AS unpaid_months,
                (SELECT COALESCE(SUM(amount), 0) FROM supplement_debts sd
                 WHERE sd.user_id = u.id AND sd.paid = 0) AS supplement_debt
            FROM users u
            WHERE u.role = 'client' AND u.active = 1
            ORDER BY u.name
            """
        ).fetchall()
    return rows


def get_client_summary(user_id):
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE id = ? AND role = 'client'", (user_id,)
        ).fetchone()
        if not user:
            return None

        monthly = conn.execute(
            """
            SELECT * FROM monthly_fees
            WHERE user_id = ?
            ORDER BY year DESC, month DESC
            LIMIT 12
            """,
            (user_id,),
        ).fetchall()

        supplements = conn.execute(
            """
            SELECT * FROM supplement_debts
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()

        unpaid_months = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count
            FROM monthly_fees
            WHERE user_id = ? AND paid = 0
            """,
            (user_id,),
        ).fetchone()

        unpaid_supplements = conn.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count
            FROM supplement_debts
            WHERE user_id = ? AND paid = 0
            """,
            (user_id,),
        ).fetchone()

    return {
        "user": user,
        "monthly_fees": monthly,
        "supplements": supplements,
        "unpaid_months_total": unpaid_months["total"],
        "unpaid_months_count": unpaid_months["count"],
        "unpaid_supplements_total": unpaid_supplements["total"],
        "unpaid_supplements_count": unpaid_supplements["count"],
    }


def create_client(username, password, name, phone):
    with get_db() as conn:
        if USE_POSTGRES:
            row = conn.execute(
                """
                INSERT INTO users (username, password_hash, name, phone, role)
                VALUES (?, ?, ?, ?, 'client')
                RETURNING id
                """,
                (username, generate_password_hash(password), name, phone),
            ).fetchone()
            user_id = row["id"]
        else:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, name, phone, role)
                VALUES (?, ?, ?, ?, 'client')
                """,
                (username, generate_password_hash(password), name, phone),
            )
            row = conn.execute("SELECT last_insert_rowid() AS id").fetchone()
            user_id = row["id"]

        now = datetime.now()
        ignore_sql = (
            """
            INSERT INTO monthly_fees (user_id, month, year, amount, paid)
            VALUES (?, ?, ?, ?, 0)
            ON CONFLICT (user_id, month, year) DO NOTHING
            """
            if USE_POSTGRES
            else """
            INSERT OR IGNORE INTO monthly_fees (user_id, month, year, amount, paid)
            VALUES (?, ?, ?, ?, 0)
            """
        )
        conn.execute(ignore_sql, (user_id, now.month, now.year, MONTHLY_FEE_DEFAULT))
    return user_id


def add_monthly_fee(user_id, month, year, amount, notes=""):
    with get_db() as conn:
        if USE_POSTGRES:
            conn.execute(
                """
                INSERT INTO monthly_fees (user_id, month, year, amount, notes)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (user_id, month, year) DO NOTHING
                """,
                (user_id, month, year, amount, notes),
            )
        else:
            conn.execute(
                """
                INSERT OR IGNORE INTO monthly_fees (user_id, month, year, amount, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, month, year, amount, notes),
            )


def mark_monthly_paid(fee_id):
    with get_db() as conn:
        conn.execute(
            f"""
            UPDATE monthly_fees
            SET paid = 1, paid_at = {_now_sql()}
            WHERE id = ?
            """,
            (fee_id,),
        )


def add_supplement_debt(user_id, product_name, amount, notes=""):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO supplement_debts (user_id, product_name, amount, notes)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, product_name, amount, notes),
        )


def mark_supplement_paid(debt_id):
    with get_db() as conn:
        conn.execute(
            f"""
            UPDATE supplement_debts
            SET paid = 1, paid_at = {_now_sql()}
            WHERE id = ?
            """,
            (debt_id,),
        )


def set_gym_status(status, message):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO gym_status (status, message) VALUES (?, ?)",
            (status, message),
        )


def get_current_gym_status():
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM gym_status ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
    return row


def create_notification(user_id, title, body, notif_type="general"):
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO notifications (user_id, title, body, type)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, title, body, notif_type),
        )


def create_broadcast_notification(title, body, notif_type="general"):
    with get_db() as conn:
        clients = conn.execute(
            "SELECT id FROM users WHERE role = 'client' AND active = 1"
        ).fetchall()
        for client in clients:
            conn.execute(
                """
                INSERT INTO notifications (user_id, title, body, type)
                VALUES (?, ?, ?, ?)
                """,
                (client["id"], title, body, notif_type),
            )


def get_user_notifications(user_id, limit=20):
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return rows


def mark_notification_read(notif_id, user_id):
    with get_db() as conn:
        conn.execute(
            """
            UPDATE notifications SET read = 1
            WHERE id = ? AND user_id = ?
            """,
            (notif_id, user_id),
        )


def save_push_subscription(user_id, endpoint, p256dh, auth):
    with get_db() as conn:
        if USE_POSTGRES:
            conn.execute(
                """
                INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (endpoint) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    p256dh = EXCLUDED.p256dh,
                    auth = EXCLUDED.auth
                """,
                (user_id, endpoint, p256dh, auth),
            )
        else:
            conn.execute(
                """
                INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(endpoint) DO UPDATE SET
                    user_id = excluded.user_id,
                    p256dh = excluded.p256dh,
                    auth = excluded.auth
                """,
                (user_id, endpoint, p256dh, auth),
            )


def get_all_push_subscriptions():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM push_subscriptions").fetchall()
    return rows


def get_client_push_subscriptions(user_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM push_subscriptions WHERE user_id = ?", (user_id,)
        ).fetchall()
    return rows


def get_admin_stats():
    with get_db() as conn:
        total_clients = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE role = 'client' AND active = 1"
        ).fetchone()["c"]

        clients_with_debt = conn.execute(
            """
            SELECT COUNT(DISTINCT u.id) AS c FROM users u
            WHERE u.role = 'client' AND u.active = 1 AND (
                EXISTS (SELECT 1 FROM monthly_fees mf WHERE mf.user_id = u.id AND mf.paid = 0)
                OR EXISTS (SELECT 1 FROM supplement_debts sd WHERE sd.user_id = u.id AND sd.paid = 0)
            )
            """
        ).fetchone()["c"]

        total_monthly_debt = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS t FROM monthly_fees WHERE paid = 0"
        ).fetchone()["t"]

        total_supplement_debt = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS t FROM supplement_debts WHERE paid = 0"
        ).fetchone()["t"]

        push_subscribers = conn.execute(
            "SELECT COUNT(*) AS c FROM push_subscriptions"
        ).fetchone()["c"]

    return {
        "total_clients": total_clients,
        "clients_with_debt": clients_with_debt,
        "total_monthly_debt": total_monthly_debt,
        "total_supplement_debt": total_supplement_debt,
        "total_debt": total_monthly_debt + total_supplement_debt,
        "push_subscribers": push_subscribers,
    }
