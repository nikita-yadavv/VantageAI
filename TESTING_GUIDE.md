# VantageAI — Complete System Testing Guide

**Product:** VantageAI (Adaptive Technical Screening & Evaluation Engine)  
**Platform:** macOS | FastAPI Backend + React Frontend + SQLite

---

## 1. Quick Launch

### Start Backend (Terminal 1):
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --port 8000 --reload
```

### Start Frontend (Terminal 2):
```bash
cd frontend
npm run dev
```

Open **[http://localhost:5173](http://localhost:5173)** *(or [http://localhost:8000](http://localhost:8000))*.

---

## 2. Automated Test Verification (Pytest)

Run all unit and integration tests:
```bash
PYTHONPATH=backend ./backend/venv/bin/pytest backend/tests -v
```
**Expected Result:** 17/17 tests passing (`test_resume_parser.py`, `test_rag_service.py`, `test_interview_engine.py`, `test_evaluation_service.py`, `test_api_endpoints.py`).

---

## 3. Step-by-Step Manual User Walkthrough

### Step 1: Role Selection & Resume Ingestion
1. Open the UI at `http://localhost:5173`.
2. Pick a target role: **AI / Machine Learning Engineer**, **Backend Engineer**, or **Data Scientist**.
3. Under *2. Upload Resume*, click any quick-fill button (e.g. **Alex (AI/ML)** or **Jordan (Backend)**) or upload a PDF/TXT resume.
4. The candidate's name and detected skills will appear instantly.

### Step 2: Adaptive Technical Interview
1. Click **Start Interview**.
2. Read the dynamic technical question grounded in the role's foundational knowledge base.
3. Type your technical response into the reasoning box, or click the **`⚡ Quick Fill (Demo/Testing)`** button to instantly insert a calibrated response for demo and testing.
4. Click **Submit Answer** — view immediate feedback and score (0-10), then click **Next Question** to proceed.

### Step 3: Candidate Assessment Report
1. After completing the interview, view the comprehensive **Assessment Results**.
2. Review:
   - Overall Competency Score (0-100) and Rating
   - Executive Summary
   - Topic Proficiency Breakdown
   - Key Strengths & Areas for Improvement
   - Question-by-Question audit with candidate response and feedback
3. Click **Export JSON** to download the raw scorecard.
