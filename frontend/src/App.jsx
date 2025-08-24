
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import ChatPage from '@/pages/ChatPage'
import FileUpload from '@/pages/FileUpload'
import LoginPage from '@/pages/LoginPage'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<div className="p-8 text-center"><h1 className="text-2xl font-bold">Policy Compliance App</h1><p className="mt-4">Welcome to the Policy Compliance system</p></div>} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/upload" element={<FileUpload />} />
        <Route path="/login" element={<LoginPage />} />
      </Routes>
    </Router>
  )
}

export default App
