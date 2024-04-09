import os

import google.generativeai as genai

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.chains import RetrievalQA
from prompts import QA_PROMPT
from langchain.memory import ConversationBufferMemory
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from webscraper import getGeneralWebData

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))


def get_content(source, type):
    if type == 'pdf':
        pages = list()
        for pdf in source:
            pdf_path = os.path.join('docs/pdf/', pdf.name)
            with open(pdf_path, 'wb') as f: 
                f.write(pdf.getbuffer())
            loader = PyPDFLoader(pdf_path)
            pages += loader.load_and_split()
        return pages
    
    elif type == 'url':
        file = getGeneralWebData(source)
        loader = TextLoader(file)
        docs = loader.load()
        return docs
    
    elif type == 'winmate_product':
        loader = DirectoryLoader('docs/json/winmate_product/', glob='**/*.json', loader_cls=TextLoader)
        docs = loader.load()
        return docs
        

def get_db(docs):
    embedding = GoogleGenerativeAIEmbeddings(model='models/embedding-001')
    try:
        db = FAISS.load_local('faiss_db', embeddings=embedding, allow_dangerous_deserialization=True)
        db.add_documents(docs)
    except Exception as e:
        db = FAISS.from_documents(docs, embedding=embedding)
    db.save_local('faiss_db')
    return db


def get_chain(db):
    llm = ChatGoogleGenerativeAI(
        model='gemini-pro',
        client=genai,
        temperature=0.5,
        convert_system_message_to_human=True,
    )

    # question_generator = LLMChain(llm=llm, prompt=CONDENSE_QUESTION_PROMPT)
    # doc_chain = load_qa_chain(llm=llm, chain_type='stuff', prompt=QA_PROMPT)

    retriever = db.as_retriever(search_type='mmr', search_kwargs={'k': 3})
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True, input_key='question') 

    # chain = ConversationalRetrievalChain(
    #     retriever=retriever,
    #     question_generator=question_generator,
    #     combine_docs_chain=doc_chain,
    #     memory=memory,
    #     verbose=True,
    #     return_source_documents=True
    # )

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type='stuff',
        retriever=retriever,
        verbose=True,
        chain_type_kwargs={
            'verbose': True,
            'prompt': QA_PROMPT,
            'memory': memory,
        }
    )

    return chain