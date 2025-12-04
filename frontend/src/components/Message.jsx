import React from 'react'

export default function Message({ type = 'info', children }) {
  const colors = { error: '#ffdddd', success: '#ddffdd', info: '#eef' }
  const border = { error: '#ff8888', success: '#88cc88', info: '#aab' }
  return (
    <div style={{ background: colors[type] || colors.info, border: `1px solid ${border[type] || border.info}`, padding: '8px', borderRadius: '4px', margin: '8px 0' }}>
      {children}
    </div>
  )
}
