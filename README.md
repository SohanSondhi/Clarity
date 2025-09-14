# Clarity

Clarity is a cross-platform application for scraping, indexing, searching, and managing files and images using LanceDB and modern AI models.

## Features

- **Frontend:** Electron-based desktop app (React, Fluent UI, Radix UI)
- **Backend:** FastAPI server for file and image indexing, search, and management
- **File Scraping:** Supports text (PDF, DOCX, HTML, TXT, etc.) and image files
- **Embeddings:** Uses HuggingFace Transformers, CLIP, and SentenceTransformers
- **Database:** LanceDB for fast vector search and metadata storage
- **Live Monitoring:** Observer pattern for automatic ingestion of new files

---

## Getting Started

### 1. Clone the repository

```sh
git clone <repo-url>
cd Clarity
```

### 2. Backend Setup

#### a. Create and activate a Python virtual environment

```sh
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux/zsh
# OR
.venv\Scripts\activate     # Windows (cmd)
```

#### b. Install Python dependencies

```sh
pip install -r requirements.txt
```

#### c. Run the API server

```sh
cd apps/api/src
python -m clarity_api.app
```

### 3. Frontend Setup

```sh
cd apps/desktop
npm install
npm run dev
```

### 4. Build Executable

```sh
npm run build:python
```

---

## Directory Structure

- `apps/desktop/` — Electron/React frontend
- `apps/api/src/clarity_api/` — FastAPI backend, routes, and indexing logic
- `apps/api/data/` — File scraping, embedding, and observer utilities

---

## Key Python Dependencies

- `fastapi`, `uvicorn` — API server
- `lancedb`, `pyarrow`, `pandas` — Database and data handling
- `transformers`, `sentence-transformers`, `torch` — AI models
- `watchdog` — Directory observer
- `python-dotenv` — Environment variable management

---

## Usage

- Start the backend and frontend as described above.
- The backend will automatically scrape and index files in the specified directory.
- New files added to the directory will be detected and indexed in real time.
- Use the frontend to search, view, and manage indexed files and images.

---

## Troubleshooting

- If you see `permission denied` when activating the virtual environment, use `source .venv/bin/activate` (not direct execution).
- For `500 Internal Server Error` on API requests, check backend logs for Python tracebacks and missing environment variables.

---

Let me know if you want to add API endpoint documentation, environment variable setup, or more details!
