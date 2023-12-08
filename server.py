from flask import Flask, request
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

cred = credentials.Certificate('serviceAccountKey.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

@app.route('/update_firestore', methods=['POST'])
def update_firestore():
  data = request.json

  collection_name = data['pills']
  document_name = data['uid']
  document_data = data['data']

  db.collection(collection_name).document(document_name).set(document_data)

  return "Data sent to Firestore", 200



if __name__ == '__main__':
  app.run(debug=True)

@app.route('/get_firestore', methods = ['GET'])
def get_firestore():
  collection_name = request.args.get('pills')
  document_name = request.args.get('uid')

  if not collection_name or not document_name:
    return "Missing collection or document name ", 400

  try:
    doc_ref = db.collection(collection_name).document(document_name)
    doc = doc_ref.get()
    if doc.exists:
      return doc.to_dic(), 200
    else:
      return "Document not found", 404

  except Exception as e:
    return f"an error occured: {str(e)}", 500