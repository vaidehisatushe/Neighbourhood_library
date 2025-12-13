import React, { useEffect, useState } from 'react'
import api from '../services/api' // Use centralized api service
import Message from './Message'

export default function MemberDetail({ memberId, onBack }) {
  const [member, setMember] = useState(null)
  const [borrowings, setBorrowings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => { if (memberId) load() }, [memberId])

  async function load() {
    setLoading(true); setError('')
    try {
      const res = await api.get('/members/' + memberId)
      setMember(res.data)

      try {
        const br = await api.get(`/members/${memberId}/borrowed`)
        setBorrowings(br.data)
      } catch (e) {
        console.error("Failed to fetch history", e)
        setBorrowings([])
      }
    } catch (err) {
      console.error(err)
      setError('Failed to load member details')
    } finally { setLoading(false) }
  }

  async function returnBook(borrowingId) {
    if (!window.confirm('Return this book?')) return
    try {
      await api.post('/return', { borrowing_id: borrowingId })
      load() // reload to update status
    } catch (err) {
      console.error(err)
      setError('Failed to return book')
    }
  }

  if (loading) return <div>Loading...</div>
  if (error) return <Message type="error">{error}</Message>
  if (!member) return <div>Member not found</div>

  function fmt(d) {
    if (!d) return ''
    if (d.seconds) return new Date(Number(d.seconds) * 1000).toLocaleString()
    return new Date(d).toLocaleString()
  }

  return (
    <div>
      <button onClick={onBack}>Back</button>
      <h2>Member: {member.name} (id:{member.id})</h2>
      <div><strong>Email:</strong> {member.email || '—'}</div>
      <div><strong>Phone:</strong> {member.phone || '—'}</div>
      <div><strong>Address:</strong> {member.address || '—'}</div>

      <h3>Borrowing History</h3>
      {borrowings.length === 0 ? <div>No borrowings found.</div> : (
        <table>
          <thead><tr><th>ID</th><th>Book ID</th><th>Status</th><th>Borrowed At</th><th>Returned At</th><th>Action</th></tr></thead>
          <tbody>
            {borrowings.map(b => (
              <tr key={b.id}>
                <td>{b.id}</td><td>{b.book_id}</td><td>{b.status}</td><td>{fmt(b.borrowed_at)}</td><td>{fmt(b.returned_at)}</td>
                <td>
                  {b.status === 'BORROWED' && <button onClick={() => returnBook(b.id)}>Return</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
