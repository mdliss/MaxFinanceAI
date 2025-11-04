# SpendSense: Technical Decision Log

## 1. Framework Selection

### Backend: FastAPI (Python)
**Decision:** Use FastAPI over Flask/Django
**Rationale:**
- Built-in async/await support for database operations
- Automatic API documentation (OpenAPI/Swagger)
- Pydantic integration for request/response validation
- Better performance for I/O-bound operations

**Alternatives Considered:**
- Flask: Too basic, requires many extensions
- Django: Overkill for API-only backend, slower

### Frontend: Next.js 14
**Decision:** Use Next.js with App Router
**Rationale:**
- Server-side rendering for better performance
- Built-in routing and API routes
- TypeScript support out of the box
- React 18 features (Server Components)

**Alternatives Considered:**
- Create React App: Deprecated, no SSR
- Vite + React: Less structure, manual setup

## 2. Database Selection

### Choice: SQLite
**Decision:** Use SQLite with async SQLAlchemy
**Rationale:**
- Zero-configuration deployment
- File-based storage (./data/spendsense.db)
- Sufficient for 50-100 users
- Rubric allows local storage
- Easy backup and version control

**Alternatives Considered:**
- PostgreSQL: Overkill for demo, requires separate service
- MySQL: Same overhead as PostgreSQL
- MongoDB: Not ideal for relational financial data

**Trade-offs:**
- ✅ Simple deployment
- ✅ No external dependencies
- ⚠️ Limited to ~100k transactions (acceptable for scope)
- ⚠️ Not production-ready at scale

## 3. Persona Assignment Approach

### Choice: Rules-Based System
**Decision:** Use deterministic rules instead of ML
**Rationale:**
- 100% explainable (rubric requirement)
- No training data needed
- Deterministic and auditable
- Faster inference (<2 seconds)
- No ML bias issues

**Persona Criteria:**
1. High Utilization: credit ≥50% OR interest > 0
2. Variable Income: irregular payments + low buffer
3. Subscription-Heavy: ≥3 recurring + $50/month
4. Savings Builder: growth ≥2% + utilization <30%
5. Paycheck-to-Paycheck: stable income + low buffer

**Alternatives Considered:**
- ML Classification: Less explainable, requires training
- Clustering: No guarantees on persona types

## 4. AI Integration Strategy

### OpenAI API Usage
**Decision:** Use GPT-4 for recommendation text generation
**Rationale:**
- Generates natural, empowering language
- Incorporates user data into rationales
- Faster than manual content authoring
- Can validate tone automatically

**Integration Points:**
1. Recommendation rationale generation
2. Tone validation (guardrails)
3. Content personalization

**Fallback:** Pre-written template library for offline mode

**API Key Management:**
- Stored in environment variables
- Never committed to git
- Optional for testing (templates available)

## 5. Testing Framework

### Backend: pytest + pytest-asyncio
**Decision:** Use pytest for async testing
**Rationale:**
- Native async test support
- Fixtures for database setup
- Coverage reporting built-in
- Industry standard for Python

**Coverage:**
- 108 passing tests
- Core features: signals, personas, recommendations
- Guardrails: consent, eligibility, tone
- Evaluation: metrics calculation

### Frontend: Vitest
**Decision:** Use Vitest over Jest
**Rationale:**
- Faster than Jest
- Better TypeScript support
- Compatible with Vite build system
- Same API as Jest (easy migration)

## 6. Deployment Architecture

### Docker Compose
**Decision:** Use multi-container Docker setup
**Rationale:**
- One-command startup (docker-compose up)
- Isolated environments for backend/frontend
- Volume mounting for development
- Production-ready containerization

**Services:**
- backend: FastAPI on port 8000
- frontend: Next.js on port 3001
- Shared volume: ./data for SQLite

**Trade-offs:**
- ✅ Easy deployment
- ✅ Consistent environments
- ⚠️ Requires Docker installed

## 7. Synthetic Data Generation

### Approach: Deterministic Faker
**Decision:** Use Faker library with fixed seeds
**Rationale:**
- Reproducible data across runs
- Realistic names and values
- Seed control (seed=42)
- No real PII concerns

**Data Volume:**
- 73 users
- 180+ days of transactions per user
- 2,500+ total transactions
- Diverse financial profiles (income levels, behaviors)

## 8. Signal Detection Algorithms

### Subscription Detection
**Algorithm:** Transaction grouping by merchant + frequency analysis
**Parameters:**
- Minimum 2 occurrences
- Monthly: 28-32 day intervals
- Weekly: 6-8 day intervals
- Amount variance: ±10%

### Credit Utilization
**Algorithm:** balance / credit_limit * 100
**Thresholds:**
- 30% (caution)
- 50% (warning)
- 80% (critical)

### Income Stability
**Algorithm:** Interval variance + amount consistency
**Metrics:**
- Payment frequency detection
- Coefficient of variation
- Cash-flow buffer calculation

## 9. Guardrails Architecture

### Multi-Layer Approach
**Decision:** Separate guardrail types
**Layers:**
1. Consent: Block processing without opt-in
2. Eligibility: Age, transactions, signals
3. Tone: Prohibited pattern detection
4. Content Safety: No predatory products
5. Rate Limiting: Max 10 recommendations/user

**Fail-Closed Design:**
- Default deny if check fails
- Explicit approval required
- All violations logged

## 10. Modular Code Structure

### Organization
```
backend/
  app/
    api/          # FastAPI routers
    models/       # SQLAlchemy models
    services/     # Business logic
    schemas/      # Pydantic validation
frontend/
  src/
    app/          # Next.js pages
    components/   # React components
    types/        # TypeScript types
```

**Principles:**
- Separation of concerns
- Single responsibility
- Dependency injection
- API-first design

## 11. Evaluation Harness

### Metrics Calculation
**Decision:** Real-time computation from database
**Rationale:**
- Always up-to-date
- No separate ETL pipeline
- Direct SQL queries for accuracy

**Metrics Tracked:**
1. Quality: relevance, diversity, coverage, personalization
2. Performance: throughput, latency
3. Outcomes: approval rates, persona distribution
4. Guardrails: eligibility, vulnerable populations

**Export Formats:**
- JSON: Full metrics object
- CSV: Flattened for spreadsheets
- TXT: Human-readable summary

## 12. Operator Dashboard

### Design Philosophy
**Decision:** Full transparency + override capability
**Features:**
- View all signals per user
- See persona assignment rationale
- Approve/reject/flag recommendations
- Complete audit trail
- Search and filter

**Technology:**
- Next.js + TypeScript
- Tailwind CSS for styling
- Real-time API integration
- Responsive design

## Key Trade-offs Summary

| Decision | Benefit | Trade-off |
|----------|---------|-----------|
| SQLite | Simple deployment | Not scalable to millions |
| Rules-based personas | 100% explainable | Less adaptive than ML |
| Docker | Consistent environment | Requires Docker installed |
| OpenAI API | High-quality text | External dependency |
| FastAPI | Modern async support | Less mature than Django |

## Future Considerations

If scaling beyond rubric requirements:
1. Migrate to PostgreSQL for production
2. Add Redis for caching
3. Implement ML models with SHAP explanations
4. Add real-time streaming updates
5. Multi-tenancy support

---

**Last Updated:** 2025-11-04
**Project:** SpendSense Financial Education Platform
