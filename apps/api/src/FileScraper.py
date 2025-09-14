import os
import json
import docx
import pdfplumber
from bs4 import BeautifulSoup as soup
from transformers import pipeline
from keybert import KeyBERT 
from sentence_transformers import SentenceTransformer
import lancedb
import pandas as pd
import pyarrow as pa
from sklearn.metrics.pairwise import cosine_similarity

db = lancedb.connect("C:/Professional/test-db")

#File Scraper class
class FileScraper:
    def __init__(self, file_path):
        self.file_path = file_path

    def chunk_text(self, text, max_words=500):
        words = text.split()
        chunks = []
        for i in range(0, len(words), max_words):
            chunk = ' '.join(words[i:i+max_words])
            chunks.append(chunk)
        return chunks
        
    def scrape_docx(self, docx_path):
        if not os.path.exists(docx_path):
            raise FileNotFoundError(f"The file {docx_path} does not exist.")
        
        doc = docx.Document(docx_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)

        return self.chunk_text('\n'.join(full_text))

    def scrape_pdf(self, pdf_path):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The file {pdf_path} does not exist.")
        
        full_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                full_text.append(page.extract_text())

        return self.chunk_text('\n'.join(full_text))

    def scrape_html(self, html_path):
        if not os.path.exists(html_path):
            raise FileNotFoundError(f"The file {html_path} does not exist.")
        
        with open(html_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        soup = soup(content, 'html.parser')
        text = soup.get_text()

        return self.chunk_text(text)

    def scrape(self):
        #Scrape based on file extension
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"The file {self.file_path} does not exist.")
        file_extension = os.path.splitext(self.file_path)[1].lower()
        if file_extension == '.docx':
            return self.scrape_docx(self.file_path)
        elif file_extension == '.pdf':
            return self.scrape_pdf(self.file_path)
        elif file_extension == '.html' or file_extension == '.htm':
            return self.scrape_html(self.file_path)
        else:
            if file_extension in ('.txt','.py','.cpp','.java','.json','.csv'):
                with open(self.file_path, 'r', encoding='utf-8') as file:
                    return self.chunk_text(file.read())
            else: 
                print(f"Unsupported file type: {file_extension}")
                return []  # Return empty list for unsupported files


#Text Summarization and Tagging 
class Summarizer: 
    def __init__(self):
        self._summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        self._bert = KeyBERT(model='all-MiniLM-L6-v2')
        self._embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def summarize(self, text_chunks):
        all_summaries = []
        for chunk in text_chunks:
            summary = self._summarizer(chunk, max_length=500, min_length=1, do_sample=False)
            all_summaries.append(summary[0]['summary_text'])

        # Combine all summaries
        combined_summary = ' '.join(all_summaries)

        # Return Tuple of summary and embeddings
        final_summary = self._summarizer(combined_summary, max_length=200, min_length=50, do_sample=False)[0]['summary_text']
        embeddings = self._embedder.encode(final_summary)
        chunk_embeddings = self._embedder.encode(text_chunks, convert_to_numpy=True)
        similarities = cosine_similarity(chunk_embeddings)
        return (final_summary, embeddings, similarities)
    
class LanceDBManager(): 
    def __init__(self, db_path):
        self.db = lancedb.connect(db_path)

    def create_table(self, table_name, data):
        schema = pa.schema([
                    pa.field("Path", pa.string()),
                    pa.field("Parent", pa.string()),
                    pa.field("Vector", pa.list_(pa.float32())),  # embedding vector
                    pa.field("Similarities", pa.list_(pa.list_(pa.float32()))),  # similarity matrix
                    pa.field("Name", pa.string()),
                    pa.field("When_Created", pa.float64()),  # UNIX timestamp
                    pa.field("When_Last_Modified", pa.float64()),
                    pa.field("Description", pa.string()),
                    pa.field("File_type", pa.string()),
                ])    
        
        if len(data) > 0:  
            self.db.create_table(table_name, schema=schema, data = data, mode="overwrite")
            
    def get_table(self, table_name):
        if table_name in self.db.table_names():
            return self.db.open_table(table_name)
        else:
            raise ValueError(f"Table {table_name} does not exist in the database.")
        
    def local_scrape(self, table_name, root_dir):
        exclude_dirs = {'/System', '/Library', '/private', '/dev', '/Volumes', '/Applications', '/usr', '/bin', '/sbin', '/etc', '/proc', '/tmp'}
        seen_files = set()
        summarizer = Summarizer()
        data = []

        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if os.path.join(dirpath, d) not in exclude_dirs]
            for filename in filenames:
                parent_path = os.path.abspath(dirpath)
                file_id = f"{parent_path}/{filename}"
                if file_id in seen_files:
                    print(f"Skipping already seen file: {file_id}")
                    continue  
                seen_files.add(file_id)
                file_path = os.path.join(dirpath, filename)
                try:
                    scraper = FileScraper(file_path)
                    text_chunks = scraper.scrape()
                    if not text_chunks:
                        print(f"Skipping {file_path}: No text chunks returned.")
                        continue
                    summary, embeddings, similarities = summarizer.summarize(text_chunks)
                    file_stats = os.stat(file_path)
                    file_type = os.path.splitext(filename)[1].lower()
                    json_entry = {
                        "Path": file_path,
                        "Parent": parent_path,
                        "Vector": embeddings.tolist(),  # Convert numpy array to list
                        "Similarities": similarities.tolist(),  # Convert numpy array to list
                        "Name": filename,
                        "When_Created": float(file_stats.st_ctime),
                        "When_Last_Modified": float(file_stats.st_mtime),
                        "Description": summary,
                        "File_type": file_type
                    }
                    data.append(json_entry)
                    print(f"Inserted data for {file_path} into table '{table_name}'")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
        if len(data) > 0:  
            self.create_table(table_name, data)
            
        
if __name__ == "__main__":
    ROOT_DIR = "C:/Professional"
    DB_PATH = "C:/Professional/test-db"
    TABLE_NAME = "Hello"

    # Initialize LanceDB manager
    db_manager = LanceDBManager(DB_PATH)

    # Scrape local files and populate the database
    db_manager.local_scrape(TABLE_NAME, ROOT_DIR)
