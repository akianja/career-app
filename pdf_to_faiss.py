# Import necessary libraries and modules for file management, AI modeling, document processing, vector storage, and environment management.
import os
import openai
from openai import AsyncOpenAI 
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.runnables import RunnablePassthrough
from langchain.schema.runnable.config import RunnableConfig
from operator import itemgetter
from langchain.prompts import ChatPromptTemplate
from ragas.testset.evolutions import simple, reasoning, multi_context
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, answer_correctness, context_recall, context_precision
import chainlit as cl  
from dotenv import load_dotenv

# Load environment variables, such as API keys, from a .env file.
load_dotenv()

# Initialize the OpenAI embeddings model, specifying which model to use for generating text embeddings.
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

# Specify the directory that contains the PDF files you want to process.
documents_directory = "downloaded_pdfs"

# A flag to keep track of whether we're processing the first document.
first_doc = True

# Iterate over all files in the specified directory.
for filename in os.listdir(documents_directory):

    # Check if the file is a PDF based on its extension.
    if filename.endswith(".pdf"):
        # Construct the full path to the PDF file.
        file_path = os.path.join(documents_directory, filename)
        # Load the PDF file content using the PyMuPDFLoader.
        loader = PyMuPDFLoader(file_path)
        documents = loader.load()

        # Split the document text into smaller chunks to improve processing and retrieval efficiency.
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=50)
        documents = text_splitter.split_documents(documents)

        # For the first document, create a new FAISS VectorStore from its content.
        if first_doc == True:
            # Create a FAISS VectorStore from documents
            vector_store = FAISS.from_documents(documents, embeddings)

        # For subsequent documents, create a temporary VectorStore and merge it with the main one.
        else:
            temp_vector_store = FAISS.from_documents(documents, embeddings)
            vector_store.merge_from(temp_vector_store)

    # After processing the first document, set this flag to False so that the above if condition is not met again.
    first_doc = False

# Once all documents have been processed and their vectors stored, save the FAISS index to the local filesystem for future use.
vector_store.save_local("faiss_index")
