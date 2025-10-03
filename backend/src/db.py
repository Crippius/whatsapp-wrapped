import os
from pathlib import Path
import sqlite3
from typing import Optional
import urllib.parse as urlparse

try:
    import psycopg2  # noqa: F401

    HAS_PG = True
except Exception:
    HAS_PG = False


# Database path configuration compatible with Render and local dev
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Parse and validate DATABASE_URL if present
if DATABASE_URL:
    try:
        url = urlparse.urlparse(DATABASE_URL)
        if not url.hostname or not url.password or not url.username or not url.path:
            print("[DB] Warning: Invalid DATABASE_URL format")
            DATABASE_URL = ""
    except Exception as e:
        print(f"[DB] Warning: Could not parse DATABASE_URL: {e}")
        DATABASE_URL = ""

USE_POSTGRES = DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith(
    "postgresql://"
)

# SQLite path used as fallback
SQLITE_PATH = (
    "/opt/render/project/src/analytics.db"
    if os.getenv("RENDER")
    else str(Path(__file__).resolve().parent.parent / "analytics.db")
)


def _get_connection():
    """Return a DB connection depending on environment."""
    if USE_POSTGRES and HAS_PG:
        try:
            print("[DB] Attempting PostgreSQL connection...")
            conn = psycopg2.connect(
                DATABASE_URL,
                connect_timeout=5  # 5 seconds timeout
            )
            print("[DB] Successfully connected to PostgreSQL")
            return conn
        except Exception as e:
            print(f"[DB] PostgreSQL connection failed: {e}")
            print("[DB] Falling back to SQLite")
            return sqlite3.connect(SQLITE_PATH)
    print("[DB] Using SQLite")
    return sqlite3.connect(SQLITE_PATH)


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = _get_connection()
    try:
        c = conn.cursor()
        # PDF generations table: one row per request
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS pdf_generations (
                id TEXT PRIMARY KEY,
                timestamp TIMESTAMP,
                language TEXT,
                status TEXT,
                error TEXT,
                processing_time INTEGER
            )
            """
        )

        # Chat analytics table: anonymous aggregates only
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_analytics (
                request_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP,
                lang TEXT,
                is_group INTEGER,
                participants_count INTEGER,
                total_messages INTEGER,
                active_days INTEGER,
                start_date TEXT,
                end_date TEXT,
                avg_msgs_per_day REAL,
                most_active_weekday INTEGER,
                most_active_month TEXT,
                files_shared_count INTEGER,
                avg_message_length_words REAL,
                response_seconds_typical INTEGER
            )
            """
        )

        # Daily message counts table
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_message_counts (
                request_id TEXT NOT NULL,
                day TEXT NOT NULL,
                message_count INTEGER NOT NULL,
                PRIMARY KEY (request_id, day)
            )
            """
        )

        # Most used words table
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS most_used_words (
                request_id TEXT NOT NULL,
                word TEXT NOT NULL,
                count INTEGER NOT NULL,
                rank INTEGER NOT NULL,
                PRIMARY KEY (request_id, word)
            )
            """
        )

        # Most used emojis table
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS most_used_emojis (
                request_id TEXT NOT NULL,
                emoji TEXT NOT NULL,
                count INTEGER NOT NULL,
                rank INTEGER NOT NULL,
                PRIMARY KEY (request_id, emoji)
            )
            """
        )

        conn.commit()
        print("[DB] Tables created successfully")
    finally:
        conn.close()


def save_pdf_generation(
    request_id: str,
    language: str,
    status: str,
    processing_time_ms: Optional[int],
    error: Optional[str] = None,
) -> None:
    """Insert or update a pdf_generation record.

    :param request_id: unique ID for the request
    :param language: language code used for the PDF generation
    :param status: status of the generation ('started', 'completed', 'failed')
    :param processing_time_ms: processing time in milliseconds (None if not completed)
    :param error: error message if status is 'failed'"""
    conn = _get_connection()
    try:
        c = conn.cursor()
        if USE_POSTGRES and HAS_PG:
            c.execute(
                """
                INSERT INTO pdf_generations (id, timestamp, language, status, error, processing_time)
                VALUES (%s, NOW(), %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    timestamp = EXCLUDED.timestamp,
                    language = EXCLUDED.language,
                    status = EXCLUDED.status,
                    error = EXCLUDED.error,
                    processing_time = EXCLUDED.processing_time
                """,
                (request_id, language, status, error, processing_time_ms),
            )
        else:
            c.execute(
                """
                INSERT OR REPLACE INTO pdf_generations (
                    id, timestamp, language, status, error, processing_time
                ) VALUES (
                    ?, datetime('now'), ?, ?, ?, ?
                )
                """,
                (request_id, language, status, error, processing_time_ms),
            )
        conn.commit()
        print("[DB] PDF generation data saved successfully")
    finally:
        conn.close()


def _save_daily_message_counts(cursor, request_id: str, daily_counts: list) -> None:
    """Save daily message counts for a request."""
    if not daily_counts:
        return

    # Clear existing data for this request
    if USE_POSTGRES and HAS_PG:
        cursor.execute(
            "DELETE FROM daily_message_counts WHERE request_id = %s", (request_id,)
        )
    else:
        cursor.execute(
            "DELETE FROM daily_message_counts WHERE request_id = ?", (request_id,)
        )

    # Insert new data
    for day, count in daily_counts:
        if USE_POSTGRES and HAS_PG:
            cursor.execute(
                "INSERT INTO daily_message_counts (request_id, day, message_count) VALUES (%s, %s, %s)",
                (request_id, day, count),
            )
        else:
            cursor.execute(
                "INSERT INTO daily_message_counts (request_id, day, message_count) VALUES (?, ?, ?)",
                (request_id, day, count),
            )


def _save_most_used_words(cursor, request_id: str, word_counts: list) -> None:
    """Save most used words for a request."""
    if not word_counts:
        return

    # Clear existing data for this request
    if USE_POSTGRES and HAS_PG:
        cursor.execute(
            "DELETE FROM most_used_words WHERE request_id = %s", (request_id,)
        )
    else:
        cursor.execute(
            "DELETE FROM most_used_words WHERE request_id = ?", (request_id,)
        )

    # Insert new data (max 100 words)
    for rank, (word, count) in enumerate(word_counts[:100], 1):
        if USE_POSTGRES and HAS_PG:
            cursor.execute(
                "INSERT INTO most_used_words (request_id, word, count, rank) VALUES (%s, %s, %s, %s)",
                (request_id, word, count, rank),
            )
        else:
            cursor.execute(
                "INSERT INTO most_used_words (request_id, word, count, rank) VALUES (?, ?, ?, ?)",
                (request_id, word, count, rank),
            )


def _save_most_used_emojis(cursor, request_id: str, emoji_counts: list) -> None:
    """Save most used emojis for a request."""
    if not emoji_counts:
        return

    # Clear existing data for this request
    if USE_POSTGRES and HAS_PG:
        cursor.execute(
            "DELETE FROM most_used_emojis WHERE request_id = %s", (request_id,)
        )
    else:
        cursor.execute(
            "DELETE FROM most_used_emojis WHERE request_id = ?", (request_id,)
        )

    # Insert new data (max 15 emojis)
    for rank, (emoji, count) in enumerate(emoji_counts[:15], 1):
        if USE_POSTGRES and HAS_PG:
            cursor.execute(
                "INSERT INTO most_used_emojis (request_id, emoji, count, rank) VALUES (%s, %s, %s, %s)",
                (request_id, emoji, count, rank),
            )
        else:
            cursor.execute(
                "INSERT INTO most_used_emojis (request_id, emoji, count, rank) VALUES (?, ?, ?, ?)",
                (request_id, emoji, count, rank),
            )


def save_chat_analytics(request_id: str, analytics: dict) -> None:
    """Persist anonymous chat analytics aggregates for a request.

    :param request_id: unique ID for the request
    :param analytics: dictionary containing analytics data"""
    conn = _get_connection()
    try:
        c = conn.cursor()
        params = (
            request_id,
            analytics.get("lang"),
            int(bool(analytics.get("is_group"))),
            analytics.get("participants_count"),
            analytics.get("total_messages"),
            analytics.get("active_days"),
            analytics.get("start_date"),
            analytics.get("end_date"),
            analytics.get("avg_msgs_per_day"),
            analytics.get("most_active_weekday"),
            analytics.get("most_active_month"),
            analytics.get("files_shared_count"),
            analytics.get("avg_message_length_words"),
            analytics.get("response_seconds_typical"),
        )
        if USE_POSTGRES and HAS_PG:
            c.execute(
                """
                INSERT INTO chat_analytics (
                    request_id, timestamp, lang, is_group, participants_count,
                    total_messages, active_days, start_date, end_date,
                    avg_msgs_per_day, most_active_weekday, most_active_month,
                    files_shared_count, avg_message_length_words, response_seconds_typical
                ) VALUES (
                    %s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (request_id) DO UPDATE SET
                    timestamp = EXCLUDED.timestamp,
                    lang = EXCLUDED.lang,
                    is_group = EXCLUDED.is_group,
                    participants_count = EXCLUDED.participants_count,
                    total_messages = EXCLUDED.total_messages,
                    active_days = EXCLUDED.active_days,
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    avg_msgs_per_day = EXCLUDED.avg_msgs_per_day,
                    most_active_weekday = EXCLUDED.most_active_weekday,
                    most_active_month = EXCLUDED.most_active_month,
                    files_shared_count = EXCLUDED.files_shared_count,
                    avg_message_length_words = EXCLUDED.avg_message_length_words,
                    response_seconds_typical = EXCLUDED.response_seconds_typical
                """,
                params,
            )
        else:
            c.execute(
                """
                INSERT OR REPLACE INTO chat_analytics (
                    request_id, timestamp, lang, is_group, participants_count,
                    total_messages, active_days, start_date, end_date,
                    avg_msgs_per_day, most_active_weekday, most_active_month,
                    files_shared_count, avg_message_length_words, response_seconds_typical
                ) VALUES (
                    ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                params,
            )

        # Save additional analytics data
        if "daily_message_counts" in analytics:
            _save_daily_message_counts(c, request_id, analytics["daily_message_counts"])

        if "most_used_words" in analytics:
            _save_most_used_words(c, request_id, analytics["most_used_words"])

        if "most_used_emojis" in analytics:
            _save_most_used_emojis(c, request_id, analytics["most_used_emojis"])

        conn.commit()
        print("[DB] Chat analytics data saved successfully")
    finally:
        conn.close()
