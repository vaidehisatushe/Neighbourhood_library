import React, { useEffect, useState } from 'react'
import axios from 'axios'
import Message from './Message'

export default function MemberDetail({ memberId, onBack }) {
  const [member, setMember] = useState(null)
  const [borrowings, setBorrowings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(()=>{ if (memberId) load() }, [memberId])

  async function load() {
    setLoading(true); setError('')
    try {
      const res = await axios.get('http://localhost:8080/members')
      const m = res.data.find(x=>x.id === Number(memberId))
      setMember(m || null)
      const br = await axios.get(`http://localhost:8080/member/${memberId}/borrowed`)
      setBorrowings(br.data)
    } catch (err) {
      console.error(err)
      setError('Failed to load member details')
    } finally { setLoading(false) }
  }

  if (loading) return <div>Loading...</div>
  if (error) return <Message type="error">{error}</Message>
  if (!member) return <div>Member not found</div>

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
          <thead><tr><th>ID</th><th>Book ID</th><th>Status</th><th>Borrowed At</th><th>Returned At</th></tr></thead>
          <tbody>
            {borrowings.map(b=> (
              <tr key={b.id}><td>{b.id}</td><td>{b.book_id}</td><td>{b.status}</td><td>{b.borrowed_at || ''}</td><td>{b.returned_at || ''}</td></tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
