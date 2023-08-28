import os
import pdfplumber
from llama_index import Document, GPTSimpleVectorIndex
from llama_index.indices.query.query_transform.base import HyDEQueryTransform
from pathlib import Path
from gpt_index import download_loader
from llama_index import SimpleDirectoryReader

PDFReader = download_loader("PDFReader")

loader = PDFReader()
# documents = loader.load_data(file=Path('./article.pdf'))
documents = SimpleDirectoryReader('pdfs').load_data()

parser = SimpleNodeParser()

nodes = parser.get_nodes_from_documents(documents)

index = GPTSimpleVectorIndex.from_documents(documents)

def pdf_to_text(filepath):
    with pdfplumber.open(filepath) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages])

def index_qa_files():
    index = create_qa_search_index()
    for filepath in glob.glob("pdfs/*.pdf"):
        title = os.path.splitext(os.path.basename(filepath))[0]
        content = pdf_to_text(filepath)
        index.add(title, content)

def create_qa_search_index():
    index = Index("qa_indexdir")
    index.define_field("title", Index.Field.TEXT, unique=True)
    index.define_field("content", Index.Field.TEXT)
    index.create()
    return index

def search_qa_index(query):
    index = create_qa_search_index()
    results = index.search(query)
    return [(r['title'], r['content'], r.score) for r in results]
