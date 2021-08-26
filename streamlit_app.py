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
import itertools

if not firebase_admin._apps:
    creds = firebase_admin.credentials.Certificate(st.secrets["googleserviceaccount"])
    firebase_app = firebase_admin.initialize_app(creds)
    db = firestore.client()


@st.cache(show_spinner=False, suppress_st_warning=True)
def doSuccess():
    placeholder = st.empty()
    with placeholder.container():
        placeholder.success('Ready')
        placeholder.empty()

@st.cache(show_spinner=False, hash_funcs={"_thread.RLock": lambda _: None}, allow_output_mutation=True, suppress_st_warning=True)
def build(key):
    app_state = get_app_state()
    # status_text = st.empty()
    progress_bar = st.progress(0) 
    
    # status_text.text('Mounting S3 file system')
    fs = s3fs.S3FileSystem(anon=False, key=st.secrets["aws_access_key_id"], secret=st.secrets["aws_secret_access_key"])
    progress_bar.progress(20)
    if not os.path.isdir(key):
        # status_text.text('Fetching embeddings')
        os.makedirs(os.path.dirname(f"./{key}"), exist_ok=True)
        fs.get(f"s3://aspect-km/{key}/embeddings", f"./{key}/embeddings")
        fs.get(f"s3://aspect-km/{key}/config", f"./{key}/config")

    progress_bar.progress(60)
    embeddings = Embeddings({"method": "sentence-transformers", "path": "clip-ViT-B-32"})
    # status_text.text('Loading embeddings')        
    embeddings.load(key)

    progress_bar.progress(80)
    if app_state.get('model', '') == 'multilingual':
        embeddings.config["path"] = 'sentence-transformers/clip-ViT-B-32-multilingual-v1'
    # status_text.text('Loading multilingual embeddings')
        embeddings.model = embeddings.loadVectors()

    # status_text.text('Done')
    progress_bar.progress(100)
    progress_bar.empty()
    # status_text = st.empty()
    doSuccess()
    return embeddings

@st.cache(show_spinner=False, allow_output_mutation=True, hash_funcs={"_thread.RLock": lambda _: None, firebase_admin.App: id})
def db():
    if not firebase_admin._apps:
        creds = firebase_admin.credentials.Certificate(st.secrets["googleserviceaccount"])
        firebase_app = firebase_admin.initialize_app(creds)
    return firestore.client()


@st.cache(suppress_st_warning=True, show_spinner=False, hash_funcs={firebase_admin.App: id, "_thread.RLock": lambda _: None})
def firebaseCallback(d):
    app_state = get_app_state()
    if app_state.get('oid', False):
        doc_ref = db().collection(u'streamlit').document(app_state.get('oid', 'missing-s-query-param-from-streamlit'))
        doc_ref.set({
            u'results': d['results'], 
            u'query': d['query']
        }, merge=True)
    else:
        st.warning('Oops, are you running this outside of ASPECT Knowledge Platform?')

def get_app_state():
    app_state = st.experimental_get_query_params()
    app_state = {k: v[0] if isinstance(v, list) else v for k, v in app_state.items()}
    return app_state

@st.cache(show_spinner=False, hash_funcs={"_thread.RLock": lambda _: None}, allow_output_mutation=True)
def generate_presigned_url(object_key, bucket_name='aspect-km', expiry=604800):
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
    st.set_page_config(layout="wide")
    hide_menu_style = """
            <style>
                .css-1e5imcs, .e1tzin5v1 {margin: 0 !important;}
                a[class^="viewerBadge_container"] * {display: none !important; opacity: 0 !important}
                [data-baseweb="notification"] {margin-top: 60px !important;}
                .stTextInput {position: absolute !important; z-index: 1 !important;}
                #root > div:nth-child(1) {color: transparent !important}
                html {overflow: hidden !important;}
                .css-1y0tads {padding-top: 0rem;}
                .css-glyadz {height: auto !important; margin-bottom: 0 !important}
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
    embeddings_path = app_state.get('key', 'precedent-images-textai-multilingual-embedding')
    embeddings = build(embeddings_path)

    query = st.text_input("")


    if query:
        # cols = st.columns(l)
        l = int(app_state.get('limit',10))

        results = embeddings.search(query, l)
        # for i, result in enumerate(results):
        #     index, _ = result
        #     st.write(index)
        #     image = generate_presigned_url(f"precedent-images/{Path(index).name}")
        #     cols[i].image(image)

        firebaseCallback({'results': [{"format": "".join([s.lower() for s in Path(k).suffixes if not " " in s]), "filepath": k, "score": v, "url": generate_presigned_url(f"precedent-images/{Path(k).name}") } for k,v in results], 'query': query})
        # st.write({"query":query, "_": _, "embeddings": embeddings_path, **app_state})

if __name__ == "__main__":
    app()
