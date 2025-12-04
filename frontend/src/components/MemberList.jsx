import React, { useEffect, useState } from 'react'
import axios from 'axios'

// Displays a list of members and basic contact info
export default function MemberList({ onCreate, onSelect }) {
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => { fetchMembers() }, [])

  async function fetchMembers() {
    setLoading(true)
    setError('')
    try {
      const res = await axios.get('http://localhost:8080/members')
      setMembers(res.data)
    } catch (e) {
      console.error('Failed to fetch members', e)
      setMembers([])
      setError('Failed to load members')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Members</h2>
      <div style={{marginBottom: '8px'}}>
        <button onClick={() => { if (onCreate) onCreate(); }}>Create Member</button>
        <button onClick={() => fetchMembers()} style={{marginLeft: '8px'}}>Refresh</button>
      </div>
      {loading ? <div>Loading...</div> : (
        error ? <div style={{color: 'red'}}>{error}</div> : (
          members.length === 0 ? (
            <div>No members yet. Use the "Create Member" button above.</div>
          ) : (
            <table>
              <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th></tr></thead>
              <tbody>
                {members.map(m => (
                  <tr key={m.id} style={{cursor: onSelect ? 'pointer' : 'default'}} onClick={() => onSelect && onSelect(m.id)}>
                    <td>{m.id}</td><td>{m.name}</td><td>{m.email}</td><td>{m.phone}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        )
      )}
    </div>
  )
}
