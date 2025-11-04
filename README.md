# MaxFinanceAI - Explainable Financial Education Platform

AI-powered financial recommendation system with operator oversight, strict guardrails, and full audit trails.

## Quick Start

```bash
./start.sh
```

That's it! The application will start with all services running.

### Start Options

```bash
./start.sh           # Start in foreground (see live logs)
./start.sh -d        # Start in background (detached mode)
./start.sh --build   # Rebuild containers before starting
./start.sh --clean   # Wipe data and start fresh
./start.sh --help    # Show all options
```

## Application URLs

Once started, access the application at:

- **Operator Dashboard**: http://localhost:3001/operator
- **Frontend UI**: http://localhost:3001
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Architecture

### Backend (FastAPI + Python)
- RESTful API on port 8000
- SQLite database with async support
- AI-powered recommendation engine with OpenAI integration
- Multi-layer guardrail system (tone detection, PII filtering, regulatory compliance)
- Financial signal detection and persona assignment

### Frontend (Next.js + React)
- Modern dashboard on port 3001
- Operator interface for recommendation review
- User profile viewer with signals and personas
- Audit log viewer
- Guardrails monitoring

### Database
- SQLite database stored in `./data/spendsense.db`
- Persistent storage across container restarts
- Full audit trail of all operator actions

## Key Features

### AI Recommendation Engine
- Detects financial signals from transaction data (credit utilization, income stability, subscription spending)
- Assigns user personas (High Spender, Smart Saver, Investor, Debt Heavy, Budget Conscious)
- Generates personalized financial education content
- Auto-approval with guardrail validation

### Multi-Layer Guardrails
1. **Tone Detection**: Ensures empowering, non-judgmental language
2. **PII Detection**: Blocks exposure of sensitive personal information
3. **Regulatory Compliance**: Prevents regulated financial advice
4. **Consent Validation**: Verifies user opt-in before processing

### Operator Dashboard
- Review all recommendations before delivery
- Override/flag problematic content
- View full decision traces and rationale
- Search users by name or ID
- Monitor guardrail violations

## Development Workflow

### View Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f  # All services
```

### Stop Services
```bash
docker-compose down
```

### Rebuild After Code Changes
```bash
./start.sh --build
```

### Clean Slate (Delete All Data)
```bash
./start.sh --clean
```

### Generate Test Data
```bash
./generate-test-data.sh
```

This creates:
- 20+ diverse users with realistic financial profiles
- 2,500+ transactions over 90 days
- 50+ bank accounts
- 70+ AI-generated recommendations

## API Endpoints

### User Management
- `POST /api/v1/users/` - Create new user
- `GET /api/v1/users/` - List all users
- `GET /api/v1/users/{user_id}` - Get user details

### Consent Management
- `POST /api/v1/consent/` - Grant consent
- `GET /api/v1/consent/{user_id}` - Check consent status
- `DELETE /api/v1/consent/{user_id}` - Revoke consent

### Signal Detection
- `POST /api/v1/signals/{user_id}/detect` - Detect financial signals
- `GET /api/v1/signals/{user_id}` - Get detected signals

### Persona Assignment
- `POST /api/v1/personas/{user_id}/assign` - Assign personas
- `GET /api/v1/personas/{user_id}` - Get user personas
- `GET /api/v1/personas/definitions/all` - List all persona types

### Recommendations
- `POST /api/v1/recommendations/{user_id}/generate` - Generate recommendations
- `GET /api/v1/recommendations/{user_id}` - Get user recommendations
- `POST /api/v1/recommendations/feedback` - Submit operator feedback

### Operator Dashboard
- `GET /api/v1/operator/dashboard/stats` - Dashboard statistics
- `GET /api/v1/operator/recommendations` - All recommendations with filters
- `GET /api/v1/operator/users/search` - Search users

### Guardrails
- `GET /api/v1/guardrails/summary` - Guardrail violation summary
- `POST /api/v1/guardrails/tone-check` - Test tone detection

## Technology Stack

**Backend:**
- FastAPI (Python async web framework)
- SQLAlchemy 2.0 (async ORM)
- SQLite (database)
- OpenAI API (recommendation generation)
- Pydantic (data validation)

**Frontend:**
- Next.js 14 (React framework)
- TypeScript (type safety)
- Tailwind CSS (styling)
- React Query (data fetching)

**DevOps:**
- Docker & Docker Compose
- Multi-stage builds for optimization
- Volume mounting for hot-reload development

## Project Structure

```
MaxFinanceAI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── database.py          # Database configuration
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── routers/             # API route handlers
│   │   ├── services/            # Business logic
│   │   └── utils/               # Helpers and utilities
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js app directory
│   │   ├── components/          # React components
│   │   └── types/               # TypeScript types
│   ├── Dockerfile
│   └── package.json
├── data/                        # Persistent database storage
├── docker-compose.yml           # Service orchestration
├── start.sh                     # One-command startup script
└── generate-test-data.sh        # Test data generator

```

## Environment Variables

The application uses these environment variables (configured in docker-compose.yml):

**Backend:**
- `DATABASE_URL` - SQLite database connection string
- `OPENAI_API_KEY` - OpenAI API key (set in .env file)
- `CORS_ORIGINS` - Allowed CORS origins

**Frontend:**
- `NEXT_PUBLIC_API_URL` - Backend API URL

## Data Model

### Core Entities

**Users**: Bank customers with consent status and profile data

**Signals**: Detected financial behaviors (credit utilization, income patterns, spending categories)

**Personas**: Financial archetypes assigned to users based on signals

**Recommendations**: AI-generated educational content with guardrail validation

**Audit Logs**: Complete trail of all operator actions and system decisions

## Testing

### Manual Testing via Dashboard

1. Start the application: `./start.sh`
2. Generate test data: `./generate-test-data.sh`
3. Open operator dashboard: http://localhost:3001/operator
4. Click "Approved" to see recommendations
5. Search for "Charlotte Jackson" to view user profiles

### API Testing via Swagger

1. Open API docs: http://localhost:8000/docs
2. Try the interactive API explorer
3. Test endpoints with sample data

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3001
lsof -ti:3001 | xargs kill -9
```

### Database Issues

```bash
# Reset database and start fresh
./start.sh --clean
./generate-test-data.sh
```

### Docker Issues

```bash
# Rebuild containers from scratch
docker-compose down
docker-compose build --no-cache
./start.sh
```

### View Container Logs

```bash
# Backend errors
docker-compose logs backend

# Frontend errors
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f
```

## Current Status

**Completed Tasks:**
- Synthetic data generation with realistic financial profiles
- Multi-layer guardrail system (tone, PII, regulatory)
- Financial signal detection engine
- Persona assignment system
- AI recommendation generation with OpenAI
- Operator dashboard with full UI
- Consent management system
- Audit logging
- Dockerized deployment

**Database Stats:**
- 26 test users
- 2,776 transactions
- 73 approved recommendations
- 49 bank accounts
- 46 financial signals
- 37 persona assignments

## Security & Privacy

- All user data is synthetic for demonstration
- Consent required before any data processing
- PII detection prevents exposure of sensitive data
- Full audit trail for compliance
- No regulated financial advice provided
- Educational content only

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, please create an issue in the project repository.
