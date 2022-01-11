from typing import List
from datetime import datetime

from firebase_admin import firestore

from rooms import get_room_data
from conf import fs


# データ構造
# room_result: game-results/{room-id}
# {
#     'createdAt': datetime,
#     'endAt': datetime,
#     'start': str,
#     'end': str,
#     'results': [
#         {'uuid': str, 'name': str, 'urls': ['url1', 'url2']},
#         {'uuid': str, 'name': str, 'urls': ['url1', 'url2']}
#     ]
# }
# player-progress: progress/{room-id}/users/{user-uuid}
# {
#     'name': 'user-name',
#     'urls': [
#         'url1',
#         'url2'
#     ]
# }

def delete_all_document_in_collection(collection_ref):
    docs = collection_ref.get()
    for doc in docs:
        doc.reference.delete()


def record_player_progress(room_id: int, uuid: str, name: str, urls: List[str]):
    ref = fs.collection('progress').document(str(room_id)).collection('users').document(uuid)
    ref.set({
        'name': name,
        'urls': urls
    })


def cancel_player_progress(room_id: int, uuid: str):
    ref = fs.collection('progress').document(str(room_id)).collection('users').document(uuid)
    ref.delete()


def get_all_player_progresses(room_id: int):
    ref = fs.collection('progress').document(str(room_id)).collection('users')
    docs = ref.stream()
    progresses = []
    for doc in docs:
        data = doc.to_dict()
        progresses.append({'uuid': doc.id, 'name': data['name'], 'urls': data['urls']})
    return progresses


def record_game_result(room_id: int):
    room_data = get_room_data(room_id)
    start, goal, rtdb_users = room_data.get('start'), room_data.get('goal'), room_data.get('users')
    in_room_user_uuids = [uuid for uuid in rtdb_users.keys()]

    # firestoreのplayer progressを全て取得
    player_progresses = get_all_player_progresses(room_id)
    in_room_player_progresses = [progress for progress in player_progresses if progress['uuid'] in in_room_user_uuids]

    # resultを書き込み
    doc_ref = fs.collection('game-results').document(str(room_id))
    data = {
        'createAt': datetime.now(),
        'start': start,
        'goal': goal,
        'results': in_room_player_progresses
    }
    doc_ref.set(data)
