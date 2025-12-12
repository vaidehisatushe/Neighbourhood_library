from server.db import get_conn
from psycopg2.extras import RealDictCursor
from server.logger import get_logger

logger = get_logger('borrowings_service')

def borrow_book(book_id, member_id, due_at=None):
    with get_conn() as conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SELECT id FROM books WHERE id=%s', (book_id,))
                if not cur.fetchone():
                    return None, 'BOOK_NOT_FOUND'
                cur.execute('SELECT id FROM members WHERE id=%s', (member_id,))
                if not cur.fetchone():
                    return None, 'MEMBER_NOT_FOUND'
                cur.execute("SELECT * FROM borrowings WHERE book_id=%s AND status='BORROWED'", (book_id,))
                if cur.fetchone():
                    return None, 'ALREADY_BORROWED'
                cur.execute('INSERT INTO borrowings(book_id, member_id, borrowed_at, due_at, status) VALUES (%s,%s,now(),%s,%s) RETURNING *', (book_id, member_id, due_at, 'BORROWED'))
                row = cur.fetchone()
            conn.commit()
            logger.info('book_borrowed', extra={'book_id': book_id, 'member_id': member_id})
            return row, None
        except Exception:
            conn.rollback()
            logger.exception('borrow_book_failed')
            raise

def return_book(borrowing_id):
    with get_conn() as conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('SELECT * FROM borrowings WHERE id=%s', (borrowing_id,))
                row = cur.fetchone()
                if not row:
                    return None, 'NOT_FOUND'
                if row['status'] != 'BORROWED':
                    return None, 'ALREADY_RETURNED'
                cur.execute("UPDATE borrowings SET returned_at=now(), status='RETURNED' WHERE id=%s RETURNING *", (borrowing_id,))
                updated = cur.fetchone()
            conn.commit()
            logger.info('book_returned', extra={'borrowing_id': borrowing_id})
            return updated, None
        except Exception:
            conn.rollback()
            logger.exception('return_book_failed')
            raise

def list_borrowed_by_member(member_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM borrowings WHERE member_id=%s AND status='BORROWED'", (member_id,))
        return cur.fetchall()
