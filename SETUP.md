# Setup Guide

## Requirements
- Python 3.13+
- Node.js 20+
- npm 10+

## Backend Setup
\`\`\`bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements.txt
\`\`\`

## Frontend Setup
\`\`\`bash
cd frontend
npm install
\`\`\`

## Starting the System
Terminal 1 (Backend):
\`\`\`bash
cd backend
source .venv/bin/activate
uvicorn api:app --host 0.0.0.0 --port 8000
\`\`\`
*(API will be available at http://localhost:8000/api)*

Terminal 2 (Frontend):
\`\`\`bash
cd frontend
npm run dev -- --host 0.0.0.0
\`\`\`
*(UI will be available at http://localhost:5173)*
