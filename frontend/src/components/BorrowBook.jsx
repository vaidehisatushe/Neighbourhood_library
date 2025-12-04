import React, { useState, useEffect } from 'react'
import axios from 'axios'
import Message from './Message'

// Allows selecting a book and member to create a borrow record via POST /borrow
export default function BorrowBook() {
  const [books, setBooks] = useState([])
  const [members, setMembers] = useState([])
  const [bookId, setBookId] = useState('')
  const [memberId, setMemberId] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(()=>{ fetchBooks(); fetchMembers() }, [])
  async function fetchBooks() {
    try { const res = await axios.get('http://localhost:8080/books'); setBooks(res.data) } catch(e){ console.error(e); setError('Failed to fetch books') }
  }
  async function fetchMembers() {
    try { const res = await axios.get('http://localhost:8080/members'); setMembers(res.data) } catch(e){ console.error(e); setError('Failed to fetch members') }
  }
  async function submit(e) {
    e.preventDefault()
    setError(''); setSuccess('')
    if (!bookId || !memberId) { setError('Please select a book and member'); return }
    try {
      const res = await axios.post('http://localhost:8080/borrow', { book_id: Number(bookId), member_id: Number(memberId) })
      setSuccess('Borrowed: id ' + res.data.id)
      setBookId(''); setMemberId('')
    } catch(err) {
      console.error(err)
      const msg = err?.response?.data?.error || err?.response?.data?.message || err?.message || 'Failed to borrow'
      setError(msg)
    }
  }

  return (
    <form onSubmit={submit}>
      <h2>Borrow Book</h2>
      {error && <Message type="error">{error}</Message>}
      {success && <Message type="success">{success}</Message>}
      <div>
        <label>Book:
          <select value={bookId} onChange={e=>setBookId(e.target.value)} required>
            <option value=''>--select--</option>
            {books.map(b=> <option key={b.id} value={b.id}>{b.title} (id:{b.id})</option>)}
          </select>
        </label>
      </div>
      <div>
        <label>Member:
          {members.length === 0 ? (
            <div>
              <div>No members found. Add a member first (Members → Create Member).</div>
              <select disabled><option>--no members--</option></select>
            </div>
          ) : (
            <select value={memberId} onChange={e=>setMemberId(e.target.value)} required>
              <option value=''>--select--</option>
              {members.map(m=> <option key={m.id} value={m.id}>{m.name} (id:{m.id})</option>)}
            </select>
          )}
        </label>
      </div>
      <button type="submit" disabled={!bookId || !memberId}>Borrow</button>
    </form>
  )
}
