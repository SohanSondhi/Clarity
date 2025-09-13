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
from sklearn.metrics.pairwise import cosine_similarity

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

class DBBuilder():
    def __init__(self, path, table_name, json_data = None):
        self.columns = ["Path", "Parent", "Vector", "Similarities", "Name", "When_Created", "When_Last_Modified", "Description", "File_type"]
        self._db = lancedb.connect(path)
        if table_name in self._db.table_names():
            self._tbl = self._db.open_table(table_name)
        else:
            if json_data:
                initial_df = self.add_json(json_data)
                self._tbl = self._db.create_table(table_name, initial_df)
            else:
                self._tbl = self._db.create_table(table_name, pd.DataFrame(columns=self.columns))
        
    def add_entry(self, Path, Parent, Vector, Similarities, Name, When_Created, When_Last_Modified, Description, File_type):
        json_entry = {
            "Path": str(Path)if Path is not None else "",
            "Parent": str(Parent) if Parent is not None else "",
            "Vector": Vector if Vector is not None and Vector != [] else [],
            "Similarities": Similarities if Similarities is not None and Similarities != [] else [],
            "Name": str(Name) if Name is not None else "",
            "When_Created": str(When_Created) if When_Created is not None else "",
            "When_Last_Modified": str(When_Last_Modified) if When_Last_Modified is not None else "",
            "Description": str(Description) if Description is not None else "",
            "File_type": str(File_type) if File_type is not None else "" 
        }
        self._tbl.add(pd.DataFrame([json_entry]))

    def add_json(self, json_entry):
        data = json.loads(json_entry)
        df = pd.DataFrame([data])
        required_columns = ["Path", "Parent", "Vector", "Similarities", "Name", "When_Created", "When_Last_Modified", "Description", "File_type"]
        contains_all_columns = all(col in df.columns for col in required_columns)
        if not contains_all_columns:
            raise ValueError(f"Missing columns in JSON entry: {set(required_columns) - set(df.columns)}")
        df = df[required_columns]  # Keep only required columns
        return df

    def to_json(self, output_file):
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    

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
    
def local_scrape(db_path, table_name, root_dir="/"):
    # Common system folders to exclude
    exclude_dirs = {'/System', '/Library', '/private', '/dev', '/Volumes', '/Applications', '/usr', '/bin', '/sbin', '/etc', '/proc', '/tmp'}
    
    # File extensions to skip (system, config, binary files)
    skip_extensions = {'.ini', '.cfg', '.conf', '.log', '.tmp', '.cache', '.db', '.sqlite', '.exe', '.dll', '.so', '.dylib', 
                      '.img', '.iso', '.dmg', '.zip', '.tar', '.gz', '.rar', '.7z', '.bin', '.dat', '.lock', '.pid'}
    
    seen_files = set()
    summarizer = Summarizer()
    db_builder = DBBuilder(db_path, table_name)

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Remove system folders from traversal
        dirnames[:] = [d for d in dirnames if os.path.join(dirpath, d) not in exclude_dirs]
        for filename in filenames:
            parent_path = os.path.abspath(dirpath)
            file_id = f"{parent_path}/{filename}"
            if file_id in seen_files: #Use localStorage to track seen files
                continue  
            seen_files.add(file_id)
            file_path = os.path.join(dirpath, filename)
            try:
                scraper = FileScraper(file_path)
                text_chunks = scraper.scrape()
                if not text_chunks:
                    continue
                summary, embeddings, similarities = summarizer.summarize(text_chunks)
                file_stats = os.stat(file_path)
                file_type = os.path.splitext(filename)[1].lower()
                db_builder.add_entry(
                    Path=file_path,
                    Parent=parent_path,
                    Vector=embeddings.tolist(),
                    Similarities=similarities.tolist(),
                    Name=filename,
                    When_Created=file_stats.st_ctime,
                    When_Last_Modified=file_stats.st_mtime,
                    Description=summary,
                    File_type=file_type
                )
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        
if __name__ == "__main__":
    local_scrape("C:/Coding/Clarity-1/apps/api/data", "db", "C:/Professional/CLIP_PAPERS")