import streamlit as st
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from scripts.file_readers import read_pdf, read_word, read_excel
from dotenv import load_dotenv
import os

from langchain import OpenAI, PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage


# Load environment variables from .env file
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Verify the key was loaded correctly
if openai_api_key is None:
    st.error("API Key is missing. Please add it to the .env file.")
else:
    st.success("API Key loaded successfully!")

llm = OpenAI(temperature=0.5, openai_api_key=openai_api_key)

template = """
You are an expert assistant trained to extract information from documents. You have access to the content of the following document: {{document_content}}.

Please provide a detailed answer to the following question based on the PDF content:

Question: {{question}}

Answer:

"""


# Function to extract conditions and chat with the document
def chat_with_document(contract_text, question):
    # Create a prompt template with Langchain
    prompt = PromptTemplate(
        input_variables=["document_content", "question"],
        template=template
    )
    
    # Set up the chain with the prompt and model
    document_chain = LLMChain(
        llm=llm,
        prompt=prompt
    )
    
    # Run the chain with the document content and user question
    result = document_chain.run({
        "document_content": contract_text,
        "question": question
    })
    
    return result














# Function to chunk the document text
def chunk_text(text, chunk_size=2000):
    """
    Splits text into chunks of a specified size to avoid exceeding token limits.
    """
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

# Function to extract conditions and chat with the document
def chat_with_document(contract_text, user_input):
    # Set up the chat model (e.g., OpenAI Chat model)
    chat = ChatOpenAI(temperature=0.5)

    # Chunk the document text to avoid exceeding token limit
    document_chunks = chunk_text(contract_text)

    # Initialize an empty result string
    final_answer = ""

    # Process each chunk individually and aggregate responses
    for chunk in document_chunks:
        # Create a simple prompt template
        system_message = SystemMessage(
            content="You are an AI assistant trained to extract information from documents."
        )
        
        # Build the chat history (one chunk at a time)
        prompt = HumanMessage(
            content=f"Here is a part of a contract: {chunk}. \n\nQuestion: {user_input}"
        )
        
        # Run the chat model for the current chunk
        messages = [system_message, prompt]
        response = chat(messages)
        
        # Aggregate the responses
        final_answer += response.content + "\n"

    return final_answer

# Streamlit application
st.title("Document Interaction System")

# File uploader for PDF, Word, and Excel
st.header("Upload Document (PDF, Word, Excel)")
document_file = st.file_uploader("Choose a document file", type=["pdf", "docx", "xlsx"])

if document_file is not None:
    file_type = document_file.name.split('.')[-1]
    
    if file_type == 'pdf':
        document_text = read_pdf(document_file)
        st.write("PDF File Uploaded Successfully!")

    elif file_type == 'docx':
        document_text = read_word(document_file)
        st.write("Word File Uploaded Successfully!")

    elif file_type == 'xlsx':
        df = read_excel(document_file)
        document_text = df.to_string()
        st.write("Excel File Uploaded Successfully!")
        st.dataframe(df)

    # Show the document content in a text area for reference
    st.text_area("Document Text", document_text, height=300)

    # Chat interface
    user_input = st.text_input("Ask a question about the document:")
    
    if user_input:
        response = chat_with_document(document_text, user_input)
        st.text_area("Chat Response", response, height=300)

