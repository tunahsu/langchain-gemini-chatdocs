import os
import json
import requests
import datetime

import google.generativeai as genai

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from prompts import condense_prompt, qa_prompt
from langchain.memory import ConversationBufferMemory
from langchain_community.document_loaders import PyPDFLoader, TextLoader, WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv


load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))


def get_web_data(url):
    try:
        res = requests.get(url=url)
    except requests.RequestException as e:
        raise e
    
    html_page = res.content
    soup = BeautifulSoup(html_page, features='html.parser')

    loader = WebBaseLoader(url, bs_get_text_kwargs={'separator': ' ', 'strip': True})
    docs = loader.load()

    content = docs[0].page_content
    imgs = soup.find_all('img')

    data = {
        'title': soup.title.get_text(),
        'content': content,
        'images': [{'alt': img.get('alt'), 'url': urljoin(url, img.get('src'))} for img in imgs]
    }

    with open(os.path.join('docs/json/', f'{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.json'), 'w', encoding='UTF-8') as f: 
        json.dump(data, f, ensure_ascii=False, indent = 4)

    return f.name


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
        file = get_web_data(source)
        loader = TextLoader(file, encoding='UTF-8')
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