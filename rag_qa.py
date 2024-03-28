# Import necessary libraries for various functionalities such as file and environment management, asynchronous operations, text processing, vector storage, and chatbot creation.
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
from datasets import Dataset
import chainlit as cl  
from dotenv import load_dotenv

# Load environment variables from a .env file, typically used for sensitive information like API keys.
load_dotenv()

final_result = None

# Instantiate an embeddings model from OpenAI, specifying the model to use for text embeddings. This is used to convert text into a vector representation.
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

# Load a local FAISS index, providing an efficient way to search for similar vectors. This index is used for retrieving information related to the user's query.
vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

# Convert the vector store into a retriever, enabling the chatbot to fetch relevant information based on vector similarity.
retriever = vector_store.as_retriever()


# Define a prompt template for the question-answering part of the chatbot. This template guides the generation of answers based on the user's input.
template = """Determine which programs and faculties the entered job description should be associated with. List all that are applicable.  You will get a reward for the more programs you list as long as they are somewhat applicable.  List them in the following format:  Program:..... new line Faculty:..... 2 new lines If you cannot answer the question with the context, please respond with 'No Program':

Context:
{context}

Question:
{question}
"""
prompt = ChatPromptTemplate.from_template(template)

# Function to set up a retrieval-augmented QA chain. This integrates the retriever with a QA model to enhance the chatbot's responses with relevant context.
def setup_retrieval_augmented_qa_chain(retriever, prompt, primary_qa_llm):
    """
    Set up the retrieval-augmented QA chain using given components.
    """
    return (
        {"context": itemgetter("question") | retriever, "question": itemgetter("question")}
        | RunnablePassthrough.assign(context=itemgetter("context"))
        | {"response": prompt | primary_qa_llm, "context": itemgetter("context")}
    )


# Initialize a basic QA model from OpenAI, setting the model name and the response generation temperature.
primary_qa_llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

# Using the defined components, set up the retrieval-augmented QA chain. This chain is used for processing user queries and generating responses.
retrieval_augmented_qa_chain = setup_retrieval_augmented_qa_chain(retriever, prompt, primary_qa_llm)

# Set environment variables for configuring and tracing operations using Langsmith, specifying project details and API keys.
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Career Coordinator AI"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")



# Decorator to define the function that runs at the start of a chat session, prompting the user to enter a job description.
@cl.on_chat_start
async def start():
    # Sending an action button within a chatbot message
    await cl.Message(content="Enter the job description").send()


# Decorator to define the function that handles incoming messages. It uses the retrieval-augmented QA chain to process the job description and generate a response.
@cl.on_message
async def main(message: cl.Message):

    result = retrieval_augmented_qa_chain.invoke({"question": message.content})
    
    final_result = result["response"].content


    if final_result=="No Program":
        await cl.Message(
            content = "I could not find a program that can be linked to this job description.",
        ).send()
    else:
        # Send a response back to the user
        await cl.Message(
            content = final_result,
        ).send()
        # Sending an action button within a chatbot message
        actions = [
            #Pass the initial response to the button function through the value attribute so that the list of related programs are added to the context when requesting the associated courses.
            cl.Action(name="course_button", value=final_result, label="Show Courses", description="Click me!", collapsed=False)
        ]

        await cl.Message(content="Click the button to display courses or enter another job description:", actions=actions).send()


# Decorator to define the function that handles the action callback when the user clicks a button (e.g., to show courses for a program).
@cl.action_callback("course_button")
async def on_action(action):
    template2 = """List the courses for each program.':

    Context:
    {context}

    Question:
    {question}
    """
    prompt2 = ChatPromptTemplate.from_template(template2)
    retrieval_augmented_qa_chain = setup_retrieval_augmented_qa_chain(retriever, prompt2, primary_qa_llm)
    result = retrieval_augmented_qa_chain.invoke({"question": action.value})
    await cl.Message(
        content = result["response"].content,
    ).send()
