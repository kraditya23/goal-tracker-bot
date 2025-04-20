import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# Try to load credentials from FIREBASE_CREDENTIALS env var
cred_json = os.getenv("FIREBASE_CREDENTIALS")

if cred_json:
    # Load from env (Railway or prod)
    cred_dict = json.loads(cred_json)
    cred = credentials.Certificate(cred_dict)
else:
    # Fallback to local file for development
    cred = credentials.Certificate("serviceAccountKey.json")

# Initialize Firebase app only once
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# Create Firestore client
db = firestore.client()