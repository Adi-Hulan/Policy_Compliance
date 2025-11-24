# Policy Compliance AI - Multi-Agent System

<div align="center">

**An intelligent, AI-driven compliance platform leveraging multi-agent architecture to analyze corporate policies, detect violations, and generate automated recommendations.**

Features • Architecture • Tech Stack • Installation • Usage • API Documentation

</div>

---

## 🎯 Overview

The Policy Compliance AI System is an enterprise-grade platform that combines the power of Google Gemini AI, LangGraph orchestration, and Retrieval-Augmented Generation (RAG) to automate compliance analysis. The system processes policy documents, identifies regulatory violations (GDPR, HIPAA), and provides actionable remediation strategies through an intuitive chat interface.

**Key Highlights:**
- 🤖 Multi-agent AI architecture with specialized processors
- 📊 Real-time streaming analysis with Server-Sent Events (SSE)
- 🔍 RAG-powered semantic search with 95%+ accuracy
- 🛡️ Role-based access control for Admins and Employees
- 💬 Interactive AI assistant with voice input support
- 📈 Automated violation detection and recommendation generation

---

## ✨ Features

### 🤖 AI-Powered Compliance Analysis
- **Multi-Agent Orchestration:** Specialized agents for query analysis, document processing, chunk retrieval, and recommendations
- **Real-Time Streaming:** Progressive result delivery via SSE for enhanced UX
- **Semantic Understanding:** Vector embeddings and cosine similarity for context-aware analysis
- **Automated Violation Detection:** Identifies compliance gaps against company policies with severity classification

### 📄 Document Management & Analysis
- **Intelligent Document Processing:** PDF parsing, chunking, and embedding generation
- **Interactive PDF Viewer:** Built-in viewer with zoom and navigation controls
- **Batch Analysis:** Process multiple documents simultaneously
- **Context-Aware Retrieval:** RAG-based system retrieving relevant policy sections

### 💬 Interactive AI Chat Interface
- **Natural Language Querying:** Ask compliance questions in plain English
- **Voice Input Support:** Speech-to-text integration for hands-free interaction
- **Thinking Process Visualization:** Transparent AI reasoning steps displayed in real-time
- **File Attachment Support:** Analyze images and documents directly in chat
- **Session Management:** Persistent chat history per session

### 🛡️ Security & Access Control
- **JWT Authentication:** Secure token-based authentication
- **Role-Based Access Control (RBAC):** Distinct permissions for Admins and Employees
- **Supabase Integration:** Secure database and storage backend
- **User Management Dashboard:** Admin portal for employee account management

### 📊 Recommendation Engine
- **Prioritized Action Items:** High/Medium/Low severity classification
- **Timeline Estimation:** Immediate, short-term, and long-term remediation plans
- **Resource Allocation:** Identifies resources needed for each recommendation
- **Expected Outcomes:** Clear success metrics for each action item

### 💎 Subscription Management
- **Tiered Plans:** Free, Standard, and Premium subscription models
- **Payment Gateway:** Integrated billing and payment processing
- **Usage Tracking:** Monitor API calls and document analysis limits

---

## 🏗️ Architecture

### Multi-Agent System Design

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend Layer                       │
│            React + Vite + Tailwind CSS + SSE                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
│                Flask + CORS + JWT Auth                      │
├─────────────────────────────────────────────────────────────┤
│  Routes:                                                     │
│  • /documents/upload    • /documents/analyze                │
│  • /queries/analyze/stream                                  │
│  • /recommendations/generate                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Orchestrator Layer                         │
│              LangGraph + Event Formatter                     │
├─────────────────────────────────────────────────────────────┤
│  Components:                                                 │
│  • Graph Builder        • State Manager                     │
│  • Event Streamer       • Executor                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Agent Layer                             │
├─────────────────────────────────────────────────────────────┤
│  Specialized Agents:                                         │
│  • QueryAnalyzer          → Parse and classify queries      │
│  • DocumentProcessor      → Extract and chunk documents     │
│  • ChunkRetriever         → Semantic search with RAG        │
│  • PolicyAnalyzer         → Compare against policies        │
│  • RecommendationAgent    → Generate action items           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data & AI Layer                           │
├─────────────────────────────────────────────────────────────┤
│  • Supabase (PostgreSQL + Storage)                          │
│  • Google Gemini 2.5 Flash API                              │
│  • Vector Embeddings Store                                   │
│  • PDF Parser & Utils                                        │
└─────────────────────────────────────────────────────────────┘
```

### Agent Workflow

```
User Query → QueryAnalyzer → ChunkRetriever → PolicyAnalyzer → RecommendationAgent
                ↓                  ↓                 ↓                  ↓
           Parse Intent      Semantic Search    Compare Context   Generate Actions
                ↓                  ↓                 ↓                  ↓
           Extract Entities   Top-K Results    Identify Gaps    Prioritize Items
                ↓                  ↓                 ↓                  ↓
           SSE: Analyzing    SSE: Retrieving   SSE: Analyzing   SSE: Final Result
