import React, { useState } from 'react'
import api from '../services/api'
import Message from './Message'

export default function CreateMember({ onCreated }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  function validate(n, e, p) {
    if (!n) return 'Name is required'
    if (e && !/^\S+@\S+\.\S+$/.test(e)) return 'Email looks invalid'
    if (p && !/^\d+$/.test(p)) return 'Phone must be digits only'
    return ''
  }

  async function submit(e) {
    e.preventDefault()
    setError('')
    setSuccess('')

    const n = name.trim()
    const em = email.trim()
    const p = phone.trim()
    const a = address.trim()

    const v = validate(n, em, p)
    if (v) { setError(v); return }

    try {
      const res = await api.post('/members', { name: n, email: em, phone: p, address: a })
      setSuccess('Member created (id: ' + res.data.id + ')')
      setName(''); setEmail(''); setPhone(''); setAddress('')
      if (onCreated) onCreated(res.data)
    } catch (err) {
      console.error(err)
      const msg = err?.response?.data?.error || err?.response?.data?.message || err?.message || 'Failed to create member'
      setError(msg)
    }
  }

  return (
    <form onSubmit={submit}>
      <h2>Create Member</h2>
      {error && <Message type="error">{error}</Message>}
      {success && <Message type="success">{success}</Message>}
      <div><label>Name: <input value={name} onChange={e => setName(e.target.value)} required /></label></div>
      <div><label>Email: <input value={email} onChange={e => setEmail(e.target.value)} /></label></div>
      <div><label>Phone: <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="Digits only" /></label></div>
      <div><label>Address: <input value={address} onChange={e => setAddress(e.target.value)} /></label></div>
      <button type="submit">Create</button>
    </form>
  )
}
