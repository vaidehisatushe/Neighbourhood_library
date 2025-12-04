# Sample Python client to exercise the gRPC service.
import grpc
import os
import sys

# Try direct imports, and if they fail (e.g. running from the clients/ folder),
# add the project root to sys.path and retry so generated modules can be found.
try:
    import library_pb2
    import library_pb2_grpc
except ImportError:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    import library_pb2
    import library_pb2_grpc

from google.protobuf.timestamp_pb2 import Timestamp

def main():
    channel = grpc.insecure_channel('localhost:50051')
    client = library_pb2_grpc.LibraryServiceStub(channel)

    # Create a book
    b = library_pb2.Book(title='The Hobbit', author='J.R.R. Tolkien')
    resp = client.CreateBook(library_pb2.CreateBookRequest(book=b))
    print('Created book:', resp.book)

    # Create a member
    m = library_pb2.Member(name='Alice', email='alice@example.com')
    mem = client.CreateMember(library_pb2.CreateMemberRequest(member=m))
    print('Created member:', mem.member)

    # Borrow the book
    borrow = client.BorrowBook(library_pb2.BorrowBookRequest(book_id=resp.book.id, member_id=mem.member.id))
    print('Borrowed:', borrow.borrowing)

    # List borrowed by member
    list_resp = client.ListBorrowedByMember(library_pb2.ListBorrowedByMemberRequest(member_id=mem.member.id))
    print('Active borrows:', list_resp.borrowings)

if __name__ == '__main__':
    main()
