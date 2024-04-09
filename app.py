import os
import glob
import streamlit as st

from utils import get_content, get_db, get_chain
from prompts import output_parser


def clear_chat_history():
    st.session_state.messages = [{'role': 'assistant', 'content': 'Let me read some documents and ask me some questions!'}]


def user_query(user_question, chain):
    response = chain({'query': user_question})
    return response


def main():
    st.set_page_config(page_title='Gemini Docs Chatbot', page_icon='🤖')

    # Sidebar for uploading PDF files
    with st.sidebar:
        st.header('Menu')

        with st.expander('PDF'):
            pdf_docs = st.file_uploader('Upload PDF Files', type=['pdf'], accept_multiple_files=True)
        
            if pdf_docs:
                if st.button('Submit', 'pdf_btn'):
                    with st.spinner('Processing...'):
                        pages = get_content(pdf_docs, 'pdf')
                        db = get_db(pages)
                        st.session_state.chain = get_chain(db)
                        st.session_state.messages.append({'role': 'assistant', 'content': "Processing complete ✅"})

        with st.expander('URL'):
            web_url = st.text_input('Enter a web URL')

            if web_url:
                if st.button('Submit', 'url_btn'):
                    with st.spinner('Processing...'):
                        docs = get_content(web_url, 'url')
                        db = get_db(docs)
                        st.session_state.chain = get_chain(db)
                        st.session_state.messages.append({'role': 'assistant', 'content': "Processing complete ✅"})

        if st.button('Load Winmate Product Data'):
            with st.spinner('Processing...'):
                docs = get_content(web_url, 'winmate_product')
                db = get_db(docs)
                st.session_state.chain = get_chain(db)
                st.session_state.messages.append({'role': 'assistant', 'content': "Processing complete ✅"})

        if st.button('Clear'):
            clear_chat_history()
            for f in glob.glob('faiss_db/*'):
                os.remove(f)

    # Main content 
    st.title('Chat with Docs using Gemini 🤖')

    if 'messages' not in st.session_state.keys():
        clear_chat_history()

    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.write(message['content'])

    if prompt := st.chat_input(disabled=False if 'chain' in st.session_state.keys() else True):
        st.session_state.messages.append({'role': 'user', 'content': prompt})
        with st.chat_message('user'):
            st.write(prompt)

    # Display chat messages and bot response
    if st.session_state.messages[-1]['role'] != 'assistant':
        with st.chat_message('assistant'):
            with st.spinner('Thinking...'):
                response = user_query(prompt, st.session_state.chain)
                text = output_parser.parse(response['result'])['text']
                picture = output_parser.parse(response['result'])['picture']
                st.markdown(text)

                if picture != 'NO_PICTURE':
                    print(picture)
                    cols = st.columns(len(picture))
                    cols_n = 0

                    for k, v in picture.items():
                        with cols[cols_n]:
                            st.image(v)
                            cols_n += 1

        if response is not None:
            message = {'role': 'assistant', 'content': text}
            st.session_state.messages.append(message)


if __name__ == '__main__':
    main()