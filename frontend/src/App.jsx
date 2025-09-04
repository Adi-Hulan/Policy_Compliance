
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import ChatPage from '@/pages/ChatPage'
import FileUpload from '@/pages/FileUpload'
import LoginPage from '@/pages/LoginPage'
import DocAttach from '@/pages/DocAttach'
import ChatwLang from '@/pages/ChatwLang'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<div className="p-8 text-center"><h1 className="text-2xl font-bold">Policy Compliance App</h1><p className="mt-4">Welcome to the Policy Compliance system</p></div>} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/upload" element={<FileUpload />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/doc-attach" element={<DocAttach />} />
        <Route path="/chat-with-lang" element={<ChatwLang />} />
      </Routes>
    </Router>
  )
}

export default App
