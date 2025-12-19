# IREA_V3 Developer Manual

## 1. Project Overview
This project is a full-stack web application for estimating residential house prices in the Boston area.
- Frontend: Next.js (TypeScript)
- Backend: FastAPI (Python)
- Model: Baseline + Residual prediction pipeline

## 2. Repository Structure
|--- backend/
    |-- api/
       |-- main.py  # FastAPI app entry 
       |-- models/  # Baseline model & Residual model
       |-- routes/  # API routes (predict, health)
       |-- services/  # Model inference & feature logic
       |-- utils/  # Shared utilites
    |-- requirements.txt
|--- frontend/
    |-- app/  # Next.js pages (App Router)
    |-- components/  # Reusable UI components
    |-- lib/  # API client and helpers
    |-- package.json
|--- data/
    |-- baseline_model/  # Training code & Data_source
    |-- residual_model/  # Training code & Data_source
|--- docs/
    |-- developer_manual.md
    |-- user_manual.md
|--- README.md

## 3. Backend Design
1. `api/main.py` initializes the FastAPI application and middleware.
2. `routes/` defines REST endpoints (`/predict`, `/health`).
3. `services/` contains model loading, feature processing, and inference logic.
4. The prediction pipeline uses a baseline estimate followed by a residual adjustment model.

## 4. Frontend Design
1. Built with Next.js App Router.
2. `app/predict` is the main user-facing page.
3. `components/` contains isolated UI components:
    - `MapView`: Google Maps interaction
    - `HouseForm`: input form and validation
    - `TrendChart`: visualization of price trends
4. `lib/api.ts` handles communication with backend APIs.

## 5. Development Workflow
### Backend
```bash
cd backend
uvicorn api.main:app --reload
```
### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 6. Code Quality
1. TypeScript is used on the frontend with ESLint enabled.
2. All ESLint warnings and errors have been resolved.
3. Backend follows modular service-based design.
4. Clear naming conventions and defensive typing are used for API boundaries.

## 7. Notes for Extension
1. The residual model can be retrained independently of the baseline model. You can collect more sales data(see data/residual_model/data_source.txt), and it will helps to improve the performence.
2. Additional features or visualization components can be added without modifying the core pipeline.