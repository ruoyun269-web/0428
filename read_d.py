import firebase_admin
from firebase_admin import credentials, firestore
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

keyword = input("請輸入姓名關鍵字")
collection_ref = db.collection("靜宜資管")
docs = collection_ref.get()
for doc in docs:
    teacher = doc.to_dict()
    if keyword in teacher["name"]:
        print(teacher)