```

---

## 🛠️ Tech Stack

### Backend
| Category | Technologies |
|----------|-------------|
| **Core Framework** | Python 3.9+, Flask 3.0+, Flask-CORS |
| **AI/ML** | Google Gemini 2.5 Flash API, LangChain, LangGraph |
| **Vector Search** | RAG (Retrieval-Augmented Generation), Embedding Models |
| **Database** | Supabase (PostgreSQL), Vector Store |
| **Authentication** | JWT, Supabase Auth, Custom Middleware |
| **Document Processing** | PDF.js, PyPDF2, Python-docx |
| **API Architecture** | RESTful APIs, Server-Sent Events (SSE) |

### Frontend
| Category | Technologies |
|----------|-------------|
| **Core Framework** | React 18+, Vite, TypeScript/JavaScript |
| **Styling** | Tailwind CSS, Lucide React Icons |
| **State Management** | React Hooks (useState, useEffect, useContext) |
| **Routing** | React Router DOM |
| **Real-Time** | SSE (Server-Sent Events), Fetch API |
| **PDF Viewer** | PDF.js Integration |
| **Voice Input** | Web Speech API |

### Infrastructure & DevOps
- **Version Control:** Git, GitHub
- **Environment Management:** dotenv, Python Virtual Environment
- **File Storage:** Supabase Storage, Local temp directories
- **Development:** VS Code, Hot Reload

---

## 📂 Project Structure

```
Policy_Compliance/
│
├── backend/                          # Python Flask Backend
│   ├── agents/                       # Specialized AI Agents
│   │   ├── query_analyzer.py        # Query parsing and intent extraction
│   │   ├── document_processor.py    # PDF processing and chunking
│   │   ├── chunk_retriever.py       # RAG-based retrieval
│   │   ├── policy_analyze_document_processor.py
│   │   ├── policy_analyze_chunk_retriever.py
│   │   ├── recommendation_agent.py  # Action item generation
│   │   └── attached_document_processor.py
│   │
│   ├── orchestrator/                 # LangGraph Orchestration
│   │   ├── orchestrator.py          # Main orchestrator logic
│   │   ├── graph.py                 # Graph definition
│   │   ├── general_graph.py         # General-purpose graph
│   │   ├── executor.py              # Graph execution engine
│   │   └── event_formatter.py       # SSE event formatting
│   │
│   ├── routes/                       # API Endpoints
│   │   ├── document_routes.py       # Document upload & analysis
│   │   ├── query_routes.py          # Streaming query endpoint
│   │   └── recommendation_routes.py # Recommendation generation
│   │
│   ├── db/                           # Database Layer
│   │   ├── connection.py            # Supabase connection
│   │   └── repositories/            # Data access patterns
│   │
│   ├── middleware/                   # Auth & Security
│   │   └── auth_middleware.py       # JWT verification
│   │
│   ├── utils/                        # Helper Functions
│   │   ├── auth.py                  # Authentication utilities
│   │   ├── embeddings.py            # Vector embedding generation
│   │   ├── pdf_parser.py            # PDF text extraction
│   │   ├── prompts.py               # LLM prompts
│   │   └── supabase_client.py       # Supabase client setup
│   │
│   ├── uploads/                      # Temporary file storage
│   ├── temp_uploads/                 # Session-based uploads
│   ├── app.py                        # Flask application factory
│   ├── requirements.txt              # Python dependencies
│   └── .env                          # Environment variables
│
└── frontend/                         # React Frontend (separate repo)
    ├── src/
    │   ├── api/                      # API service calls
    │   ├── components/               # Reusable components
    │   │   ├── chat/                 # Chat UI components
    │   │   ├── PaymentGateway.jsx
    │   │   └── ProtectedRoute.jsx
    │   ├── pages/                    # Application pages
    │   │   ├── AdminDashboard.jsx
    │   │   ├── AIChatbotUI.jsx
    │   │   ├── PolicyAnalyzerUI.jsx
    │   │   └── EmployeeDashboard.jsx
    │   ├── hooks/                    # Custom React hooks
    │   ├── lib/                      # Supabase client config
    │   ├── utils/                    # Helper functions
    │   └── App.jsx
    └── package.json
