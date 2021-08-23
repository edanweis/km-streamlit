"""
Streamlit version of https://colab.research.google.com/github/neuml/txtai/blob/master/examples/13_Similarity_search_with_images.ipynb

Requires streamlit and torchvision to be installed.
  pip install streamlit torchvision
"""

import glob
import sys
import shutil
import os
from pathlib import Path

import streamlit as st

from PIL import Image

from txtai.embeddings import Embeddings

# import firebase_admin
# from firebase_admin import credentials
# from firebase_admin import firestore

import s3fs

import boto3

# if not firebase_admin._apps:
#     cred = credentials.Certificate('./aspect-km-4e35c3950fe3.json')
#     firebase_admin.initialize_app(cred)
#     db = firestore.client()


def images(directory):
    """
    Generator that loops over each image in a directory.

    Args:
        directory: directory with images
    """

    for path in glob.glob(directory + "/*jpg") + glob.glob(directory + "/*png"):
        yield (path, Image.open(path), None)


@st.cache(suppress_st_warning=True)
def doSuccess():
    placeholder = st.empty()
    with placeholder.container():
    # st.balloons()
        placeholder.success('Ready')
        placeholder.empty()


<<<<<<< HEAD
def build(key):
    status_text = st.empty()
    progress_bar = st.progress(0) 
    directory = f'{key}-embedding'
=======
@st.cache(hash_funcs={st.secrets.Secrets: id}, suppress_st_warning=True)
def build(key):
    status_text = st.empty()
    progress_bar = st.progress(0) 
    directory = f'./{key}-embedding'
>>>>>>> 6bbc65de2c338c4cd5edb7a5f310dbd70d074e16
    # if 'embeddings' in vars() or 'e
    # mbeddings' in globals():
    #     return embeddings
    # else:
    # 
    status_text.text('Mounting S3 file system')
<<<<<<< HEAD
    fs = s3fs.S3FileSystem(anon=False, key=st.secrets.aws_access_key_id, secret=st.secrets.aws_secret_access_key)
=======
    fs = s3fs.S3FileSystem(anon=False, key=st.secrets["aws_access_key_id"], secret=st.secrets["aws_secret_access_key"])
>>>>>>> 6bbc65de2c338c4cd5edb7a5f310dbd70d074e16
    progress_bar.progress(20)
    status_text.text('Copying embeddings')
    if not os.path.isdir(directory):
        os.makedirs(os.path.dirname(f"./{directory}"), exist_ok=True)
        fs.get(f"s3://aspect-km/{directory}/embeddings", f"./{directory}/embeddings")
        fs.get(f"s3://aspect-km/{directory}/config", f"./{directory}/config")

    progress_bar.progress(60)
    # status_text.text('Downloading CLIP model from Sentence Transformers')
    # clippath = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'clip-ViT-B-32')
    embeddings = Embeddings()
    progress_bar.progress(80)
    embeddings.load(f"./{directory}")
    progress_bar.progress(100)
    progress_bar.empty()
    status_text.text('')
    doSuccess()
    return embeddings

# @st.cache(allow_output_mutation=True, hash_funcs={firebase_admin.App: id})
# def db():
#     if not firebase_admin._apps:
#         cred = credentials.Certificate('./aspect-km-4e35c3950fe3.json')
#         firebase_admin.initialize_app(cred)
#     return firestore.client()


# @st.cache(hash_funcs={firebase_admin.App: id, s3fs.core.S3File: id})
# def firebaseCallback(results, app_state):
#     app_state = get_app_state()
#     if app_state['s']:
#         doc_ref = db().collection(u'streamlit').document(app_state['s'])
#         doc_ref.set({
#             u'results': results
#         }, merge=True)

def get_app_state():
    app_state = st.experimental_get_query_params()
    app_state = {k: v[0] if isinstance(v, list) else v for k, v in app_state.items()}
    return app_state

@st.cache(hash_funcs={"_thread.RLock": lambda _: None}, allow_output_mutation=True)
def generate_presigned_url(object_key, bucket_name='aspect-km', expiry=3600):
    client = boto3.client("s3",region_name='ap-southeast-2',
                          aws_secret_access_key=st.secrets.aws_secret_access_key,
                          aws_access_key_id=st.secrets.aws_access_key_id)
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

if __name__ == "__main__":
    app()
