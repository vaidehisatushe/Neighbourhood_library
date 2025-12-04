-- PostgreSQL schema for Neighborhood Library

CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    isbn VARCHAR(32) UNIQUE,
    title TEXT NOT NULL,
    author TEXT,
    publisher TEXT,
    published_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS members (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS borrowings (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    member_id INTEGER NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    borrowed_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    due_at TIMESTAMP WITH TIME ZONE,
    returned_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(16) NOT NULL DEFAULT 'BORROWED'
);

CREATE INDEX IF NOT EXISTS idx_borrowings_bookid_status ON borrowings(book_id, status);
CREATE INDEX IF NOT EXISTS idx_borrowings_memberid_status ON borrowings(member_id, status);
