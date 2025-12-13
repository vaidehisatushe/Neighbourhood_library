import React, { useEffect, useState } from 'react'
import api from '../services/api' // Use centralized api service
import Message from './Message'

// Displays a list of members and basic contact info
export default function MemberList({ onCreate, onSelect }) {
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [editingMember, setEditingMember] = useState(null)
  const [editForm, setEditForm] = useState({ name: '', email: '', phone: '', address: '' })

  useEffect(() => { fetchMembers() }, [])

  async function fetchMembers() {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/members')
      setMembers(res.data)
    } catch (e) {
      console.error('Failed to fetch members', e)
      setMembers([])
      setError('Failed to load members')
    } finally {
      setLoading(false)
    }
  }

  async function deleteMember(id, e) {
    e.stopPropagation() // prevent row click
    if (!window.confirm('Are you sure you want to delete this member?')) return
    try {
      await api.delete(`/members/${id}`)
      fetchMembers()
    } catch (err) {
      console.error(err)
      const msg = err?.response?.data?.error || 'Failed to delete member'
      setError(msg)
    }
  }

  function openEdit(member, e) {
    e.stopPropagation()
    setEditingMember(member.id)
    setEditForm({
      name: member.name || '',
      email: member.email || '',
      phone: member.phone || '',
      address: member.address || ''
    })
  }

  async function updateMember(e) {
    e.preventDefault()
    try {
      await api.put(`/members/${editingMember}`, editForm)
      setEditingMember(null)
      fetchMembers()
    } catch (err) {
      console.error(err)
      setError('Failed to update member')
    }
  }

  return (
    <div>
      <h2>Members</h2>
      <div style={{ marginBottom: '8px' }}>
        <button onClick={() => { if (onCreate) onCreate(); }}>Create Member</button>
        <button onClick={() => fetchMembers()} style={{ marginLeft: '8px' }}>Refresh</button>
      </div>
      {loading ? <div>Loading...</div> : (
        error ? <div style={{ color: 'red' }}>{error}</div> : (
          members.length === 0 ? (
            <div>No members yet. Use the "Create Member" button above.</div>
          ) : (
            <table>
              <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Actions</th></tr></thead>
              <tbody>
                {members.map(m => (
                  <tr key={m.id} style={{ cursor: onSelect ? 'pointer' : 'default' }} onClick={() => onSelect && onSelect(m.id)}>
                    <td>{m.id}</td><td>{m.name}</td><td>{m.email}</td><td>{m.phone}</td>
                    <td>
                      <button onClick={(e) => openEdit(m, e)}>Edit</button>
                      <button onClick={(e) => deleteMember(m.id, e)} style={{ marginLeft: 8, color: 'red' }}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        )
      )}

      {editingMember && (
        <div className="modal-backdrop" onClick={() => setEditingMember(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>Edit Member #{editingMember}</h3>
            <form onSubmit={updateMember}>
              <div style={{ marginBottom: 8 }}><label>Name: <input value={editForm.name} onChange={e => setEditForm({ ...editForm, name: e.target.value })} required /></label></div>
              <div style={{ marginBottom: 8 }}><label>Email: <input value={editForm.email} onChange={e => setEditForm({ ...editForm, email: e.target.value })} /></label></div>
              <div style={{ marginBottom: 8 }}><label>Phone: <input value={editForm.phone} onChange={e => setEditForm({ ...editForm, phone: e.target.value })} /></label></div>
              <div style={{ marginBottom: 8 }}><label>Address: <input value={editForm.address} onChange={e => setEditForm({ ...editForm, address: e.target.value })} /></label></div>
              <div style={{ marginTop: 10 }}>
                <button type="submit">Save</button>
                <button type="button" onClick={() => setEditingMember(null)} style={{ marginLeft: 8 }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
