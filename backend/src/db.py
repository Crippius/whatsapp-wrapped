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
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
USE_POSTGRES = DATABASE_URL.startswith('postgres://') or DATABASE_URL.startswith('postgresql://')

# SQLite path used as fallback
SQLITE_PATH = (
    '/opt/render/project/src/analytics.db'
    if os.getenv('RENDER') else str(Path(__file__).resolve().parent.parent / 'analytics.db')
)


def _get_connection():
    """Return a DB connection depending on environment."""
    if USE_POSTGRES and HAS_PG:
        return psycopg2.connect(DATABASE_URL)
    return sqlite3.connect(SQLITE_PATH)


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = _get_connection()
    try:
        c = conn.cursor()
        # PDF generations table: one row per request
        c.execute(
            '''
            CREATE TABLE IF NOT EXISTS pdf_generations (
                id TEXT PRIMARY KEY,
                timestamp TIMESTAMP,
                language TEXT,
                status TEXT,
                error TEXT,
                processing_time INTEGER
            )
            '''
        )

        # Chat analytics table: anonymous aggregates only
        c.execute(
            '''
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
            '''
        )

        conn.commit()
    finally:
        conn.close()


def save_pdf_generation(request_id: str, language: str, status: str, processing_time_ms: Optional[int], error: Optional[str] = None) -> None:
    """Insert or update a pdf_generation record."""
    conn = _get_connection()
    try:
        c = conn.cursor()
        if USE_POSTGRES and HAS_PG:
            c.execute(
                '''
                INSERT INTO pdf_generations (id, timestamp, language, status, error, processing_time)
                VALUES (%s, NOW(), %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    timestamp = EXCLUDED.timestamp,
                    language = EXCLUDED.language,
                    status = EXCLUDED.status,
                    error = EXCLUDED.error,
                    processing_time = EXCLUDED.processing_time
                ''',
                (request_id, language, status, error, processing_time_ms)
            )
        else:
            c.execute(
                '''
                INSERT OR REPLACE INTO pdf_generations (
                    id, timestamp, language, status, error, processing_time
                ) VALUES (
                    ?, datetime('now'), ?, ?, ?, ?
                )
                ''',
                (request_id, language, status, error, processing_time_ms)
            )
        conn.commit()
    finally:
        conn.close()


def save_chat_analytics(request_id: str, analytics: dict) -> None:
    """Persist anonymous chat analytics aggregates for a request."""
    conn = _get_connection()
    try:
        c = conn.cursor()
        params = (
            request_id,
            analytics.get('lang'),
            int(bool(analytics.get('is_group'))),
            analytics.get('participants_count'),
            analytics.get('total_messages'),
            analytics.get('active_days'),
            analytics.get('start_date'),
            analytics.get('end_date'),
            analytics.get('avg_msgs_per_day'),
            analytics.get('most_active_weekday'),
            analytics.get('most_active_month'),
            analytics.get('files_shared_count'),
            analytics.get('avg_message_length_words'),
            analytics.get('response_seconds_typical')
        )
        if USE_POSTGRES and HAS_PG:
            c.execute(
                '''
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
                ''', params)
        else:
            c.execute(
                '''
                INSERT OR REPLACE INTO chat_analytics (
                    request_id, timestamp, lang, is_group, participants_count,
                    total_messages, active_days, start_date, end_date,
                    avg_msgs_per_day, most_active_weekday, most_active_month,
                    files_shared_count, avg_message_length_words, response_seconds_typical
                ) VALUES (
                    ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ''', params)
        conn.commit()
    finally:
        conn.close()

