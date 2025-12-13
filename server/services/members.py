from server.db import get_conn
from psycopg2.extras import RealDictCursor
from psycopg2 import IntegrityError
from server.logger import get_logger

logger = get_logger('members_service')

def create_member(data):
    with get_conn() as conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('INSERT INTO members(name,email,phone,address,created_at,updated_at) VALUES (%s,%s,%s,%s,now(),now()) RETURNING *',
                            (data['name'], data.get('email'), data.get('phone'), data.get('address')))
                row = cur.fetchone()
            conn.commit()
            logger.info('member_created', extra={'member_id': row['id']})
            return row
        except IntegrityError:
            conn.rollback()
            logger.warning('create_member_duplicate', extra={'email': data.get('email')})
            raise ValueError('ALREADY_EXISTS')
        except Exception:
            conn.rollback()
            logger.exception('create_member_failed')
            raise

def update_member(data):
    with get_conn() as conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute('UPDATE members SET name=%s,email=%s,phone=%s,address=%s,updated_at=now() WHERE id=%s RETURNING *',
                            (data['name'], data.get('email'), data.get('phone'), data.get('address'), data['id']))
                row = cur.fetchone()
            if row:
                conn.commit()
                logger.info('member_updated', extra={'member_id': row['id']})
                return row
            conn.rollback()
            return None
        except IntegrityError:
            conn.rollback()
            logger.warning('update_member_duplicate', extra={'email': data.get('email'), 'member_id': data['id']})
            raise ValueError('ALREADY_EXISTS')
        except Exception:
            conn.rollback()
            logger.exception('update_member_failed')
            raise

def delete_member(member_id):
    with get_conn() as conn:
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check for active borrowings
                cur.execute("SELECT id FROM borrowings WHERE member_id=%s AND status='BORROWED'", (member_id,))
                if cur.fetchone():
                    raise ValueError('CANNOT_DELETE_MEMBER_WITH_BORROWINGS')

                cur.execute('DELETE FROM members WHERE id=%s RETURNING id', (member_id,))
                row = cur.fetchone()
            if row:
                conn.commit()
                logger.info('member_deleted', extra={'member_id': member_id})
                return True
            conn.rollback()
            return False
        except ValueError:
            conn.rollback()
            raise
        except Exception:
            conn.rollback()
            logger.exception('delete_member_failed')
            raise

def get_member(member_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM members WHERE id=%s', (member_id,))
            return cur.fetchone()

def list_members():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM members ORDER BY id')
            return cur.fetchall()
