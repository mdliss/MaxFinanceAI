# SpendSense - Tasks for Rubric Compliance

## Project Status

**Implementation**: Core features complete
**Documentation**: Required for submission
**Submission Readiness**: In progress

---

## Submission Checklist (Per Rubric)

### ✅ Core Implementation (Complete)
- [x] Code repository with modular structure
- [x] One-command setup (Docker Compose)
- [x] ≥10 unit/integration tests (18 tests passing)
- [x] Synthetic Plaid-style data generator (50-100 users)
- [x] Behavioral signal detection (subscriptions, savings, credit, income)
- [x] Five persona assignment system with prioritization
- [x] Recommendation engine with plain-language rationales
- [x] Consent and guardrails (eligibility, tone, disclosure)
- [x] Operator view for oversight
- [x] Evaluation harness with metrics

### 📋 Required Documentation (In Progress)

#### 1. Decision Log
**Status**: Not started
**Priority**: High
**Requirements per rubric**:
- Document key technical choices
- Explain rationale for framework selection (FastAPI vs alternatives)
- Database choice (SQLite vs PostgreSQL/MySQL)
- Persona approach (rules-based vs ML)
- AI integration strategy (OpenAI usage)
- Modular structure decisions

**Deliverable**: `/docs/decision-log.md` explaining technical choices and trade-offs

---

#### 2. Data Model/Schema Documentation
**Status**: Not started
**Priority**: High
**Requirements per rubric**:
- Document all database tables
- Field descriptions and types
- Relationships between tables
- Sample data examples

**Deliverable**: `/docs/schema.md` with complete schema documentation

---

#### 3. AI Tools and Prompts Documentation
**Status**: Not started
**Priority**: High
**Requirements per rubric**:
- Document all AI integration points
- OpenAI API usage locations
- Prompt templates used
- Model selection rationale

**Deliverable**: `/docs/ai-integration.md` documenting AI tools and prompts

---

#### 4. Technical Writeup (1-2 pages)
**Status**: Not started
**Priority**: High
**Requirements per rubric**:
- System architecture overview
- Key technical achievements
- Challenges and solutions
- Limitations and trade-offs

**Deliverable**: `/docs/technical-writeup.md` (1-2 pages)

---

#### 5. Evaluation Report
**Status**: Code exists, report needed
**Priority**: High
**Requirements per rubric**:
- Coverage: % users with persona + ≥3 behaviors
- Explainability: % recommendations with rationales
- Relevance: Education-persona fit scoring
- Latency: Time to generate recommendations
- Fairness: Basic demographic parity check

**Actions**:
1. Run evaluation harness on all test users
2. Export metrics to JSON format
3. Export metrics to CSV format
4. Generate 1-2 page summary report

**Deliverables**:
- `/evaluation/metrics.json`
- `/evaluation/metrics.csv`
- `/evaluation/summary-report.md`

---

#### 6. Performance Metrics and Benchmarks
**Status**: Not started
**Priority**: Medium
**Requirements per rubric**:
- Signal detection processing time per user
- Recommendation generation time per user
- Total pipeline execution time
- API response times

**Actions**:
1. Measure processing time for signal detection
2. Measure recommendation generation latency
3. Test with varying user counts
4. Document results

**Deliverable**: `/docs/performance-benchmarks.md`

---

#### 7. Test Cases and Validation Results
**Status**: Tests exist, documentation needed
**Priority**: Medium
**Requirements per rubric**:
- Document all test cases
- Backend test results (pytest)
- Frontend test results (Vitest)
- Coverage statistics

**Actions**:
1. Run complete test suite
2. Capture results and coverage
3. Document test strategy

**Deliverable**: `/docs/test-results.md`

---

#### 8. Demo Video or Live Presentation
**Status**: Not started
**Priority**: High
**Requirements per rubric**:
- System walkthrough showing all features
- Data generation process
- Signal detection and persona assignment
- Recommendation generation with rationales
- Operator view and oversight capabilities
- Guardrail enforcement demonstration

**Deliverable**: Video file or live presentation link

---

## Priority Sequence

### Must-Have for Submission (High Priority)
1. **Decision Log** - Explain key technical choices
2. **Data Model Documentation** - Complete schema documentation
3. **AI Tools Documentation** - Document OpenAI integration and prompts
4. **Technical Writeup** - 1-2 page summary of implementation
5. **Evaluation Report** - JSON/CSV metrics + summary
6. **Demo Video/Presentation** - Complete system walkthrough

