import os
import pdfplumber
from llama_index import Document, SimpleNodeParser, GPTSimpleVectorIndex
from llama_index.indices.query.query_transform.base import HyDEQueryTransform


class PDFReader:
    def __init__(self, pdf_file):
        self.pdf_file = pdf_file

        # Extract and preprocess text
        self.text_data = self.extract_pdf_text(pdf_file)

        # Load documents
        self.documents = [Document(t) for t in self.text_data]

        # Parse documents into nodes
        parser = SimpleNodeParser()
        self.nodes = parser.get_nodes_from_documents(self.documents)

        # Build index
        self.index = GPTSimpleVectorIndex(self.nodes)

    def extract_pdf_text(self, pdf_file):
        with pdfplumber.open(pdf_file) as pdf:
            text_data = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_data.append(text)
        return text_data

def query(user_query):
    # Create a HyDE query transform
    hyde = HyDEQueryTransform(include_original=True)
    
    # Execute the query with the HyDE transform
    results = index.query(user_query)
    return results


pdf_file = "path/to/your/pdf_file.pdf"
pdf_reader = PDFReader(pdf_file)

user_query = "Your query here"
results = pdf_reader.query(user_query)

print("Results:")
for result in results:
    print(result)
