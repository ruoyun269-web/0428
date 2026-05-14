import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate(r"D:\serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "林彣媞",
  "mail": "wunti0906@gmail.com",
  "lab": 854
}

doc_ref = db.collection("靜宜資管2026").document("wunti")
doc_ref.set(doc)
