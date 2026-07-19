import React from 'react'
import Header from './components/Header'

export default function App() {
  return (
    <div style={{ fontFamily: 'sans-serif', margin: '0 auto', maxWidth: '800px' }}>
      <Header />
      <main style={{ padding: '1rem' }}>
        <p>Welcome to the application!</p>
        <UserProfile />
      </main>
    </div>
  )
}
