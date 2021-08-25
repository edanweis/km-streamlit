import glob
import sys
import shutil
import os
from pathlib import Path
import streamlit as st
from PIL import Image
from txtai.embeddings import Embeddings
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import s3fs
import boto3

if not firebase_admin._apps:
    creds = firebase_admin.credentials.Certificate(st.secrets["googleserviceaccount"])
    firebase_app = firebase_admin.initialize_app(creds)
    db = firestore.client()


@st.cache(suppress_st_warning=True)
def doSuccess():
    placeholder = st.empty()
    with placeholder.container():
        placeholder.success('Ready')
        placeholder.empty()

@st.cache(hash_funcs={"_thread.RLock": lambda _: None}, allow_output_mutation=True, suppress_st_warning=True)
def build(key):
    status_text = st.empty()
    progress_bar = st.progress(0) 
    directory = f'{key}-multilingual-embedding'
    status_text.text('Mounting S3 file system')
    fs = s3fs.S3FileSystem(anon=False, key=st.secrets["aws_access_key_id"], secret=st.secrets["aws_secret_access_key"])
    progress_bar.progress(20)
    # status_text.text('Copying embeddings')
    if not os.path.isdir(directory):
        os.makedirs(os.path.dirname(f"./{directory}"), exist_ok=True)
        fs.get(f"s3://aspect-km/{directory}/embeddings", f"./{directory}/embeddings")
        fs.get(f"s3://aspect-km/{directory}/config", f"./{directory}/config")

    progress_bar.progress(60)
        
    embeddings = Embeddings({"method": "sentence-transformers", "path": "clip-ViT-B-32"})
    embeddings.load(directory)

    progress_bar.progress(80)
    
    embeddings.config["path"] = 'sentence-transformers/clip-ViT-B-32-multilingual-v1'
    embeddings.model = embeddings.loadVectors()

    progress_bar.progress(100)
    progress_bar.empty()
    status_text.text('')
    doSuccess()
    return embeddings

@st.cache(allow_output_mutation=True, hash_funcs={firebase_admin.App: id})
def db():
    if not firebase_admin._apps:
        creds = firebase_admin.credentials.Certificate(st.secrets["googleserviceaccount"])
        firebase_app = firebase_admin.initialize_app(creds)
        db = firestore.client()
    return db


@st.cache(hash_funcs={firebase_admin.App: id})
def firebaseCallback(results, app_state):
    app_state = get_app_state()
    if app_state.get('s', False):
        doc_ref = db().collection(u'streamlit').document(app_state.get('s', 'missing-s-query-param-from-streamlit'))
        doc_ref.set({
            u'results': results
        }, merge=True)
    else:
        st.warning('Oops, are you running this outside of ASPECT Knowledge Platform?')

def get_app_state():
    app_state = st.experimental_get_query_params()
    app_state = {k: v[0] if isinstance(v, list) else v for k, v in app_state.items()}
    st.write(app_state)
    return app_state

@st.cache(hash_funcs={"_thread.RLock": lambda _: None}, allow_output_mutation=True)
def generate_presigned_url(object_key, bucket_name='aspect-km', expiry=3600):
    client = boto3.client("s3",region_name='ap-southeast-2',
                          aws_secret_access_key=st.secrets["aws_secret_access_key"],
                          aws_access_key_id=st.secrets["aws_access_key_id"])
    try:
        response = client.generate_presigned_url('get_object',
                          Params={'Bucket': bucket_name,'Key': object_key},
                          ExpiresIn=expiry)
        return response
    except ClientError as e:
        print(e)
        

def app():
    embeddings_path = 'precedent-images-textai'
    embeddings = build(embeddings_path)
    hide_menu_style = """
            <style>
                html {overflow: hidden !important;}
                .css-1y0tads {padding-top: 0rem;}
                body {background: transparent !important;}
                section {align-items: start;}
                .stTextInput input {background: white;}
                [data-testid="stDecoration"]{display: none !important}
                .stApp {background: transparent !important;}
                .block-container {padding: 0; margin:0}
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_menu_style, unsafe_allow_html=True)
    # see https://pmbaumgartner.github.io/streamlitopedia/essentials.html
    app_state = get_app_state()

    query = st.text_input("")

    if query:
        for result in embeddings.search(query, 10):
            index, _ = result
            st.write(index)
            st.image(generate_presigned_url(f"precedent-images/{Path(index).name}"))
            firebaseCallback({"index": index.info()['name'], "query":query, "_": _, "s": app_state.get('s', {}), "embeddings": embeddings_path }, app_state)

if __name__ == "__main__":
    app()
