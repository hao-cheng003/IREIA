# Quick Start
## Requirements
- Python 3.11
- Node.js 18+

## Install
### backend
cd ./backend
pip install -r requirements.txt
### frontend
cd ./frontend
npm install

## Run
### backend
cd ./backend
uvicorn api.main:app --reload --port 8000
### frontend
cd ./frontend
npm run dev

## Verify
- Open http://localhost:3000 in browser
- Backend health check: http://localhost:8000/health

# Project Structure (Frontend)
"app/" - Next.js app router pages
"components/" - Reusable UI components (MapView, HouseForm, TrendChart)
"lib/" - API clients and utilities

# Manual
- User Manual: docs/user_manual.md
- Developer Manual: docs/developer_manual.md

