import streamlit as st
import logging
import sys
import os
import inspect

# Add parent directory to path for direct page access
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Common variables shared by pages
DIRECTION_MAP = {
    "Up": "U", "Down": "D", "Left": "L", "Right": "R", "Skip": "S"
}

def initApp():
    """Initialize or retrieve the App instance from session state"""
    try:
        # Import here to avoid circular import issues with Streamlit
        from app import App

        # If an App instance exists in session, reuse it. Otherwise create a fresh one.
        if 'app' not in st.session_state:
            st.session_state.app = App()
        else:
            # Ensure the session-backed fields are synchronized into the live App
            try:
                st.session_state.app.load_from_session()
            except Exception as e:
                logging.exception(f"Failed to load from session: {e}")
                # If loading fails, recreate a fresh App to avoid stale state
                st.session_state.app = App()

        return st.session_state.app
    except ImportError as e:
        logging.error(f"Error importing App: {e}")
        # For direct page access
        if 'app' in st.session_state:
            return st.session_state.app
        else:
            st.error("⚠️ Application not properly initialized. Please return to the main page.")
            st.info("👈 Go to the home page to initialize the app properly.")
            st.stop()
            return None
    except Exception as e:
        logging.error(f"Error initializing app: {e}")
        st.error(f"Error initializing app: {e}")
        st.stop()
        return None

# Initialize app
app = initApp()