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

if not firebase_admin._apps:
    # cred = credentials.Certificate('./aspect-km-4e35c3950fe3.json')
    firebase_admin.initialize_app({
          "type": "service_account",
          "project_id": "aspect-km",
          "private_key_id": st.secrets['private_key_id'],
          "private_key": st.secrets['private_key'],
          "client_email": "indd-417@aspect-km.iam.gserviceaccount.com",
          "client_id": "105210967099409135216",
          "auth_uri": "https://accounts.google.com/o/oauth2/auth",
          "token_uri": "https://oauth2.googleapis.com/token",
          "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
          "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/indd-417%40aspect-km.iam.gserviceaccount.com"
        })
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
        cred = credentials.Certificate(st.secrets["googleserviceaccount"])
        firebase_admin.initialize_app({
          "type": "service_account",
          "project_id": "aspect-km",
          "private_key_id": st.secrets['private_key_id'],
          "private_key": st.secrets['private_key'],
          "client_email": "indd-417@aspect-km.iam.gserviceaccount.com",
          "client_id": "105210967099409135216",
          "auth_uri": "https://accounts.google.com/o/oauth2/auth",
          "token_uri": "https://oauth2.googleapis.com/token",
          "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
          "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/indd-417%40aspect-km.iam.gserviceaccount.com"
        })
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
