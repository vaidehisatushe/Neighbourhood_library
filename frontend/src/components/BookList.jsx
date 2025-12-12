import React, { useEffect, useState } from 'react'
import api from '../services/api'
import Message from './Message'
import '../styles.css'

export default function BookList() {
  const [books, setBooks] = useState([])
  const [error, setError] = useState('')
  const [editingBook, setEditingBook] = useState(null)
  const [editForm, setEditForm] = useState({ title: '', author: '', isbn: '' })

  useEffect(() => { fetchBooks() }, [])

  async function fetchBooks() {
    setError('')
    try {
      const res = await api.get('/books')
      setBooks(res.data)
    } catch (e) { console.error(e); setError('Failed to fetch books') }
  }

  async function deleteBook(id) {
    if (!window.confirm('Are you sure you want to delete this book?')) return
    try {
      await api.delete(`/books/${id}`)
      fetchBooks()
    } catch (e) { console.error(e); setError('Failed to delete the book') }
  }

  function openEdit(book) {
    setEditingBook(book.id)
    setEditForm({ title: book.title || '', author: book.author || '', isbn: book.isbn || '' })
  }

  async function updateBook(e) {
    e.preventDefault()
    // trim inputs
    const payload = { title: editForm.title.trim(), author: editForm.author.trim(), isbn: editForm.isbn.trim() }
    if (!payload.title) { setError('Title is required'); return }
    try {
      await api.put(`/books/${editingBook}`, payload)
      setEditingBook(null)
      fetchBooks()
    } catch (e) { console.error(e); setError('Failed to update book') }
  }

  return (
    <div>
      <h2>Books</h2>
      {error && <Message type="error">{error}</Message>}
      <table>
        <thead><tr><th>ID</th><th>Title</th><th>Author</th><th>ISBN</th><th>Actions</th></tr></thead>
        <tbody>
          {books.map(b=> <tr key={b.id}><td>{b.id}</td><td>{b.title}</td><td>{b.author}</td><td>{b.isbn}</td>
            <td>
              <button onClick={() => openEdit(b)}>Edit</button>
              <button onClick={() => deleteBook(b.id)} style={{color:'red', marginLeft:8}}>Delete</button>
            </td>
          </tr>)}
        </tbody>
      </table>

      {editingBook && (
        <div className="modal-backdrop">
          <div className="modal">
            <h3>Edit Book #{editingBook}</h3>
            <form onSubmit={updateBook}>
              <label>Title:</label>
              <input value={editForm.title} onChange={e=>setEditForm({...editForm, title: e.target.value})} required />
              <label>Author:</label>
              <input value={editForm.author} onChange={e=>setEditForm({...editForm, author: e.target.value})} />
              <label>ISBN:</label>
              <input value={editForm.isbn} onChange={e=>setEditForm({...editForm, isbn: e.target.value})} />
              <div style={{marginTop:10}}>
                <button type="submit">Update</button>
                <button type="button" onClick={()=>setEditingBook(null)} style={{marginLeft:8}}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
