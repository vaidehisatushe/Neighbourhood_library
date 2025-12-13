#!/usr/bin/env python3
import os, time
from concurrent import futures
import grpc
from google.protobuf.timestamp_pb2 import Timestamp
from threading import Thread
from flask import Flask, jsonify
from server.logger import get_logger
from server.db import init_pool, get_conn
import server.services.books as books_svc
import server.services.members as members_svc
import server.services.borrowings as borrows_svc
import server.validators as validators
import library_pb2, library_pb2_grpc
logger = get_logger('server')

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/library')

health_app = Flask(__name__)

@health_app.route('/health')
def health():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT 1')
                cur.fetchone()
        return jsonify({'status':'ok'})
    except Exception as e:
        logger.exception('health check failed')
        return jsonify({'status':'down', 'error': str(e)}), 500

class LibraryServicer(library_pb2_grpc.LibraryServiceServicer):
    def _row_to_book(self, row):
        b = library_pb2.Book(id=row['id'], isbn=row.get('isbn') or '', title=row['title'], author=row.get('author') or '', publisher=row.get('publisher') or '')
        if row.get('published_date'):
            ts = Timestamp(); ts.FromDatetime(row['published_date']); b.published_date.CopyFrom(ts)
        return b

    def _row_to_member(self, row):
        return library_pb2.Member(id=row['id'], name=row['name'], email=row.get('email') or '', phone=row.get('phone') or '', address=row.get('address') or '')

    def _row_to_borrowing(self, row):
        bor = library_pb2.Borrowing(id=row['id'], book_id=row['book_id'], member_id=row['member_id'], status=row['status'])
        if row.get('borrowed_at'):
            ts = Timestamp(); ts.FromDatetime(row['borrowed_at']); bor.borrowed_at.CopyFrom(ts)
        if row.get('due_at'):
            ts = Timestamp(); ts.FromDatetime(row['due_at']); bor.due_at.CopyFrom(ts)
        if row.get('returned_at'):
            ts = Timestamp(); ts.FromDatetime(row['returned_at']); bor.returned_at.CopyFrom(ts)
        return bor

    def CreateBook(self, request, context):
        try:
            data = { 'title': request.book.title, 'author': request.book.author, 'isbn': request.book.isbn, 'publisher': request.book.publisher }
            val = validators.BookCreate(**data)
            row = books_svc.create_book(val.dict())
            return library_pb2.CreateBookResponse(book=self._row_to_book(row))
        except ValueError as e:
            if str(e) == 'ALREADY_EXISTS':
                context.set_code(grpc.StatusCode.ALREADY_EXISTS); context.set_details('Book already exists (ISBN check)'); return library_pb2.CreateBookResponse()
            logger.exception('CreateBook failed') # Log unexpected ValueErrors
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT); context.set_details(str(e)); return library_pb2.CreateBookResponse()
        except Exception as e:
            logger.exception('CreateBook failed')
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT); context.set_details(str(e)); return library_pb2.CreateBookResponse()

    def UpdateBook(self, request, context):
        try:
            data = { 'id': request.book.id, 'title': request.book.title, 'author': request.book.author, 'isbn': request.book.isbn, 'publisher': request.book.publisher }
            val = validators.BookUpdate(**data)
            row = books_svc.update_book(val.dict())
            if not row:
                context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details('Book not found'); return library_pb2.UpdateBookResponse()
            return library_pb2.UpdateBookResponse(book=self._row_to_book(row))
        except ValueError as e:
            if str(e) == 'ALREADY_EXISTS':
                context.set_code(grpc.StatusCode.ALREADY_EXISTS); context.set_details('Book with this ISBN already exists'); return library_pb2.UpdateBookResponse()
            logger.exception('UpdateBook failed'); context.set_code(grpc.StatusCode.INVALID_ARGUMENT); context.set_details(str(e)); return library_pb2.UpdateBookResponse()
        except Exception as e:
            logger.exception('UpdateBook failed')
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT); context.set_details(str(e)); return library_pb2.UpdateBookResponse()

    def DeleteBook(self, request, context):
        try:
            book_id = request.book_id
            deleted = books_svc.delete_book(book_id)
            if not deleted:
                context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details('Book not found'); return library_pb2.DeleteBookResponse(success=False, message='Not found')
            return library_pb2.DeleteBookResponse(success=True, message='Deleted')
        except Exception as e:
            if str(e) == 'CANNOT_DELETE_BORROWED':
                context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                context.set_details('Cannot delete book that is currently borrowed')
                return library_pb2.DeleteBookResponse(success=False, message='Book is borrowed')
            logger.exception('DeleteBook failed')
            context.set_code(grpc.StatusCode.INTERNAL); context.set_details(str(e)); return library_pb2.DeleteBookResponse(success=False, message=str(e))

    def CreateMember(self, request, context):
        try:
            data = {'name': request.member.name, 'email': request.member.email, 'phone': request.member.phone, 'address': request.member.address}
            val = validators.MemberCreate(**data)
            row = members_svc.create_member(val.dict())
            return library_pb2.CreateMemberResponse(member=self._row_to_member(row))
        except ValueError as e:
            if str(e) == 'ALREADY_EXISTS':
                context.set_code(grpc.StatusCode.ALREADY_EXISTS); context.set_details('Member already exists (Email/Phone check)'); return library_pb2.CreateMemberResponse()
            logger.exception('CreateMember failed'); context.set_code(grpc.StatusCode.INVALID_ARGUMENT); context.set_details(str(e)); return library_pb2.CreateMemberResponse()
        except Exception as e:
            logger.exception('CreateMember failed')
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT); context.set_details(str(e)); return library_pb2.CreateMemberResponse()

    def UpdateMember(self, request, context):
        try:
            data = {'id': request.member.id, 'name': request.member.name, 'email': request.member.email, 'phone': request.member.phone, 'address': request.member.address}
            val = validators.MemberUpdate(**data)
            row = members_svc.update_member(val.dict())
            if not row:
                context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details('Member not found'); return library_pb2.UpdateMemberResponse()
            return library_pb2.UpdateMemberResponse(member=self._row_to_member(row))
        except ValueError as e:
            if str(e) == 'ALREADY_EXISTS':
                context.set_code(grpc.StatusCode.ALREADY_EXISTS); context.set_details('Member email/phone already exists'); return library_pb2.UpdateMemberResponse()
            logger.exception('UpdateMember failed'); context.set_code(grpc.StatusCode.INVALID_ARGUMENT); context.set_details(str(e)); return library_pb2.UpdateMemberResponse()
        except Exception as e:
            logger.exception('UpdateMember failed')
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT); context.set_details(str(e)); return library_pb2.UpdateMemberResponse()

    def DeleteMember(self, request, context):
        try:
            member_id = request.member_id
            deleted = members_svc.delete_member(member_id)
            if not deleted:
                context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details('Member not found'); return library_pb2.DeleteMemberResponse(success=False)
            return library_pb2.DeleteMemberResponse(success=True)
        except Exception as e:
            if str(e) == 'CANNOT_DELETE_MEMBER_WITH_BORROWINGS':
                context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                context.set_details('Cannot delete member with active borrowings')
                return library_pb2.DeleteMemberResponse(success=False)
            logger.exception('DeleteMember failed')
            context.set_code(grpc.StatusCode.INTERNAL); context.set_details(str(e)); return library_pb2.DeleteMemberResponse(success=False)

    def BorrowBook(self, request, context):
        try:
            val = validators.BorrowRequest(book_id=request.book_id, member_id=request.member_id)
            row, err = borrows_svc.borrow_book(val.book_id, val.member_id, val.due_at)
            if err:
                if err == 'BOOK_NOT_FOUND': context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details('Book not found'); return library_pb2.BorrowBookResponse()
                if err == 'MEMBER_NOT_FOUND': context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details('Member not found'); return library_pb2.BorrowBookResponse()
                if err == 'ALREADY_BORROWED': context.set_code(grpc.StatusCode.FAILED_PRECONDITION); context.set_details('Book already borrowed'); return library_pb2.BorrowBookResponse()
            return library_pb2.BorrowBookResponse(borrowing=self._row_to_borrowing(row))
        except Exception as e:
            logger.exception('BorrowBook failed')
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT); context.set_details(str(e)); return library_pb2.BorrowBookResponse()

    def ReturnBook(self, request, context):
        try:
            val = validators.ReturnRequest(borrowing_id=request.borrowing_id)
            row, err = borrows_svc.return_book(val.borrowing_id)
            if err:
                if err == 'NOT_FOUND': context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details('Borrowing not found'); return library_pb2.ReturnBookResponse()
                if err == 'ALREADY_RETURNED': context.set_code(grpc.StatusCode.FAILED_PRECONDITION); context.set_details('Already returned'); return library_pb2.ReturnBookResponse()
            return library_pb2.ReturnBookResponse(borrowing=self._row_to_borrowing(row))
        except Exception as e:
            logger.exception('ReturnBook failed')
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT); context.set_details(str(e)); return library_pb2.ReturnBookResponse()

    def ListBorrowedByMember(self, request, context):
        try:
            rows = borrows_svc.list_borrowed_by_member(request.member_id)
            borrows = [self._row_to_borrowing(r) for r in rows]
            return library_pb2.ListBorrowedByMemberResponse(borrowings=borrows)
        except Exception as e:
            logger.exception('ListBorrowedByMember failed')
            context.set_code(grpc.StatusCode.INTERNAL); context.set_details(str(e)); return library_pb2.ListBorrowedByMemberResponse()

    def ListBooks(self, request, context):
        try:
            rows = books_svc.list_books()
            books = [self._row_to_book(r) for r in rows]
            return library_pb2.ListBooksResponse(books=books)
        except Exception as e:
            logger.exception('ListBooks failed')
            context.set_code(grpc.StatusCode.INTERNAL); context.set_details(str(e)); return library_pb2.ListBooksResponse()

    def ListMembers(self, request, context):
        try:
            rows = members_svc.list_members()
            members = [library_pb2.Member(id=r['id'], name=r['name'], email=r.get('email') or '', phone=r.get('phone') or '', address=r.get('address') or '') for r in rows]
            return library_pb2.ListMembersResponse(members=members)
        except Exception as e:
            logger.exception('ListMembers failed')
            context.set_code(grpc.StatusCode.INTERNAL); context.set_details(str(e)); return library_pb2.ListMembersResponse()

    def GetMember(self, request, context):
        try:
            r = members_svc.get_member(request.id)
            if not r:
                context.set_code(grpc.StatusCode.NOT_FOUND); context.set_details('Member not found'); return library_pb2.GetMemberResponse()
            m = library_pb2.Member(id=r['id'], name=r['name'], email=r.get('email') or '', phone=r.get('phone') or '', address=r.get('address') or '')
            return library_pb2.GetMemberResponse(member=m)
        except Exception as e:
            logger.exception('GetMember failed')
            context.set_code(grpc.StatusCode.INTERNAL); context.set_details(str(e)); return library_pb2.GetMemberResponse()

def serve():
    init_pool(minconn=int(os.environ.get('DB_MINCONN',1)), maxconn=int(os.environ.get('DB_MAXCONN',5)))
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    library_pb2_grpc.add_LibraryServiceServicer_to_server(LibraryServicer(), server)
    port = os.environ.get('GRPC_PORT', '50051')
    server.add_insecure_port(f'[::]:{port}')
    t = Thread(target=lambda: health_app.run(host='0.0.0.0', port=8081), daemon=True)
    t.start()
    server.start()
    logger.info('gRPC server started', extra={'port':port})
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
