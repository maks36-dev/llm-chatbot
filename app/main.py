import streamlit as st
import os

# init db
from db import setup_all_db, update_knowledge_table, update_ground_truth_table
setup_all_db()
update_knowledge_table(os.path.join(os.getcwd(), 'data/data.json'))
update_ground_truth_table(os.path.join(os.getcwd(), 'data/ground_truth_data.csv'))

# save transformer
from sentence_transformers import SentenceTransformer
bert = SentenceTransformer('bert-base-nli-stsb-mean-tokens')
current_directory = os.getcwd()
bert.save(os.path.join(current_directory, 'saved_models/'))

# init elasticsearch
from vectSearch import init_es,calculate_accuracy
init_es()
calculate_accuracy()

# load model
from model import ask


# create streamlit app
if __name__ == "__main__":
    st.set_page_config(page_title="🦙💬 Quotes for everyone")

    def clear_chat_history():
        st.session_state.messages = [{"role": "assistant", "content": "I can offer the quote for your question or statement."}]
    st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

    with st.sidebar:
        st.title('🦙💬 Quotes for everyone')
        
        temperature = st.sidebar.slider('temperature', min_value=0.01, max_value=5.0, value=0.1, step=0.01)
        top_p = st.sidebar.slider('top_p', min_value=0.01, max_value=1.0, value=0.9, step=0.01)
        

    if "messages" not in st.session_state.keys():
        st.session_state.messages = [{"role": "assistant", "content": "I can offer the quote for your question or statement."}]


    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])


    def generate_llama2_response(prompt_input):
        settings = {
            "temperature":temperature,
            "top_p":top_p
        }
        output = ask(prompt_input, settings)

        return output


    if prompt := st.chat_input(disabled=False):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)


    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = generate_llama2_response(prompt)
                placeholder = st.empty()
                full_response = ''
                for item in response:
                    full_response += item
                    placeholder.markdown(full_response)
                placeholder.markdown(full_response)
        message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(message)
