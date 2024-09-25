import PyPDF2
import pandas as pd
from docx import Document

# Function to read PDF
def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

# Function to read Word document
def read_word(file):
    doc = Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# Function to read Excel file
def read_excel(file):
    df = pd.read_excel(file)
    return df
