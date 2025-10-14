# main.py
from flask import Flask, request
from google.cloud import firestore, storage
import base64, json, os
from datetime import datetime

app = Flask(__name__)

# Resolve project id explicitly (Cloud Run sets GOOGLE_CLOUD_PROJECT)
PROJECT_ID = (
    os.environ.get("GCP_PROJECT")
    or os.environ.get("GOOGLE_CLOUD_PROJECT")
    or "mtl-gcloud-pubsub-example"
)

# Safety: if emulator env is set locally, ignore it in prod
os.environ.pop("FIRESTORE_EMULATOR_HOST", None)

# NEW: specify project AND database="default"
db = firestore.Client(project=PROJECT_ID, database="default")
storage_client = storage.Client(project=PROJECT_ID)


@app.route("/pubsub", methods=["POST"])
def pubsub():
    envelope = request.get_json()
    if not envelope or "message" not in envelope:
        return ("Bad Request", 400)

    msg_data = base64.b64decode(envelope["message"]["data"]).decode("utf-8")
    msg = json.loads(msg_data)
    bucket_name = msg.get("bucket")
    file_name = msg.get("name")

    print(f"📦 Processing file: gs://{bucket_name}/{file_name}")
    metadata = {
        "bucket": bucket_name,
        "file_name": file_name,
        "processed_at": datetime.utcnow().isoformat(),
        "project_used": PROJECT_ID,
    }
    db.collection("tracks").document(file_name).set(metadata)
    print("✅ Saved metadata to Firestore.")
    return ("", 204)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
