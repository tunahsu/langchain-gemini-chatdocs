import os

import google.generativeai as genai

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from prompts import condense_prompt, qa_prompt
from langchain.memory import ConversationBufferMemory
from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
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
        temperature=1.0,
        convert_system_message_to_human=True,
    )
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True) 
    retriever = db.as_retriever(search_type='mmr', search_kwargs={'k': 3})
    # compressor = LLMChainExtractor.from_llm(ChatGoogleGenerativeAI(model='gemini-pro', temperature=0))
    # compression_retriever = ContextualCompressionRetriever(base_compressor=compressor, base_retriever=retriever)

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm, 
        retriever=retriever,
        memory=memory,
        condense_question_prompt=condense_prompt,
        combine_docs_chain_kwargs={'prompt': qa_prompt},
        verbose=True
    )

    return chain