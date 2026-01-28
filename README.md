# Intelligent Book Management System

A comprehensive full-stack application featuring a Python FastAPI backend with RAG-based Q&A capabilities and a React TypeScript frontend. This system manages books, user reviews, document ingestion, and provides AI-powered recommendations and question-answering using Llama3.

## Features

### Backend (Python FastAPI)
- **User Authentication & Authorization**: JWT-based auth with role management (Admin/User)
- **Book Management**: CRUD operations for books with auto-generated summaries
- **Review System**: User reviews with ratings and AI-generated aggregated summaries
- **AI-Powered Summarization**: Uses Llama3 via Hugging Face for book and review summaries
- **Recommendation Engine**: Hybrid ML model combining collaborative and content-based filtering
- **RAG System**: Document ingestion with embeddings and vector search for Q&A
- **Async Operations**: Fully asynchronous database and API operations
- **Comprehensive Testing**: Unit and integration tests with pytest
- **Production-Ready**: Error handling, logging, caching, and security best practices

### Frontend (React TypeScript)
- **Modern UI**: Responsive design with React 18 and TypeScript
- **Authentication**: Sign up, login, logout functionality
- **User Management**: Admin panel for managing users and roles
- **Book Management**: Browse, search, and manage books
- **Document Upload**: Upload and manage documents for RAG system
- **Q&A Interface**: Ask questions and get AI-powered answers with source citations
- **Recommendations**: Personalized book recommendations
- **Responsive Design**: Mobile-first, accessible design

## Architecture

```
jk/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies.py
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   │           ├── auth.py
│   │   │           ├── books.py
│   │   │           ├── reviews.py
│   │   │           ├── users.py
│   │   │           ├── documents.py
│   │   │           ├── qa.py
│   │   │           └── recommendations.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── db/
│   │   │   └── session.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── book.py
│   │   │   ├── review.py
│   │   │   └── document.py
│   │   ├── schemas/
│   │   │   ├── user.py
│   │   │   ├── book.py
│   │   │   ├── review.py
│   │   │   ├── document.py
│   │   │   └── qa.py
│   │   ├── services/
│   │   │   ├── llama_service.py
│   │   │   └── rag_service.py
│   │   ├── ml/
│   │   │   └── recommendation_model.py
│   │   ├── tests/
│   │   │   ├── conftest.py
│   │   │   └── unit/
│   │   │       ├── test_auth.py
│   │   │       └── test_books.py
│   │   └── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Technology Stack

### Backend
- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL with SQLAlchemy async
- **Authentication**: JWT with python-jose
- **AI/ML**:
  - Llama3 via Hugging Face for text generation
  - Sentence Transformers for embeddings
  - FAISS for vector search
  - Scikit-learn for recommendations
- **Caching**: Redis
- **Testing**: pytest, pytest-asyncio
- **Deployment**: Docker, Docker Compose

### Frontend
- **Framework**: React 18 with TypeScript
- **State Management**: React Context API / Redux Toolkit
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **UI Components**: Custom components with CSS Modules
- **Form Handling**: React Hook Form
- **Testing**: Jest, React Testing Library

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker and Docker Compose (for containerized deployment)
- Hugging Face API Key (for Llama3 access)

## Setup Instructions

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd jk
   ```

2. **Create environment file**
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **Update environment variables**
   Edit `backend/.env` and set:
   - `SECRET_KEY`: Generate a secure 32+ character secret key
   - `HUGGINGFACE_API_KEY`: Your Hugging Face API key (see "Hugging Face API Key Setup" section below)
   - Other configuration as needed

4. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

   This will start:
   - PostgreSQL database (port 5432)
   - Redis cache (port 6379)
   - Backend API (port 8000)
   - Frontend app (port 3000)

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 2: Local Development Setup

#### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL**
   ```bash
   createdb bookdb
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

6. **Run database migrations**
   ```bash
   # The application will auto-create tables on startup
   ```

7. **Run the backend**
   ```bash
   python -m app.main
   # Or with uvicorn:
   uvicorn app.main:app --reload
   ```

#### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment**
   ```bash
   # Create .env file
   echo "REACT_APP_API_URL=http://localhost:8000" > .env
   ```

4. **Run the frontend**
   ```bash
   npm start
   ```

## API Documentation

### Authentication Endpoints

#### POST /api/v1/auth/register
Register a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "SecurePassword123",
  "full_name": "Full Name",
  "role": "user"
}
```

#### POST /api/v1/auth/login
Login and receive JWT tokens.

