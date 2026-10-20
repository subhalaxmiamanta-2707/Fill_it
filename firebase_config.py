import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os
import json

env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)

def init_firebase():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    cert_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY", "serviceAccountKey.json")
    json_env = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    options = {'projectId': os.getenv('FIREBASE_PROJECT_ID', 'fill-it-19a6e')}

    if os.path.exists(cert_path):
        cred = credentials.Certificate(cert_path)
        return firebase_admin.initialize_app(cred, options)
    elif json_env:
        try:
            cert_dict = json.loads(json_env)
            cred = credentials.Certificate(cert_dict)
            return firebase_admin.initialize_app(cred, options)
        except Exception as e:
            print(f"Warning: Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
    
    # Fallback initialization for local dev or when key is omitted
    print("Warning: serviceAccountKey.json not found. Initializing Firebase Admin with application default or unauthenticated fallback.")
    try:
        cred = credentials.ApplicationDefault()
        return firebase_admin.initialize_app(cred, options)
    except Exception:
        # Fallback empty initialization with project ID
        return firebase_admin.initialize_app(options=options)


app = init_firebase()

# Realtime Database Fallback Proxy
class LocalDoc:
    def __init__(self, data=None, doc_id=None):
        self._data = data if data is not None else {}
        self.id = doc_id
        self.exists = bool(self._data)
    
    def to_dict(self):
        return self._data
    
    def get(self):
        return self

    def set(self, data, merge=False):
        if not merge:
            self._data.clear()
        if isinstance(data, dict):
            self._data.update(data)
        self.exists = bool(self._data)
        return self

    def update(self, data):
        if isinstance(data, dict):
            self._data.update(data)
        self.exists = bool(self._data)
        return self


class LocalCollection:
    _store = {}

    def __init__(self, name):
        self.name = name
        if name not in LocalCollection._store:
            LocalCollection._store[name] = {}

    def document(self, doc_id):
        doc_id = str(doc_id).lower()
        if doc_id not in LocalCollection._store[self.name]:
            LocalCollection._store[self.name][doc_id] = {}
        data = LocalCollection._store[self.name][doc_id]
        return LocalDoc(data, doc_id)

class LocalFirestore:
    def collection(self, name):
        return LocalCollection(name)

try:
    db = firestore.client()
except Exception as e:
    print(f"Warning: Could not connect to Firestore client ({e}). Using LocalFirestore fallback.")
    db = LocalFirestore()

# Seed default demo accounts if not already present
try:
    cust_doc = db.collection("Customer").document("demo.customer@fillit.com")
    if not cust_doc.get().exists:
        cust_doc.set({
            "name": "Demo Customer",
            "email": "demo.customer@fillit.com",
            "phone": "9876543210",
            "role": "customer"
        })
    driver_doc = db.collection("Driver").document("demo.driver@fillit.com")
    if not driver_doc.get().exists:
        driver_doc.set({
            "name": "Demo Driver",
            "email": "demo.driver@fillit.com",
            "phone": "9123456789",
            "role": "driver",
            "vehicle_number": "OD-02-DEMO-9999",
            "vehicle_chassis": "CHASSIS-DEMO-12345"
        })
except Exception as seed_err:
    print(f"Demo account seed notice: {seed_err}")

class LocalRTDBRef:
    _root_data = {}

    def __init__(self, path="/", target_child=None, target_value=None):
        self.path = "/" + path.strip("/") if path.strip("/") else "/"
        parts = [p for p in self.path.split("/") if p]
        self.key = parts[-1] if parts else ""
        self._target_child = target_child
        self._target_value = target_value

    def _get_node(self):
        parts = [p for p in self.path.split("/") if p]
        curr = LocalRTDBRef._root_data
        for p in parts:
            if not isinstance(curr, dict) or p not in curr:
                return None
            curr = curr[p]
        return curr

    def _set_node(self, value):
        parts = [p for p in self.path.split("/") if p]
        if not parts:
            LocalRTDBRef._root_data = value
            return
        curr = LocalRTDBRef._root_data
        for p in parts[:-1]:
            if p not in curr or not isinstance(curr[p], dict):
                curr[p] = {}
            curr = curr[p]
        if isinstance(curr, dict):
            curr[parts[-1]] = value

    def get(self):
        node = self._get_node()
        if node is not None:
            if isinstance(node, dict) and self._target_child and self._target_value is not None:
                target_str = str(self._target_value).strip().lower()
                res = {
                    k: v for k, v in node.items() 
                    if isinstance(v, dict) and (
                        v.get(self._target_child) == self._target_value or 
                        str(v.get(self._target_child, '')).strip().lower() == target_str
                    )
                }
                return res
            return node
        return None

    def set(self, value):
        self._set_node(value)

    def push(self, value):
        import uuid
        key = f"-local-{str(uuid.uuid4())[:8]}"
        child_ref = self.child(key)
        child_ref.set(value)
        child_ref.key = key
        return child_ref

    def child(self, child_path):
        new_path = f"{self.path.rstrip('/')}/{child_path.strip('/')}"
        return LocalRTDBRef(new_path, self._target_child, self._target_value)

    def update(self, value):
        if isinstance(value, list):
            value = dict(value)
        node = self._get_node()
        if node is None or not isinstance(node, dict):
            self._set_node(value)
        else:
            if isinstance(value, dict):
                node.update(value)

    def delete(self):
        parts = [p for p in self.path.split("/") if p]
        if not parts:
            LocalRTDBRef._root_data = {}
            return
        curr = LocalRTDBRef._root_data
        for p in parts[:-1]:
            if not isinstance(curr, dict) or p not in curr:
                return
            curr = curr[p]
        if isinstance(curr, dict) and parts[-1] in curr:
            del curr[parts[-1]]

    def order_by_child(self, child_name):
        return LocalRTDBRef(self.path, target_child=child_name, target_value=self._target_value)

    def equal_to(self, value):
        return LocalRTDBRef(self.path, target_child=self._target_child, target_value=value)


DEFAULT_RTDB_URL = 'https://fill-it-19a6e-default-rtdb.asia-southeast1.firebasedatabase.app/'

def get_rtdb_ref(path, url=DEFAULT_RTDB_URL):
    try:
        from firebase_admin import db as rtdb
        return rtdb.reference(path, url=url)
    except Exception as e:
        print(f"Warning: Could not connect to Realtime Database at {path} ({e}). Using LocalRTDBRef fallback.")
        return LocalRTDBRef(path)


