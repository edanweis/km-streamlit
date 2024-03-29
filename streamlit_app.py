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
from copy import deepcopy

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

    embeddings_dir = f"{key}-multilingual-embedding"
    
    Path(embeddings_dir).mkdir(parents=True, exist_ok=True)
    
    fs.get(f"s3://aspect-km/{embeddings_dir}/embeddings", f"./{embeddings_dir}/embeddings")
    fs.get(f"s3://aspect-km/{embeddings_dir}/config", f"./{embeddings_dir}/config")

    progress_bar.progress(60)

    embeddings_english = Embeddings({"method": "sentence-transformers", "path": "sentence-transformers/clip-ViT-B-32"})
    
    embeddings_english.load(embeddings_dir) # contains the corrected config from txtai==3.0.0
    
    # embeddings_multilingual = deepcopy(embeddings_english)

    # embeddings_multilingual.config["path"] = 'sentence-transformers/clip-ViT-B-32-multilingual-v1'
    # embeddings_multilingual.model = embeddings_multilingual.loadVectors()
    
    progress_bar.progress(100)
    progress_bar.empty()
    # status_text = st.empty()
    doSuccess()
    return embeddings_english

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
            u'results': d.get('results', []), 
            u'query': d.get('query', []),
            u'loading': d.get('loading', False)
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
    firebaseCallback({"loading": True})
    st.set_page_config(layout="wide")
    hide_menu_style = """
            <style>
                .block-container {pointer-events: none !important}
                .stTextInput {pointer-events: all !important;}
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
    app_state = get_app_state()

    if app_state.get('debug', 'false').lower() != 'true':
        st.markdown(hide_menu_style, unsafe_allow_html=True)
    # see https://pmbaumgartner.github.io/streamlitopedia/essentials.html
    embeddings_path = app_state.get('key', 'precedent-images-textai')
    embeddings_english = build(embeddings_path)

    query = st.text_input("")
    firebaseCallback({"loading": False})

    if query:
        # cols = st.columns(l)
        l = int(app_state.get('limit',10))
        results = embeddings_english.search(query, l)
        # for i, result in enumerate(results):
        #     index, _ = result
        #     st.write(index)
        #     image = generate_presigned_url(f"precedent-images/{Path(index).name}")
        #     cols[i].image(image)

        firebaseCallback({'model_path': 'sentence-transformers/clip-ViT-B-32', 'results': [{"format": "".join([s.lower() for s in Path(k).suffixes if not " " in s]), "filepath": k, "score": v, "url": generate_presigned_url(f"precedent-images/{Path(k).name}"), "thumbnail": generate_presigned_url(f"precedent-images-300/{Path(k).stem}.jpg") } for k,v in results], 'query': query, 'loading':False})
        # st.write({"query":query, "_": _, "embeddings": embeddings_path, **app_state})

if __name__ == "__main__":
    app()
