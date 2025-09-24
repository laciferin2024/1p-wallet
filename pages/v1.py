import streamlit as st

# import time
# from threading import Timer

# st.set_page_config(page_title="Inactivity Timeout", page_icon="⏰")

st.header("v1 will be implemented in python, [wip]")

# # Function to reset the timer on user activity
# def reset_timer():
#     global timer
#     timer.cancel()
#     timer = Timer(timeout_seconds, timeout_callback)
#     timer.start()

# # Function to handle user inactivity timeout
# def timeout_callback():
#     st.session_state.is_timed_out = True
#     st.experimental_rerun()

# # Set timeout duration in seconds
# timeout_seconds = st.sidebar.slider("Set Timeout (seconds)", 1, 300, 2,key="timeout_seconds")

# # Initialize timer
# timer = Timer(timeout_seconds, timeout_callback)
# timer.start()

# # Check if the session is timed out
# if hasattr(st.session_state, "is_timed_out") and st.session_state.is_timed_out:
#     st.warning("Session timed out due to inactivity. Refresh the page to start a new session.")
#     st.markdown(f"""<script>alert("session timeout after {timeout_seconds}s"); </script>""")
# else:
#     # Listen for user activity and reset the timer
#     st.session_state.is_timed_out = False

#     st.write("# Streamlit App with Timeout")

#     # Add your app content here
#     st.write("This is your Streamlit app content.")

#     # Reset the timer on user activity
#     st.text("Interact with the app to reset the timer.")
#     reset_timer()
