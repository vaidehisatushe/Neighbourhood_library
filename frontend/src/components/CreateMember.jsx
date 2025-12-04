import React, { useState } from 'react'
import axios from 'axios'
import Message from './Message'

export default function CreateMember({ onCreated }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [address, setAddress] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  function validate() {
    if (!name.trim()) return 'Name is required'
    if (email && !/^\S+@\S+\.\S+$/.test(email)) return 'Email looks invalid'
    return ''
  }

  async function submit(e) {
    e.preventDefault()
    setError('')
    setSuccess('')
    const v = validate()
    if (v) { setError(v); return }
    try {
      const res = await axios.post('http://localhost:8080/members', { name, email, phone, address })
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
      <div><label>Name: <input value={name} onChange={e=>setName(e.target.value)} required /></label></div>
      <div><label>Email: <input value={email} onChange={e=>setEmail(e.target.value)} /></label></div>
      <div><label>Phone: <input value={phone} onChange={e=>setPhone(e.target.value)} /></label></div>
      <div><label>Address: <input value={address} onChange={e=>setAddress(e.target.value)} /></label></div>
      <button type="submit">Create</button>
    </form>
  )
}
