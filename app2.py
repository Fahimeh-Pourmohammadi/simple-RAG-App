import streamlit as st
from docx import Document
from PyPDF2 import PdfReader
import json
import re
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SimpleSequentialChain
from langchain.text_splitter import RecursiveCharacterTextSplitter


OPENAI_API_KEY="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"
# Helper function to chunk the contract
def chunk_contract_text(contract_text, chunk_size=350, overlap=150):
    # Use RecursiveCharacterTextSplitter to divide contract text into manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=overlap
    )
    chunks = text_splitter.split_text(contract_text)
    return chunks

# Helper function to create the initial JSON structure

# Define the chain for initial extraction of main contract constraints
# Define your OpenAI LLM instance
llm = OpenAI(api_key=OPENAI_API_KEY)

# Define the chain for initial extraction of main contract constraints
# Define the chain for initial extraction of main contract constraints
def create_initial_extraction_chain():
    initial_prompt = """
    You are an expert legal assistant tasked with analyzing a contract. Your goal is to carefully extract and organize all key terms and conditions into a structured JSON format. 
    Focus on main terms such as:
    - Budget constraints
    - Allowable work
    - Payment terms
    - Time constraints
    - Travel policies
    - Special provisions
    - Any other important sections
    
    
    Contract Text:
    {contract_text}
    
    Please return the result **strictly** in a valid JSON format.
    """
    
    prompt = PromptTemplate(template=initial_prompt, input_variables=["contract_text"])
    llm = OpenAI(api_key=OPENAI_API_KEY)  # Define the OpenAI LLM
    
    # Create an LLMChain for this step
    return LLMChain(prompt=prompt, llm=llm)

# Define the chain for updating JSON with each chunk of text
def create_update_json_chain():
    update_prompt = """
    The following is a JSON structure containing key contract terms and conditions.
    You will now be provided with another chunk of contract text. 
    Please read the chunk carefully and update the JSON with any new terms or amendments.
    
    If there is an amendment or clarification, update the relevant section. If there is a new term or section, add it.
    
    JSON:
    {existing_json}
    
    Contract Chunk:
    {contract_chunk}
    
    Updated JSON: 
    Make sure that the updated ouput is well_structured Json format. 
    """
    
    prompt = PromptTemplate(template=update_prompt, input_variables=["existing_json", "contract_chunk"])
    llm = OpenAI(api_key=OPENAI_API_KEY)  # Define the OpenAI LLM
    
    # Create an LLMChain for this step
    return LLMChain(prompt=prompt, llm=llm)







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
    llm = OpenAI(api_key=OPENAI_API_KEY)  # Define the OpenAI LLM
    return LLMChain(prompt=prompt, llm=OpenAI(api_key=OPENAI_API_KEY))

# Chain to update JSON with additional chunks of contract


# Main process to extract and update JSON with each contract chunk
def process_contract_in_chunks(contract_text):
    # Step 1: Create the initial extraction chain
    initial_extraction_chain = create_initial_extraction_chain()
    
    # Step 2: Run the chain to extract the initial JSON structure
    st.write("Extracting main constraints from the contract...")
    initial_json = initial_extraction_chain.run(contract_text=contract_text)
    
    # Step 3: Create a JSON validation chain to ensure the JSON is valid
    validation_chain = create_json_validation_chain()
    
    # Validate and correct the JSON using the secondary chain
    validated_json = validation_chain.run(generated_json=initial_json)

    # Step 4: Load the JSON structure
    try:
        current_json = json.loads(validated_json)
    except json.JSONDecodeError as e:
        st.error(f"JSON decoding error: {e}")
        st.error(f"Invalid JSON: {validated_json}")
        return

    # Step 5: Chunk the contract into manageable pieces
    st.write("Splitting the contract into chunks for further analysis...")
    chunks = chunk_contract_text(contract_text)
    
    # Step 6: Create the chain for updating JSON with each chunk
    update_json_chain = create_update_json_chain()

    # Step 7: Sequentially process each chunk
    for i, chunk in enumerate(chunks):
        st.write(f"Processing chunk {i+1}/{len(chunks)}...")
        updated_json = update_json_chain.run(existing_json=json.dumps(current_json), contract_chunk=chunk)
        
        # Validate and clean the updated JSON
        validated_updated_json = validation_chain.run(generated_json=updated_json)
        try:
            current_json = json.loads(validated_updated_json)  # Parse the updated JSON
        except json.JSONDecodeError as e:
            st.error(f"JSON decoding error after chunk {i+1}: {e}")
            st.error(f"Invalid updated JSON: {validated_updated_json}")
            return
        
    # Step 8: Final JSON output
    st.write("Final extracted and updated JSON:")
    return current_json
















# Function to clean the LLM response and make it valid JSON
def clean_json_string(json_string):
    # Replace invalid single quotes with double quotes
    json_string = re.sub(r"(?<!\\)'", '"', json_string)  # Replace single quotes with double quotes
    
    # Fix improperly nested double quotes
    json_string = re.sub(r'(\w+)\s*"\s*:\s*', r'"\1": ', json_string)  # Ensure correct quote usage for keys

    # Replace any double quotes inside values with escaped double quotes
    json_string = re.sub(r'":\s*"([^"]*?)"', lambda match: '": "{}"'.format(match.group(1).replace('"', '\\"')), json_string)
    
    # Remove trailing commas (e.g., in lists or objects)
    json_string = re.sub(r',\s*([\]}])', r'\1', json_string)  # Remove commas before closing brackets
    
    # Handle incomplete or cut-off parts (ensure proper termination)
    if not json_string.endswith('}'):
        json_string += '}'  # Ensure JSON closes if it was cut off

    return json_string


# Helper function to extract text from documents
def extract_text_from_document(doc_file):
    # Based on file type, extract text
    if doc_file.name.endswith(".pdf"):
        return extract_text_from_pdf(doc_file)
    elif doc_file.name.endswith(".docx"):
        return extract_text_from_docx(doc_file)
    else:
        st.error("Unsupported file type. Please upload a PDF or DOCX file.")
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

# Streamlit UI
st.title("Contract Term Extraction with Sequential Updates")

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
        
        # Proceed with chunking and processing
        final_json = process_contract_in_chunks(contract_text)
        st.json(final_json)
