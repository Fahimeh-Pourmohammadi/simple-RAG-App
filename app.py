import streamlit as st
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from scripts.file_readers import read_pdf, read_word, read_excel
from dotenv import load_dotenv
import os
import json

# Load environment variables from .env file
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Verify the key was loaded correctly
if openai_api_key is None:
    st.error("API Key is missing. Please add it to the .env file.")
else:
    st.success("API Key loaded successfully!")

llm = OpenAI(temperature=0.5, openai_api_key=openai_api_key)


# Define a prompt template that asks for JSON output
template = """
You are an expert legal assistant tasked with analyzing a contract. Your goal is to carefully extract and organize all key terms and conditions into a structured JSON format. Please ensure that:

- All main sections are extracted, even if they are not explicitly listed below.
- If any amendments are found in the contract, they must be noted and incorporated by updating the relevant sections or adding new terms where necessary.

The main sections you should focus on include, but are not limited to:
- Budget constraints (include any limits, multipliers, exceptions, and penalties)
- Allowable work (describe what types of work are permitted, restricted, or prohibited)
- Payment terms (include payment schedule, conditions for payment, and penalties for late payments)
- Time constraints (include deadlines, milestones, and any conditions regarding delays)
- Travel policies (detail any travel-related provisions, including approval requirements, expense caps, and special conditions)
- Special provisions (note any other unique terms, exceptions, or penalties that may apply)

### Additional Instructions:
- Pay careful attention to any amendments and ensure they are reflected in the appropriate sections of the JSON, either by updating existing terms or creating new entries.
- If there are sections in the contract that are not explicitly listed above, be sure to add them as additional main sections with their relevant terms and sub-terms.
- Be thorough and do not skip any details.

The contract text is provided below:

{contract_text}

Please return the extracted information in JSON format, ensuring amendments are incorporated:


"""
template_3 = """
You are a highly skilled contract analyst. Your task is to read the contract carefully and extract **all constraints** or rules that affect the execution of tasks, financial limitations, work conditions, or other policies.

Constraints can include, but are not limited to:
- Budget constraints (limits on spending, specific budgets per task, total contract budget, etc.)
- Time constraints (deadlines, project timelines, task durations, etc.)
- Work constraints (types of work allowed or prohibited, conditions for task execution, etc.)
- Payment terms (schedules, deposit requirements, milestones, etc.)
- Travel policies (travel expense limits, pre-approvals, multipliers for special cases like urgent or high-cost travel)
- Any other constraints or conditions not explicitly listed here but mentioned in the contract.

For each identified constraint, provide a brief explanation(JSON list with keywords for different conditions) of its impact on the contract and format the response in JSON for clarity.

Contract:
{contract_text}

Extracted Constraints (in JSON):
"""
template_2 = """
You are a legal assistant helping to extract important conditions from a contract.
The contract is provided below. Extract and summarize the following conditions, and format the response as valid JSON:
- Budget constraints (in numbers)
- Types of allowable work (list of strings)
- Time constraints (in dates)
- Payment terms (describe briefly)

Contract:
{contract_text}

Extracted Conditions (in JSON):
"""
def extract_conditions(contract_text):
    # Create a prompt template with Langchain
    prompt = PromptTemplate(
        input_variables=["contract_text"],
        template=template
    )
    # Set up the chain with the prompt and model
    contract_condition_chain = LLMChain(
        llm=llm,
        prompt=prompt
    )
    # Run the chain to get the output
    result = contract_condition_chain.run(contract_text)
    st.text_area("Extracted Contract Conditions", result, height=1500)
    return result









st.title("Contract Verification System")

# Contract file uploader for PDF, Word, and Excel
st.header("Upload Contract File (PDF, Word, Excel)")
contract_file = st.file_uploader("Choose a contract file", type=["pdf", "docx", "xlsx"])

if contract_file is not None:
    file_type = contract_file.name.split('.')[-1]
    
    if file_type == 'pdf':
        contract_text = read_pdf(contract_file)
        st.write("PDF File Uploaded Successfully!")
        extract_conditions(contract_text)
       # st.text_area("Contract Text", contract_text, height=300)

    elif file_type == 'docx':
        contract_text = read_word(contract_file)
        st.write("Word File Uploaded Successfully!")
        extract_conditions(contract_text)
        #st.text_area("Contract Text", contract_text, height=300)

    elif file_type == 'xlsx':
        df = read_excel(contract_file)
        contract_text = df.to_string()
        st.write("Excel File Uploaded Successfully!")
        extract_conditions(contract_text)
        st.dataframe(df)

# Task description file uploader for PDF, Word, and Excel
st.header("Upload Task Descriptions (PDF, Word, Excel)")
tasks_file = st.file_uploader("Choose a task file", type=["pdf", "docx", "xlsx"], key="tasks")

if tasks_file is not None:
    file_type = tasks_file.name.split('.')[-1]
    
    if file_type == 'pdf':
        tasks_text = read_pdf(tasks_file)
        st.write("PDF Task File Uploaded Successfully!")
        st.text_area("Task Description Text", tasks_text, height=600)

    elif file_type == 'docx':
        tasks_text = read_word(tasks_file)
        st.write("Word Task File Uploaded Successfully!")
        st.text_area("Task Description Text", tasks_text, height=600)

    elif file_type == 'xlsx':
        df_tasks = read_excel(tasks_file)
        st.write("Excel Task File Uploaded Successfully!")
        st.dataframe(df_tasks)


