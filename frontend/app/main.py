import uuid

import streamlit as st

from app.client import BackendClient

st.set_page_config(page_title="AWS Support Bot", page_icon=":robot:", layout="wide")

_client = BackendClient()

# Keep session_id in the URL so history survives a page reload.
if "session_id" not in st.query_params:
    st.query_params["session_id"] = str(uuid.uuid4())

session_id: str = st.query_params["session_id"]

# On first load (or after the session_id changes), fetch history from the backend.
if st.session_state.get("session_id") != session_id:
    st.session_state["session_id"] = session_id
    try:
        st.session_state["messages"] = _client.get_history(session_id)
    except Exception:
        st.session_state["messages"] = []

title_col, new_col, clear_col = st.columns([7, 1, 1])
with title_col:
    st.title(":robot: AWS Support Bot")
    st.caption("Powered by Amazon Bedrock & Tavily · Live AWS Documentation")
with new_col:
    st.write("")
    if st.button("New chat", use_container_width=True):
        st.query_params["session_id"] = str(uuid.uuid4())
        st.rerun()
with clear_col:
    st.write("")
    if st.button("Clear chat", use_container_width=True):
        _client.clear_history(session_id)
        st.session_state["messages"] = []
        st.query_params["session_id"] = str(uuid.uuid4())
        st.rerun()

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask about AWS…"):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            content = _client.send_message(session_id, prompt)
        st.markdown(content)
        st.session_state["messages"].append({"role": "assistant", "content": content})
