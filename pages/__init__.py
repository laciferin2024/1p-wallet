import streamlit as st




def initApp():
    from app import App
    if 'app' not in st.session_state:
        st.session_state.app = App()
    return st.session_state.app

app = initApp()