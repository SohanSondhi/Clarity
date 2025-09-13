# To run the frontend

npm install ; npm run dev


# To get an executable
npm run build:python



# Start pgvector

docker run --name pgvector17 -e "POSTGRES_PASSWORD=postgres" -p 5432:5432 -d ankane/pgvector:pg17
