from google.cloud import storage
import os

# CONFIG
BUCKET_NAME = "face-sync-vishva-2026"
KEY_PATH = "gcp_key.json"


def get_client():
    return storage.Client.from_service_account_json(KEY_PATH)


def upload_file(local_path, blob_name):
    """
    Upload file to GCP bucket.
    local_path: path on your system
    blob_name: name in bucket
    """
    client = get_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)

    blob.upload_from_filename(local_path)
    print(f"Uploaded {local_path} to cloud as {blob_name}")


def download_file(blob_name, local_path):
    """
    Download file from GCP bucket.
    blob_name: name in bucket
    local_path: where to save locally
    """
    client = get_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)

    if not blob.exists():
        print("File does not exist in cloud.")
        return False

    blob.download_to_filename(local_path)
    print(f"Downloaded {blob_name} to {local_path}")
    return True