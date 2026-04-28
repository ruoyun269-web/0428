import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "林彣媞20260409",
  "mail": "wunti0906@gmail.com",
  "lab": 409
}

collection_ref = db.collection("靜宜資管")
collection_ref.add(doc)