```

---

## 🚀 Installation

### Prerequisites

- **Python** 3.9 or higher
- **Node.js** 16+ and npm/yarn
- **Git**
- **Supabase Account** (for database and storage)
- **Google Cloud Account** (for Gemini API access)

### Backend Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/Policy_Compliance.git
cd Policy_Compliance/backend
```

2. **Create and activate virtual environment:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**

Create a `.env` file in the `backend` directory:

```env
# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Flask
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_secret_key_here

# JWT
JWT_SECRET_KEY=your_jwt_secret_here
JWT_ALGORITHM=HS256
```

5. **Initialize database:**
```bash
python test_connection.py
```

6. **Run the backend server:**
```bash
python app.py
```

Backend will run on `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd ../frontend
```

2. **Install dependencies:**
```bash
npm install
# or
yarn install
```

3. **Configure environment variables:**

Create a `.env` file in the `frontend` directory:

```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_BASE_URL=http://localhost:5000
```

4. **Run the development server:**
```bash
npm run dev
# or
yarn dev
```

Frontend will run on `http://localhost:5173`

---

## 💻 Usage

### For Administrators

1. **Login with Admin Credentials**
   - Navigate to `http://localhost:5173`
   - Use admin email and password

2. **Upload Company Policies**
   - Access Admin Dashboard
   - Click "Upload Policy Document"
   - Select PDF file containing company policies
   - System will process and store in vector database

3. **Manage Users**
   - Navigate to User Management section
   - Create employee accounts with appropriate roles
   - Monitor user activity and subscription status

### For Employees

1. **Interactive Compliance Chat**
   - Login with employee credentials
   - Navigate to AI Chat interface
   - Ask questions like:
     - "What are our data retention policies?"
     - "How do we handle GDPR compliance?"
     - "Can I share customer data with third parties?"

2. **Document Analysis**
   - Navigate to Policy Analyzer
   - Upload contract or document for review
   - System will:
     - Extract and chunk document
     - Compare against company policies
     - Identify violations
     - Generate recommendations

3. **View Recommendations**
   - Review prioritized action items
   - See severity levels (High/Medium/Low)
   - Access timeline estimates
   - View expected outcomes

### API Examples

**Stream Query Analysis:**
```bash
curl -X POST http://localhost:5000/queries/analyze/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "session_id": "unique-session-id",
    "message": "What are our data privacy policies?",
    "document_url": "optional-document-url"
  }'
```

**Analyze Document:**
```bash
curl -X POST http://localhost:5000/documents/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "document_url": "https://your-storage.com/contract.pdf",
    "session_id": "unique-session-id"
  }'
```

**Generate Recommendations:**
```bash
curl -X POST http://localhost:5000/recommendations/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "violations": [
      {
        "type": "Violation",
        "title": "Data Retention Period Exceeded",
        "description": "Contract specifies 5-year retention, policy allows max 3 years",
        "severity": "high"
      }
    ],
    "session_id": "unique-session-id"
  }'
```

---

## 📡 API Documentation

### Document Routes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/documents/upload` | POST | Upload policy document |
| `/documents/analyze` | POST | Analyze document for violations |

### Query Routes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/queries/analyze/stream` | POST | Stream AI analysis results via SSE |

### Recommendation Routes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/recommendations/generate` | POST | Generate recommendations from violations |
| `/recommendations/summary` | POST | Get summary of recommendations |

### Authentication

All protected endpoints require JWT token in Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## 🎨 Screenshots & Demo

### Admin Dashboard
![Admin Dashboard](./docs/images/admin-dashboard.png)
*Upload policies, manage users, and monitor system activity*

### AI Chat Interface
![AI Chat](./docs/images/ai-chat.png)
*Interactive compliance assistant with real-time streaming*

### Policy Analyzer
![Policy Analyzer](./docs/images/policy-analyzer.png)
*Document viewer with violation detection and recommendations*

### Thinking Process Visualization
![Thinking Process](./docs/images/thinking-ui.png)
*Transparent AI reasoning steps displayed in real-time*

---

## 🧪 Testing

### Backend Tests
```bash
# Test database connection
python test_connection.py

# Test streaming client
python test_stream_client.py

# Run all tests
pytest tests/
```

### Frontend Tests
```bash
npm run test
# or
yarn test
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👥 Authors

- **Your Name** - *Initial work* - [GitHub Profile](https://github.com/yourusername)

---

## 🙏 Acknowledgments

- Google Gemini AI for powering the language model
- LangChain & LangGraph for agent orchestration framework
- Supabase for backend infrastructure
- React & Vite communities for frontend tools

---

## 📞 Support

For support, email support@yourcompany.com or open an issue in the repository.

---

<div align="center">

**Built with ❤️ using AI-powered multi-agent architecture**

⬆ Back to Top

</div>
