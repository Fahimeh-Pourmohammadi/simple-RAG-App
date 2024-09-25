import streamlit as st
from docx import Document
from PyPDF2 import PdfReader
import json
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.text_splitter import RecursiveCharacterTextSplitter

OPENAI_API_KEY=""

# Chain to extract each section of the contract and return valid JSON for that section
def create_section_extraction_chain(section_name):
    section_prompt = f"""
    You are tasked with extracting the '{section_name}' section from the following contract.

    Please return the result **strictly** in a valid JSON format for the section '{section_name}'.

    Instructions:
    - Ensure that all keys are wrapped in double quotes ("").
    - All string values should also be wrapped in double quotes.
    - There should be no trailing commas.
    - All objects and arrays should be closed properly with braces or brackets.
    - Ensure there are no incomplete strings or fields.
    - Check the entire JSON output for the section '{section_name}' to ensure that it is syntactically correct and fully valid.

    Contract Text:
    {{contract_text}}

    JSON Output for '{section_name}':
    """
    
    prompt = PromptTemplate(template=section_prompt, input_variables=["contract_text"])
    return LLMChain(prompt=prompt, llm=OpenAI(api_key=OPENAI_API_KEY))

# Chain to validate and correct JSON if needed
def create_json_validation_chain():
    validation_prompt = """
    You are an expert in correcting JSON formats.

    The following is a JSON structure that may have errors such as:
    - Missing closing brackets.
    - Incomplete strings.
    - Incorrect quotes around keys or values.
    - Trailing commas in objects or arrays.
    - Unclosed or improperly nested brackets.

    Please carefully review the JSON, correct any issues, and return a fully valid JSON structure.
    Make sure that:
    - All keys are enclosed in double quotes.
    - All string values are enclosed in double quotes.
    - There are no trailing commas.
    - All objects and arrays are properly closed with brackets and braces.

    Here is the potentially invalid JSON structure:
    {generated_json}

    Please return the corrected JSON structure below:
    """
    
    prompt = PromptTemplate(template=validation_prompt, input_variables=["generated_json"])
    return LLMChain(prompt=prompt, llm=OpenAI(api_key=OPENAI_API_KEY))

# Main process to extract and validate sections one by one
def process_contract_in_sections(contract_text):
    sections = ["Contract Parties", "Object of the Agreement", "Rights and Obligations", "Financial Terms", "Travel Policies"]
    complete_json = {}

    for section in sections:
        st.write(f"Extracting the '{section}' section from the contract...")
        # Create the chain to extract the section
        section_chain = create_section_extraction_chain(section)
        
        # Extract the section JSON
        section_json = section_chain.run(contract_text=contract_text)
        
        # Validate the section JSON using the validation chain
        validation_chain = create_json_validation_chain()
        validated_section_json = validation_chain.run(generated_json=section_json)
        
        # Try loading the validated section JSON
        try:
            section_data = json.loads(validated_section_json)
            complete_json[section] = section_data
        except json.JSONDecodeError as e:
            st.error(f"JSON decoding error in section '{section}': {e}")
            st.error(f"Invalid JSON for '{section}': {validated_section_json}")
            return
    
    # Step 7: Final JSON output
    st.write("Final extracted and validated JSON:")
    return complete_json

# Streamlit UI
st.title("Contract Section-by-Section Extraction")
# Helper function to extract text from documents
def extract_text_from_document(doc_file):
    if doc_file.name.endswith(".pdf"):
        return extract_text_from_pdf(doc_file)  # Extract text using PyPDF2 or another library
    elif doc_file.name.endswith(".docx"):
        return extract_text_from_docx(doc_file)  # Extract text using python-docx
    else:
        return ""

# Extract text from PDF using PyPDF2
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Extract text from DOCX using python-docx
def extract_text_from_docx(docx_file):
    doc = Document(docx_file)
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    return "\n".join(full_text)
# File Upload for Contract
contract_file = st.file_uploader("Upload Contract Document", type=["pdf", "docx"])
if contract_file:
    # Extract text from the uploaded contract document
    contract_text = extract_text_from_document(contract_file)
    
    if not contract_text:
        st.error("Could not extract text from the file. Please check the file and try again.")
    else:
        # Debug: Check the type of contract_text
        st.write(f"Contract text is of type: {type(contract_text)}")
        
        # Proceed with section-by-section processing
        final_json = process_contract_in_sections(contract_text)
        st.json(final_json)


