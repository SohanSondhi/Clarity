# To run the frontend

npm install ; npm run dev

# To run backend
# 1. Activate the virtual environment
venv\Scripts\activate

# 2. Navigate to the API source directory  
cd apps\api\src

# 3. Run the API as a module
python -m clarity_api.app

# To get an executable
npm run build:python



# Start pgvector

docker run --name pgvector17 -e "POSTGRES_PASSWORD=postgres" -p 5432:5432 -d ankane/pgvector:pg17
