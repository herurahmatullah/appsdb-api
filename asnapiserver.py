from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import firestore
import os

app = Flask(__name__)
CORS(app)

# Konfigurasi service account dari environment variable (RENDER lebih aman via dashboard)
if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON"):
    import json, tempfile
    sa = os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"]
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tf.write(sa.encode("utf-8"))
    tf.close()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tf.name

db = firestore.Client()

@app.route("/asn", methods=["GET"])
def get_asn():
    # Ambil parameter filter dari query string
    nama = request.args.get('nama', '').strip().lower()
    pangkat = request.args.get('pangkat', '').strip().lower()
    jabatan = request.args.get('jabatan', '').strip().lower()
    unit_kerja = request.args.get('unit_kerja', '').strip().lower()
    nip_baru = request.args.get('nip_baru', '').strip().lower()
    tmt_pangkat = request.args.get('tmt_pangkat', '').strip()
    tmt_jab = request.args.get('tmt_jab', '').strip()
    instansi_induk = request.args.get('instansi_induk', '').strip().lower()

    page_size = int(request.args.get('limit', 10))
    last_doc_id = request.args.get('last_doc_id')

    col = db.collection('asn')
    query = col

    # Filter Firestore yang efisien (untuk exact match saja)
    if pangkat:
        query = query.where("Pang_Gol_Ruang", "==", pangkat)
    if jabatan:
        query = query.where("Jabatan_Terakhir", "==", jabatan)
    if tmt_pangkat:
        query = query.where("TMT_Pangkat", "==", tmt_pangkat)
    if tmt_jab:
        query = query.where("TMT_Jab", "==", tmt_jab)
    if nip_baru:
        query = query.where("NIP_Baru", "==", nip_baru)
    if instansi_induk:
        query = query.where("Instansi_Induk", "==", instansi_induk)

    # Pagination
    query = query.order_by("Nama").limit(page_size)
    if last_doc_id:
        last_doc = col.document(last_doc_id).get()
        if last_doc.exists:
            query = query.start_after(last_doc)

    docs = query.stream()
    data = []
    last_doc_id_value = None
    for doc in docs:
        d = doc.to_dict()
        d['id'] = doc.id
        # Manual filter (contains) di Python
        if nama and nama not in d.get('Nama', '').lower():
            continue
        if unit_kerja and unit_kerja not in d.get('Unit_Kerja', '').lower():
            continue

        item = {
            "id": d.get("id", doc.id),
            "Gelar_Depan": d.get("Gelar_Depan", ""),
            "Nama": d.get("Nama", ""),
            "Gelar_Belakang": d.get("Gelar_Belakang", ""),
            "NIP_Baru": d.get("NIP_Baru", ""),
            "Pang_Gol_Ruang": d.get("Pang_Gol_Ruang", ""),
            "TMT_Pangkat": d.get("TMT_Pangkat", ""),
            "Jabatan_Terakhir": d.get("Jabatan_Terakhir", ""),
            "TMT_Jab": d.get("TMT_Jab", ""),
            "Unit_Kerja": d.get("Unit_Kerja", ""),
            "Instansi_Induk": d.get("Instansi_Induk", "")
        }
        data.append(item)
        last_doc_id_value = doc.id
        if len(data) >= page_size:
            break

    return jsonify({
        'data': data,
        'next_page_id': last_doc_id_value if len(data) == page_size else None
    })

@app.route("/")
def index():
    return "API ASN siap jalan!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
