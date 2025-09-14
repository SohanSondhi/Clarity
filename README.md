# To run the frontend
cd apps/desktop
npm install ; npm run dev

# To run backend
# Activate the virtual environment
venv\Scripts\activate

# Navigate to the API source directory  
cd apps\api\src

# Run the API as a module
python -m clarity_api.app

# To get an executable
npm run build:python
