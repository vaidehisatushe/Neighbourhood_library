from server.db import get_conn
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError
from server.logger import get_logger

logger = get_logger('books_service')

def create_book(data):
    with get_conn() as conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO books(isbn, title, author, publisher, published_date, created_at, updated_at)
                    VALUES (%s,%s,%s,%s,%s, now(), now()) RETURNING *
                """, (data.get('isbn'), data['title'], data.get('author'), data.get('publisher'), data.get('published_date')))
                row = cur.fetchone()
            conn.commit()
            logger.info('book_created', extra={'book_id': row['id']})
            return row
        except IntegrityError:
            conn.rollback()
            logger.warning('create_book_duplicate', extra={'isbn': data.get('isbn')})
            raise ValueError('ALREADY_EXISTS')
        except Exception:
            conn.rollback()
            logger.exception('create_book_failed')
            raise

def update_book(data):
    with get_conn() as conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    UPDATE books SET isbn=%s, title=%s, author=%s, publisher=%s, published_date=%s, updated_at=now()
                    WHERE id=%s RETURNING *
                """, (data.get('isbn'), data['title'], data.get('author'), data.get('publisher'), data.get('published_date'), data['id']))
                row = cur.fetchone()
            if row:
                conn.commit()
                logger.info('book_updated', extra={'book_id': row['id']})
                return row
            conn.rollback()
            return None
        except IntegrityError:
            conn.rollback()
            logger.warning('update_book_duplicate', extra={'isbn': data.get('isbn')})
            raise ValueError('ALREADY_EXISTS')
        except Exception:
            conn.rollback()
            logger.exception('update_book_failed')
            raise

def delete_book(book_id):
    with get_conn() as conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if book is currently borrowed
                cur.execute("SELECT id FROM borrowings WHERE book_id=%s AND status='BORROWED'", (book_id,))
                if cur.fetchone():
                    raise ValueError('CANNOT_DELETE_BORROWED')
                
                cur.execute("DELETE FROM books WHERE id=%s RETURNING id", (book_id,))
                row = cur.fetchone()
            if row:
                conn.commit()
                logger.info('book_deleted', extra={'book_id': book_id})
                return True
            conn.rollback()
            return False
        except ValueError:
            conn.rollback()
            raise
        except Exception:
            conn.rollback()
            logger.exception('delete_book_failed')
            raise

def get_book(book_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM books WHERE id=%s', (book_id,))
            return cur.fetchone()

def list_books():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM books ORDER BY id')
            return cur.fetchall()
