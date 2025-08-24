
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import ChatPage from '@/pages/ChatPage'
import FileUpload from '@/pages/FileUpload'
import LoginPage from '@/pages/LoginPage'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/upload" element={<FileUpload />} />
        <Routh path="/login" element={<LoginPage />} />
      </Routes>
    </Router>
  )
}

export default App
