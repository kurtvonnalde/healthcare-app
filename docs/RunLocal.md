Commands for running


frontend
1. cd frontend
2. npm install
3. npm run dev


backend
1. cd backend
2. .\.venv\Scripts\Activate.ps1 #activate .venv
3. python -m pip install --upgrade pip
4. python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload