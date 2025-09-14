# Requirements
Python
Npm


# Run frontend
cd apps/desktop
npm install ; npm run dev

# Run backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd apps\api\src
python -m clarity_api.app


# Run Tests
cd C:\Coding\Clarity-1
.\venv\Scripts\activate
pytest


# To get an executable
cd apps\desktop
npm install
npm run build:win