### Should-Have for Submission (Medium Priority)
7. **Performance Benchmarks** - Processing time measurements
8. **Test Results Documentation** - Test strategy and coverage

---

## Task Details

### Task 1: Create Decision Log
**Estimated Time**: 2-3 hours
**Steps**:
1. Document FastAPI vs Flask/Django choice
2. Document SQLite vs PostgreSQL choice
3. Document rules-based vs ML approach for personas
4. Document OpenAI integration decisions
5. Document testing framework choices
6. Document Docker deployment strategy

---

### Task 2: Document Data Model/Schema
**Estimated Time**: 2-3 hours
**Steps**:
1. List all database tables
2. Document each field with type and description
3. Show relationships (foreign keys)
4. Provide sample data for key tables
5. Document indexes and constraints

---

### Task 3: Document AI Integration
**Estimated Time**: 2 hours
**Steps**:
1. List all OpenAI API integration points
2. Document prompt templates (if any used)
3. Explain model selection rationale
4. Document token usage patterns
5. Describe fallback strategies

---

### Task 4: Write Technical Writeup
**Estimated Time**: 3-4 hours
**Steps**:
1. Overview of system architecture
2. Highlight key achievements
3. Document challenges and solutions
4. List known limitations
5. Keep to 1-2 pages maximum

---

### Task 5: Generate Evaluation Report
**Estimated Time**: 2 hours
**Steps**:
1. Run evaluation harness via API endpoint
2. Export metrics to `/evaluation/metrics.json`
3. Export metrics to `/evaluation/metrics.csv`
4. Write 1-2 page summary comparing results to targets
5. Include per-user decision traces

---

### Task 6: Measure Performance Benchmarks
**Estimated Time**: 1-2 hours
**Steps**:
1. Time signal detection for 10, 50, 100 users
2. Time recommendation generation per user
3. Measure API response times for key endpoints
4. Document results with methodology

---

### Task 7: Document Test Results
**Estimated Time**: 1-2 hours
**Steps**:
1. Run pytest suite and capture output
2. Run Vitest suite and capture output
3. Generate coverage report
4. Document test strategy and results

---

### Task 8: Create Demo Video/Presentation
**Estimated Time**: 3-4 hours
**Steps**:
1. Write demo script covering all features
2. Record system walkthrough:
   - Docker startup
   - Data generation
   - Operator dashboard navigation
   - User search and profile review
   - Signal and persona review
   - Recommendation approval workflow
   - Guardrail demonstrations
3. Edit and finalize video
4. Upload or prepare for live presentation

---

## Success Criteria Verification

Before submission, verify:

| Criterion | Target | Verification Method |
|-----------|--------|-------------------|
| Coverage | 100% users with persona + ≥3 behaviors | Run evaluation report |
| Explainability | 100% recommendations with rationales | Check generated recommendations |
| Latency | <5 seconds per user | Performance benchmarks |
| Auditability | 100% with decision traces | Check operator view |
| Code Quality | ≥10 tests passing | Run test suite |
| Documentation | Complete schema and decision log | Review all docs files |

---

## Submission Package Contents

Final submission should include:

```
/
├── README.md                          # Setup and usage instructions
├── docker-compose.yml                 # One-command setup
├── /backend                           # Backend code
├── /frontend                          # Frontend code
├── /docs
│   ├── decision-log.md               # Technical choices explanation
│   ├── schema.md                     # Data model documentation
│   ├── ai-integration.md             # AI tools and prompts
│   ├── technical-writeup.md          # 1-2 page summary
│   ├── performance-benchmarks.md     # Performance metrics
│   └── test-results.md               # Test documentation
├── /evaluation
│   ├── metrics.json                  # Evaluation metrics (JSON)
│   ├── metrics.csv                   # Evaluation metrics (CSV)
│   └── summary-report.md             # 1-2 page evaluation summary
└── demo-video.mp4 or presentation-link.txt
```

---

## Current State

**Core implementation is complete.** All remaining work is documentation and submission preparation as required by the rubric. No additional coding is required unless issues are discovered during final validation.

---

**Last Updated**: 2025-11-04
**Aligned with**: SpendSense Rubric Requirements
