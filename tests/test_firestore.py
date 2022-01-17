import pytest

from firebase_admin import db

from rooms import setting_article, _destroy_room
from firestore import (delete_all_document_in_collection, record_player_progress, get_all_player_progresses,
                       record_game_result, cancel_player_progress)
from conf import fs


def test_delete_all_document_in_collection():
    collection_ref = fs.collection('test_collection')
    doc_names = ['doc1', 'doc2']
    for doc_name in doc_names:
        doc_ref = collection_ref.document(doc_name)
        doc_ref.set({'key': 'value'})

    delete_all_document_in_collection(collection_ref)

    docs = collection_ref.get()
    assert docs == []


def test_record_player_progress():
    room_id = 98765
    uuid = 'test-user-uuid'
    name = 'test-user-name'
    urls = ['url1', 'url2']
    is_surrendered = False
    record_player_progress(room_id, uuid, name, urls, is_surrendered)

    target_ref = fs.collection('progress').document(str(room_id)).collection('users').document(uuid)
    doc = target_ref.get()
    assert doc.to_dict() == {
        'name': name,
        'urls': urls,
        'isSurrendered': is_surrendered
    }
    target_ref.delete()


def test_cancel_player_progress():
    room_id = 98764
    uuid = 'test-user-uuid'
    name = 'test-user-name'
    urls = ['url1', 'url2']
    is_surrendered = False
    record_player_progress(room_id, uuid, name, urls, is_surrendered)

    cancel_player_progress(room_id, uuid)
    target_ref = fs.collection('progress').document(str(room_id)).collection('users').document(uuid)
    assert target_ref.get().exists is False


def test_get_all_player_progresses():
    # テストデータ作成
    room_id = 88888
    uuid = 'test-user-uuid'
    name = 'test-user-name'
    urls = ['url1', 'url2']
    is_surrendered = False
    record_player_progress(room_id, uuid, name, urls, is_surrendered)

    # surrendered player
    uuid2 = 'test-user-uuid2'
    name2 = 'test-user-name2'
    urls2 = []
    is_surrendered = True
    record_player_progress(room_id, uuid2, name2, urls2, is_surrendered)

    player_progresses = get_all_player_progresses(room_id)
    assert player_progresses == [
        {'uuid': uuid, 'name': name, 'urls': urls, 'isSurrendered': False},
        {'uuid': uuid2, 'name': name2, 'urls': urls2, 'isSurrendered': True},
    ]
    fs.collection('progress').document(str(room_id)).collection('users').document(uuid).delete()
    fs.collection('progress').document(str(room_id)).collection('users').document(uuid2).delete()


def test_record_game_result():
    room_id = 99999
    uuid = 'test-user-uuid'
    name = 'test-user-name'
    urls = ['url1', 'url2']

    # surrendered player
    uuid2 = 'uuid2'
    name2 = 'name2'
    urls2 = []

    # rtdbのデータ準備
    ref = db.reference(f'{room_id}/')
    ref.set({
        'isReady': False,
        'users': {
            uuid: {
                'name': name,
                'isDone': True
            },
            uuid2: {
                'name': name2,
                'isDone': True
            }
        }
    })
    setting_article(room_id, 'start_url', True)
    setting_article(room_id, 'goal_url', False)

    # player progress準備
    record_player_progress(room_id, uuid, name, urls, False)
    record_player_progress(room_id, uuid2, name2, urls2, True)

    record_game_result(room_id)
    result = fs.collection('game-results').document(str(room_id)).get().to_dict()
    assert result.get('start') == 'start_url'
    assert result.get('goal') == 'goal_url'
    assert result.get('results') == [
        {
            'uuid': uuid,
            'name': name,
            'urls': urls,
            'isSurrendered': False
        },
        {
            'uuid': uuid2,
            'name': name2,
            'urls': urls2,
            'isSurrendered': True
        }
    ]

    fs.collection('game-results').document(str(room_id)).delete()
    delete_all_document_in_collection(fs.collection('progress').document(str(room_id)).collection('users'))
    _destroy_room(room_id)
