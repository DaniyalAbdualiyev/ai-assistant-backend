# AI Assistant Backend

A robust FastAPI-based backend service that provides AI-powered assistance capabilities. This project includes authentication, database integration, and various AI services.

## Features

- FastAPI-based REST API
- PostgreSQL database integration with SQLAlchemy
- JWT-based authentication
- OpenAI integration
- PDF and DOCX document processing
- QR code generation
- Admin interface
- Pinecone vector database integration
- LangChain integration
- Stripe payment integration

## Prerequisites

- Python 3.8+
- PostgreSQL
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai_assistant_backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```
Edit the `.env` file with your configuration values.

## Database Setup

1. Create a PostgreSQL database
2. Update the database connection string in `.env`
3. Run migrations:
```bash
alembic upgrade head
```

## Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Swagger UI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`

## Testing

Run tests using pytest:
```bash
pytest
```

## Project Structure

```
ai_assistant_backend/
├── app/
│   ├── admin/         # Admin interface components
│   ├── auth/          # Authentication related code
│   ├── dependencies/  # Dependency injection
│   ├── middleware/    # Custom middleware
│   ├── models/        # Database models
│   ├── routers/       # API routes
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   └── main.py        # Application entry point
├── tests/             # Test files
├── migrations/        # Database migrations
├── requirements.txt   # Project dependencies
└── .env              # Environment variables
```

## Environment Variables

Required environment variables (see `.env.example` for details):
- Database configuration
- JWT secret key
- OpenAI API key
- Stripe API keys
- Pinecone configuration
- Other service-specific keys

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here] 