**Request Body:**
```json
{
  "username": "username",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Book Endpoints

#### POST /api/v1/books/
Create a new book (Admin only).

#### GET /api/v1/books/
Get all books with optional filters (`genre`, `author`).

#### GET /api/v1/books/{book_id}
Get a specific book.

#### PUT /api/v1/books/{book_id}
Update a book (Admin only).

#### DELETE /api/v1/books/{book_id}
Delete a book (Admin only).

#### GET /api/v1/books/{book_id}/summary
Get book summary with aggregated ratings and AI-generated review summary.

### Review Endpoints

#### POST /api/v1/reviews/
Create a review for a book.

#### GET /api/v1/reviews/book/{book_id}
Get all reviews for a book.

#### PUT /api/v1/reviews/{review_id}
Update a review (owner only).

#### DELETE /api/v1/reviews/{review_id}
Delete a review (owner only).

### Document Endpoints

#### POST /api/v1/documents/
Upload a document for RAG ingestion.

#### POST /api/v1/documents/upload
Upload a document file.

#### GET /api/v1/documents/
Get all documents for current user.

#### POST /api/v1/documents/ingest
Trigger ingestion process for pending documents.

### Q&A Endpoints

#### POST /api/v1/qa/ask
Ask a question using RAG system.

**Request Body:**
```json
{
  "question": "What is the main theme of the book?",
  "context_limit": 5
}
```

**Response:**
```json
{
  "question": "What is the main theme of the book?",
  "answer": "The main theme revolves around...",
  "relevant_documents": [
    {
      "document_id": 1,
      "filename": "document.txt",
      "excerpt": "Relevant excerpt...",
      "relevance_score": 0.85
    }
  ],
  "confidence": 0.82
}
```

### Recommendation Endpoints

#### POST /api/v1/recommendations/train
Train the recommendation model with current data.

#### GET /api/v1/recommendations/
Get personalized recommendations.

Query Parameters:
- `book_id` (optional): For content-based recommendations
- `limit`: Number of recommendations (1-20, default 5)

#### GET /api/v1/recommendations/similar/{book_id}
Get books similar to a specific book.

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/unit/test_auth.py

# Run with verbose output
pytest -v
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```

## Environment Variables

### Backend (.env)

```env
# Application
APP_NAME=Book Management System
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bookdb

# Security
SECRET_KEY=your-32-character-minimum-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Hugging Face API
HUGGINGFACE_API_KEY=hf_your_huggingface_api_key_here
HUGGINGFACE_MODEL=meta-llama/Llama-3.1-8B-Instruct

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_TTL=3600

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Frontend (.env)

```env
REACT_APP_API_URL=http://localhost:8000
```

## Deployment

### Docker Deployment

1. **Build images**
   ```bash
   docker-compose build
   ```

2. **Start services**
   ```bash
   docker-compose up -d
   ```

3. **View logs**
   ```bash
   docker-compose logs -f
   ```

4. **Stop services**
   ```bash
   docker-compose down
   ```

### AWS Deployment (Optional)

For production AWS deployment:

1. **RDS (Database)**
   - Create PostgreSQL RDS instance
   - Update `DATABASE_URL` in environment variables

2. **ElastiCache (Redis)**
   - Create Redis ElastiCache cluster
   - Update `REDIS_HOST` and `REDIS_PORT`

3. **ECS/EC2 (Backend)**
   - Deploy backend container to ECS or EC2
   - Configure security groups and load balancer

4. **S3 + CloudFront (Frontend)**
   - Build frontend: `npm run build`
   - Upload to S3 bucket
   - Configure CloudFront distribution

5. **CI/CD Pipeline**
   - Set up GitHub Actions or AWS CodePipeline
   - Automate testing and deployment

## Performance Optimization

- **Database**: Indexed columns for frequent queries
- **Caching**: Redis for recommendation results
- **Async Operations**: Non-blocking I/O throughout
- **Vector Search**: FAISS for efficient similarity search
- **Connection Pooling**: SQLAlchemy async pool

## Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Authentication**: Secure token-based auth
- **Input Validation**: Pydantic schemas
- **SQL Injection Prevention**: SQLAlchemy ORM
- **CORS**: Configured for allowed origins
- **Rate Limiting**: (Can be added via middleware)

## Monitoring and Logging

- **Structured Logging**: JSON format logs
- **Log Levels**: INFO, WARNING, ERROR
- **Request Logging**: All API requests logged
- **Error Tracking**: Comprehensive error handling

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres
```

### Redis Connection Issues
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

### Backend Issues
```bash
# View backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue in the repository
- Contact: [your-email@example.com]

## Hugging Face API Key Setup

To use the AI-powered features (book summaries, review aggregation, and Q&A), you need a Hugging Face API key:

### Steps to Generate Hugging Face API Key:

1. **Create a Hugging Face Account**
   - Visit [huggingface.co](https://huggingface.co)
   - Click "Sign Up" and create a new account
   - Verify your email address

2. **Accept Model License**
   - Go to [meta-llama/Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)
   - Click "Access repository"
   - Read and accept the license terms
   - Fill in required information if prompted

3. **Generate API Token**
   - Click on your profile icon (top right)
   - Go to "Settings"
   - Click "Access Tokens" in the left sidebar
   - Click "New token"
   - Select "Fine-grained tokens" (recommended)
   - Set permissions for "Read access to contents of all public repos and gists"
   - Copy the generated token

4. **Add to Environment**
   - Add the token to your `.env` file:
     ```
     HUGGINGFACE_API_KEY=hf_your_token_here
     ```

5. **Verify Access**
   - The application will automatically verify access on startup
   - Check logs for any authentication errors

## Acknowledgments

- FastAPI for the excellent Python framework
- Hugging Face for Llama3 model access
- React team for the frontend library
- Open source community for all dependencies
