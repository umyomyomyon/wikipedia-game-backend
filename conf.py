import os

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import logging_v2

logging_client = logging_v2.Client()
labels = {
    "configuration_name": "wikipedia-game",
    "service_name": "wikipedia-game"
}
resource = logging_v2.resource.Resource(type="cloud_run_revision", labels=labels)

logger = logging_client.logger(__name__)

MIN_ROOM_ID = 10000
MAX_ROOM_ID = 99999
FIREBASE_CRED_PATH = os.getenv('FIREBASE_CRED_PATH')
RTDB_URL = os.getenv('RTDB_URL')

CORS_WHITELIST = [
    'http://localhost:3000'
]

if FIREBASE_CRED_PATH:
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': RTDB_URL
    })
else:
    firebase_admin.initialize_app(options={'databaseURL': RTDB_URL})

fs = firestore.client()


class RoomStatuses:
    PREPARATION = 'PREPARATION'
    ONGOING = 'ONGOING'
    ENDED = 'ENDED'
