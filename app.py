import os
from dataclasses import dataclass
from queue import Queue

import streamlit as st
import streamlit.components.v1 as components
# @st.cache_data
# def get_timeout():
#   return timeout_seconds
from dataclasses_json import dataclass_json, LetterCase

st.set_page_config(page_title="Inactivity Timeout", page_icon="⏰")

st.header("User Inactivity Demo App v0")


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass(slots=True)
class App:
    queue: Queue = Queue()
    _timeout: int = 1

    def __post_init__(self):
        print("creating new app instance")

    @property
    def timeout_ms(self):
        return self.timeout * 1000

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        timeout_changed = self._timeout != value

        print(self._timeout, value)

        if not timeout_changed:
            print("timeout not changed")
            return

        self._timeout = value
        # self.queue.put(value)
        print("rerun after setting timeout")
        # st.rerun() FIXME


def onchange():
    # cannot pass st.rerun in callback
    print("reruns depreacted timeout")


app = st.session_state.get('app', App())

app.timeout = st.sidebar.slider("Set Timeout (seconds)", 1, 300, value=app.timeout, key="timeout_seconds",
                                on_change=onchange)

st.write(f"Times out user after inactivity of {app.timeout} seconds")

script_path = os.path.join('static', 'timeout.js')

with open(script_path) as f1:
    script_content = f1.read()

    # script_content = script_content.format('timeout_ms', app.timeout_ms)
    script_content = script_content.replace('3000', f'{app.timeout_ms}')
    # st.markdown(f"<script> {f1.read()}</script>", unsafe_allow_html=True)
    print("timeout updated in script")

    components.html(
        f"""
        <script> 
        {script_content}
         </script>
        """,
        # height=600,
    )
