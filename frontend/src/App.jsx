import React, { useState } from 'react'
import BookList from './components/BookList'
import CreateBook from './components/CreateBook'
import BorrowBook from './components/BorrowBook'
import MemberList from './components/MemberList'
import CreateMember from './components/CreateMember'
import MemberDetail from './components/MemberDetail'

export default function App() {
  const [page, setPage] = useState('list')
  const [selectedMemberId, setSelectedMemberId] = useState(null)

  function openCreateMember() { setPage('createMember') }
  function openMemberDetail(id) { setSelectedMemberId(id); setPage('memberDetail') }
  function backToMembers() { setSelectedMemberId(null); setPage('members') }

  return (
    <div className="container">
      <header><h1>Neighborhood Library</h1>
        <nav>
          <button onClick={() => setPage('list')}>List Books</button>
          <button onClick={() => setPage('create')}>Create Book</button>
          <button onClick={() => setPage('borrow')}>Borrow Book</button>
          <button onClick={() => setPage('members')}>Members</button>
        </nav>
      </header>
      <main>
        {page === 'list' && <BookList />}
        {page === 'create' && <CreateBook />}
        {page === 'borrow' && <BorrowBook />}
        {page === 'members' && <MemberList onCreate={openCreateMember} onSelect={openMemberDetail} />}
        {page === 'createMember' && <CreateMember onCreated={() => setPage('members')} />}
        {page === 'memberDetail' && <MemberDetail memberId={selectedMemberId} onBack={backToMembers} />}
      </main>
    </div>
  )
}
