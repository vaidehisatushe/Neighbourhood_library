import React, { useEffect, useState } from 'react'
import axios from 'axios'
import Message from './Message'

// Fetches list of books from the Node gateway and displays them.
export default function BookList() {
  const [books, setBooks] = useState([])
  const [error, setError] = useState('')
  useEffect(() => { fetchBooks() }, [])
  async function fetchBooks() {
    setError('')
    try {
      const res = await axios.get('http://localhost:8080/books')
      setBooks(res.data)
    } catch (e) { console.error(e); setError('Failed to fetch books') }
  }
  return (
    <div>
      <h2>Books</h2>
      {error && <Message type="error">{error}</Message>}
      <table>
        <thead><tr><th>ID</th><th>Title</th><th>Author</th><th>ISBN</th></tr></thead>
        <tbody>
          {books.map(b=> <tr key={b.id}><td>{b.id}</td><td>{b.title}</td><td>{b.author}</td><td>{b.isbn}</td></tr>)}
        </tbody>
      </table>
    </div>
  )
}
