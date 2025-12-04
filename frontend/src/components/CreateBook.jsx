import React, { useState } from 'react'
import axios from 'axios'
import Message from './Message'

// Simple form to create a book via POST /books on the gateway
export default function CreateBook() {
  const [title, setTitle] = useState('')
  const [author, setAuthor] = useState('')
  const [isbn, setIsbn] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  async function submit(e) {
    e.preventDefault()
    setError('')
    setSuccess('')
    try {
      const res = await axios.post('http://localhost:8080/books', { title, author, isbn })
      setSuccess('Created book with id ' + res.data.id)
      setTitle(''); setAuthor(''); setIsbn('')
    } catch (err) {
      console.error(err)
      setError('Failed to create book')
    }
  }

  return (
    <form onSubmit={submit}>
      <h2>Create Book</h2>
      {error && <Message type="error">{error}</Message>}
      {success && <Message type="success">{success}</Message>}
      <div><label>Title: <input value={title} onChange={e=>setTitle(e.target.value)} required /></label></div>
      <div><label>Author: <input value={author} onChange={e=>setAuthor(e.target.value)} /></label></div>
      <div><label>ISBN: <input value={isbn} onChange={e=>setIsbn(e.target.value)} /></label></div>
      <button type="submit">Create</button>
    </form>
  )
}
