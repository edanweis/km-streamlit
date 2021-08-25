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

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import s3fs
from google.cloud import secretmanager
from google.oauth2 import service_account

if not firebase_admin._apps:
    # Create credentials object then initialize the firebase admin client
    sec_client = secretmanager.SecretManagerServiceClient()
    name = sec_client.secret_version_path('707318120192', 'firebase-adminsdk', "latest")
    response = sec_client.access_secret_version(name)
    service_account_info = json.loads(response.payload.data.decode('utf-8'))
    # build credentials with the service account dict
    creds = firebase_admin.credentials.Certificate(service_account_info)

    # initialize firebase admin
    firebase_app = firebase_admin.initialize_app(creds)

    db = firestore.client()


@st.cache(suppress_st_warning=True)
def doSuccess():
    placeholder = st.empty()
    with placeholder.container():
    # st.balloons()
        placeholder.success('Ready')
        placeholder.empty()


@st.cache(allow_output_mutation=True, hash_funcs={firebase_admin.App: id})
def db():
    if not firebase_admin._apps:
        # Create credentials object then initialize the firebase admin client
        sec_client = secretmanager.SecretManagerServiceClient()
        name = sec_client.secret_version_path('707318120192', 'firebase-adminsdk', "latest")
        response = sec_client.access_secret_version(name)
        service_account_info = json.loads(response.payload.data.decode('utf-8'))
        # build credentials with the service account dict
        creds = firebase_admin.credentials.Certificate(service_account_info)

        firebase_admin.initialize_app(creds)
    return firestore.client()


@st.cache(hash_funcs={firebase_admin.App: id, s3fs.core.S3File: id})
def firebaseCallback(results, app_state):
    app_state = get_app_state()
    if app_state['s']:
        doc_ref = db().collection(u'streamlit').document(app_state['s'])
        doc_ref.set({
            u'results': results
        }, merge=True)

def get_app_state():
    app_state = st.experimental_get_query_params()
    app_state = {k: v[0] if isinstance(v, list) else v for k, v in app_state.items()}
    return app_state
        

def app():

    app_state = get_app_state()
    firebaseCallback({"test": 'adsf'}, {"s": app_state})

if __name__ == "__main__":
    app()
