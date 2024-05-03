import os
import glob
import streamlit as st

from utils import get_content, get_db, get_chain
from prompts import output_parser, welcome_template


def clear_chat_history():
    st.session_state.messages = [{'role': 'assistant', 'content': {'text': welcome_template, 'source': 'NO_SOURCE', 'picture': 'NO_PICTURE'}}]


def user_query(user_question, chain):
    answer = chain(user_question)['answer']
    # print(answer)
    return answer


def show_messege(text, source, picture):
    st.markdown(text)

    if source != 'NO_SOURCE':
        st.markdown(f'Source: {source}')

    if picture != 'NO_PICTURE':
        try:
            cols = st.columns(len(picture))
            cols_n = 0

            for k, v in picture.items():
                with cols[cols_n]:
                    st.image(k)
                    cols_n += 1
        except:
            pass


def main():
    st.set_page_config(page_title='Gemini Docs Chatbot', page_icon='🤖')

    with st.sidebar:
        st.header('Menu')

        # Upload PDF files
        with st.expander('PDF'):
            pdf_docs = st.file_uploader('Upload PDF Files', type=['pdf'], accept_multiple_files=True)
        
            if pdf_docs:
                if st.button('Submit', 'pdf_btn'):
                    with st.spinner('Processing...'):
                        pages = get_content(pdf_docs, 'pdf')
                        db = get_db(pages)
                        st.session_state.chain = get_chain(db)
                        st.session_state.messages.append({'role': 'assistant', 'content': {'text': 'Processing complete ✅', 'source': 'NO_SOURCE', 'picture': 'NO_PICTURE'}})

        # Enter web URL
        with st.expander('URL'):
            web_url = st.text_input('Enter a web URL')

            if web_url:
                if st.button('Submit', 'url_btn'):
                    with st.spinner('Processing...'):
                        docs = get_content(web_url, 'url')
                        db = get_db(docs)
                        st.session_state.chain = get_chain(db)
                        st.session_state.messages.append({'role': 'assistant', 'content': {'text': 'Processing complete ✅', 'source': 'NO_SOURCE', 'picture': 'NO_PICTURE'}})

        # Clear database and chat history
        if st.button('Clear'):
            clear_chat_history()
            for f in glob.glob('faiss_db/*'):
                os.remove(f)

    # Main content 
    st.title('Chat with Docs using Gemini 🤖')

    # Initialize chat history
    if 'messages' not in st.session_state.keys():
        clear_chat_history()

    # Show chat messages
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            show_messege(message['content']['text'], message['content']['source'], message['content']['picture'])

    # Add user input to message session
    if prompt := st.chat_input(disabled=False if 'chain' in st.session_state.keys() else True):
        st.session_state.messages.append({'role': 'user', 'content': {'text': prompt, 'source': 'NO_SOURCE', 'picture': 'NO_PICTURE'}})
        with st.chat_message('user'):
            st.markdown(prompt)

    # Display chat messages and bot response
    if st.session_state.messages[-1]['role'] != 'assistant':
        with st.chat_message('assistant'):
            with st.spinner('Thinking...'):
                answer = user_query(prompt, st.session_state.chain)

                try:
                    text = output_parser.parse(answer)['text']
                except:
                    text = answer

                try:
                    source = output_parser.parse(answer)['source']
                except:
                    source = 'NO_SOURCE'

                try:
                    picture = output_parser.parse(answer)['picture']
                except:
                    picture = 'NO_PICTURE'

                show_messege(text, source, picture)

        if answer is not None:
            message = {'role': 'assistant', 'content': {'text': text, 'source': source, 'picture': picture}}
            st.session_state.messages.append(message)


if __name__ == '__main__':
    main()