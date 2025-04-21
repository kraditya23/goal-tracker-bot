import firebase_admin
from firebase_admin import credentials, firestore
import os
import json  # For parsing Firebase credentials from JSON format

## Attempt to load Firebase credentials from the FIREBASE_CREDENTIALS environment variable.
cred_json = os.getenv("FIREBASE_CREDENTIALS")

if cred_json:
    # Load from env (Railway or prod)
    cred_dict = json.loads(cred_json)
    cred = credentials.Certificate(cred_dict)
else:
    # Fallback to local file for development
    cred = credentials.Certificate("serviceAccountKey.json")

## Initialize the Firebase app if it hasn't been initialized already.
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

## Create and expose the Firestore client for database operations.
db = firestore.client()