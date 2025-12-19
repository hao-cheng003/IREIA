# IREA_V3 User Manual

## 1. What is this?
- A web application for estimating residential house prices in the Boston area.
- Frontend: Next.js
- Backend: FastAPI

## 2. Requirements
- Python 3.11
- Node.js 18+
- (Optional) Google Maps API Key: NEXT_PUBLIC_GOOGLE_MAPS_API_KEY

## 3. Setup
### 3.1 Backend
Type this in the Terminal(backend):
```bash
cd backend
pip install -r requirements.txt
```
### 3.2 Frontend
Type this in the Terminal(frontend):
```bash
cd frontend
npm install
```
### 3.3 Environment Variables
Create `frontend/.env.local`:
    ```env
    NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
    NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=YOUR_KEY
    ```

## 4. Run
### 4.1 Start Backend
Terminal(backend):
cd backend
uvicorn api.main:app --reload --port 8000

### 4.2 Start frontend
Terminal(frontend):
cd frontend
npm run dev

## 5. Verify
Frontend: http://localhost:3000/predict
Backend health: http://127.0.0.1:8000/health

## 6. How to use
1. Search address or click on map (Boston area only)
2. Fill in house features
3. Click “Predict”
4. Read Final Price + Trend chart

## 7. Troubleshooting
1. If map doesn’t load: check NEXT_PUBLIC_GOOGLE_MAPS_API_KEY
2. If API fails: check NEXT_PUBLIC_API_BASE and backend is running
3. If CORS error: backend CORS config + correct base URL

## 8. System Overview
The system follows a two-stage prediction design:
1. Baseline Model
   The baseline model estimates house price based on official property assessment data and structural features (e.g., size, year built, rooms).  
   This provides a stable, assessment-aligned starting point.

2. Residual Adjustment Model
   A residual model further adjusts the baseline prediction using recent market information.  
   Instead of predicting the full price again, it learns how much the market price deviates from the assessment-based estimate.

Overall workflow:
User input → Baseline price estimation → Residual adjustment → Final price output

This design improves robustness and interpretability while keeping the system efficient and easy to maintain.

## 9. Output Explanation
1. Final Price: predicted house price after residual adjustment
2. Assessment: official assessment-based baseline
3. Residual Adjustment: percentage difference from assessment
4. Trend Chart: long-term estimated price trend