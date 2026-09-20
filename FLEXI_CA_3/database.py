import os
import json
import shutil
import urllib.request
import urllib.error

# Determine file paths for local / serverless fallback
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BUNDLED_FILE = os.path.join(BASE_DIR, "deadlines.json")


def get_data_file_path():
    """Returns a writable path for serverless environments or local storage."""
    if os.getenv("VERCEL"):
        tmp_path = "/tmp/deadlines.json"
        # Seed initial data from bundled deadlines.json if not present
        if not os.path.exists(tmp_path) and os.path.exists(DEFAULT_BUNDLED_FILE):
            try:
                shutil.copyfile(DEFAULT_BUNDLED_FILE, tmp_path)
            except OSError:
                pass
        return tmp_path

    if os.path.exists("deadlines.json"):
        return "deadlines.json"
    return DEFAULT_BUNDLED_FILE


# -------------------------------------------------------------
# UPSTASH REDIS (REST API - Free Serverless KV)
# -------------------------------------------------------------

def _load_from_upstash(url, token):
    try:
        req = urllib.request.Request(
            f"{url.rstrip('/')}/get/deadlines",
            headers={"Authorization": f"Bearer {token}"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read().decode())
            result = res.get("result")
            if result:
                return json.loads(result) if isinstance(result, str) else result
    except Exception as e:
        print("Upstash load error:", e)
    return None


def _save_to_upstash(url, token, data):
    try:
        payload = json.dumps(["SET", "deadlines", json.dumps(data)]).encode()
        req = urllib.request.Request(
            url.rstrip("/"),
            data=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except Exception as e:
        print("Upstash save error:", e)
        return False


# -------------------------------------------------------------
# PUBLIC LOAD / SAVE FUNCTIONS
# -------------------------------------------------------------

def load_deadlines():
    """Loads deadlines from cloud database or local/tmp file."""
    # 1. Check Upstash Redis
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
    upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if upstash_url and upstash_token:
        cloud_data = _load_from_upstash(upstash_url, upstash_token)
        if cloud_data is not None:
            return cloud_data

    # 2. Check MongoDB
    mongo_uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URL")
    if mongo_uri:
        try:
            from pymongo import MongoClient
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
            db = client.get_database("student_tracker")
            docs = list(db.deadlines.find({}, {"_id": 0}))
            if docs:
                return docs
        except Exception as e:
            print("MongoDB load error:", e)

    # 3. File fallback
    file_path = get_data_file_path()
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


def save_deadlines(data):
    """Saves deadlines to cloud database and local/tmp file."""
    # 1. Upstash Redis
    upstash_url = os.getenv("UPSTASH_REDIS_REST_URL")
    upstash_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
    if upstash_url and upstash_token:
        _save_to_upstash(upstash_url, upstash_token, data)

    # 2. MongoDB
    mongo_uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URL")
    if mongo_uri:
        try:
            from pymongo import MongoClient
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
            db = client.get_database("student_tracker")
            db.deadlines.delete_many({})
            if data:
                db.deadlines.insert_many(data)
        except Exception as e:
            print("MongoDB save error:", e)

    # 3. File fallback
    file_path = get_data_file_path()
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    except OSError as e:
        print(f"File save error ({file_path}):", e)