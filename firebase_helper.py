"""
Firebase Helper — CAT MHI
Handles: Firebase Admin init, ID token verification, Firestore bookmarks.
"""
import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore


@st.cache_resource
def _get_db():
    """Initialize Firebase Admin SDK once and return Firestore client."""
    if not firebase_admin._apps:
        cred_dict = dict(st.secrets["firebase_service_account"])
        # TOML stores \n as literal backslash-n; fix it for the private key
        if "private_key" in cred_dict:
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()


def verify_token(id_token: str) -> dict | None:
    """
    Verify a Firebase ID token.
    Returns decoded claims dict on success, None on failure.
    """
    try:
        _get_db()          # ensure SDK is initialized
        return auth.verify_id_token(id_token)
    except Exception:
        return None


def load_bookmarks(uid: str) -> set:
    """Load user bookmark IDs from Firestore. Returns a set of int IDs."""
    try:
        db  = _get_db()
        doc = db.collection("cat_mhi_bookmarks").document(uid).get()
        if doc.exists:
            return set(doc.to_dict().get("ids", []))
        return set()
    except Exception:
        return set()


def save_bookmarks(uid: str, bookmark_ids: set) -> bool:
    """Persist user bookmark IDs to Firestore. Returns True on success."""
    try:
        db = _get_db()
        db.collection("cat_mhi_bookmarks").document(uid).set(
            {"ids": list(bookmark_ids)}
        )
        return True
    except Exception:
        return False
