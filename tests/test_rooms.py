import pytest
from firebase_admin import db

from rooms import (check_room_exists, init_room, _destroy_room, _join_room, setting_article, change_player_progress,
                   change_room_status, is_all_room_users_done, get_room_users)
from exceptions import RoomNotExistException, NotInRoomUserException, NotHostException
from conf import RoomStatuses


#  init_room -> destroy_roomの順番でテストを実行すること
def test_init_room():
    room_id = 12345
    user_uuid = 'test_user_uuid'
    user_name = 'test_user_name'
    expected_data = {
        'isReady': False,
        'status': RoomStatuses.PREPARATION,
        'users': {
            user_uuid: {
                'name': user_name,
                'isDone': False
            }
        },
        'host': user_uuid
    }

    init_room(room_id, user_uuid, user_name)
    db_path = f'{room_id}/'
    ref = db.reference(db_path)
    data = ref.get()
    assert bool(data)
    assert data == expected_data


def test_destroy_room():
    room_id = 12345
    db_path = f'{room_id}/'
    _destroy_room(room_id)
    ref = db.reference(db_path)
    assert not bool(ref.get())


def test_destroy_room_failed():
    with pytest.raises(RoomNotExistException):
        room_id = 22345
        _destroy_room(room_id)


def room_decorator(room_id):
    def _room_decorator(f):
        _room_id = 10000 if room_id is None else room_id
        user_uuid = 'test_user_uuid'
        user_name = 'test_user_name'

        def _wrapper(*args, **kwargs):
            init_room(_room_id, user_uuid, user_name)
            f(*args, **kwargs)
            _destroy_room(_room_id)

        return _wrapper

    return _room_decorator


@room_decorator(10000)
def test_check_room_exists():
    room_id = 10000
    result = check_room_exists(room_id)
    assert result is True


@room_decorator(20000)
def test_join_room():
    room_id = 20000
    user_uuid = 'join_user_uuid'
    user_name = 'join_user_name'
    expected_data = {
        'name': user_name,
        'isDone': False
    }
    _join_room(room_id, user_uuid, user_name)

    ref = db.reference(f'{room_id}/users/{user_uuid}/')
    result = ref.get()
    assert result == expected_data


def test_join_room_failed():
    with pytest.raises(RoomNotExistException):
        room_id = 20001
        user_uuid = 'test_user_uuid'
        user_name = 'test_user_name'
        _join_room(room_id, user_uuid, user_name)


@room_decorator(20002)
def test_start_room():
    room_id = 20002
    user_uuid = 'test_user_uuid'
    change_room_status(room_id, user_uuid, start=True)

    ref = db.reference(f'{room_id}/status/')
    room_status = ref.get()
    assert room_status == RoomStatuses.ONGOING


@room_decorator(20003)
def test_end_room():
    room_id = 20003
    user_uuid = 'test_user_uuid'
    change_room_status(room_id, user_uuid, start=False)

    ref = db.reference(f'{room_id}/status/')
    room_status = ref.get()
    assert room_status == RoomStatuses.ENDED


@room_decorator(20004)
def test_change_room_status_failed_not_host_user_request():
    with pytest.raises(NotHostException):
        room_id = 20004
        not_in_room_user_uuid = 'not'
        change_room_status(room_id, not_in_room_user_uuid, start=True)


@room_decorator(20005)
def test_change_room_status_not_host_user_request_force_change():
    room_id = 20005
    not_in_room_user_uuid = 'not'
    change_room_status(room_id, not_in_room_user_uuid, start=False, force_change=True)

    ref = db.reference(f'{room_id}/status/')
    room_status = ref.get()
    assert room_status == RoomStatuses.ENDED


@room_decorator(30000)
def test_setting_start_article():
    room_id = 30000
    url = 'https://ja.wikipedia.org/wiki/%E3%83%97%E3%83%AD%E3%82%B0%E3%83%A9%E3%83%9F%E3%83%B3%E3%82%B0%E8%A8%80%E8%AA%9E'
    is_start = True
    setting_article(room_id, url, is_start)

    ref = db.reference(f'{room_id}/')
    data = ref.get()
    assert data == {
        'isReady': False,
        'status': RoomStatuses.PREPARATION,
        'users': {
            'test_user_uuid': {
                'name': 'test_user_name',
                'isDone': False
            }
        },
        'host': 'test_user_uuid',
        'start': url
    }


@room_decorator(40000)
def test_setting_goal_article():
    room_id = 40000
    url = 'https://ja.wikipedia.org/wiki/%E3%83%97%E3%83%AD%E3%82%B0%E3%83%A9%E3%83%9F%E3%83%B3%E3%82%B0%E8%A8%80%E8%AA%9E'
    is_start = False
    setting_article(room_id, url, is_start)

    ref = db.reference(f'{room_id}/')
    data = ref.get()
    assert data == {
        'isReady': False,
        'status': RoomStatuses.PREPARATION,
        'users': {
            'test_user_uuid': {
                'name': 'test_user_name',
                'isDone': False
            }
        },
        'host': 'test_user_uuid',
        'goal': url
    }


def test_setting_article_failed():
    with pytest.raises(RoomNotExistException):
        room_id = 33333
        url = 'https://ja.wikipedia.org/wiki/%E3%83%97%E3%83%AD%E3%82%B0%E3%83%A9%E3%83%9F%E3%83%B3%E3%82%B0%E8%A8%80%E8%AA%9E'
        is_start = True
        setting_article(room_id, url, is_start)


@room_decorator(50000)
def test_change_player_progress():
    room_id = 50000
    user_uuid = 'test_user_uuid'
    user_name = 'test_user_name'
    is_done = True
    expected_data = {
        'name': user_name,
        'isDone': True
    }
    change_player_progress(room_id, user_uuid, is_done)

    result = db.reference(f'{room_id}/users/{user_uuid}/').get()
    assert result == expected_data


def test_is_all_room_users_done():
    rtdb_users = {
        'user-uuid1': {
            'name': 'user-name1',
            'isDone': True
        },
        'user-uuid2': {
            'name': 'user-name2',
            'isDone': True
        }
    }
    result = is_all_room_users_done(rtdb_users)
    assert result is True


def test_is_all_room_users_done_include_not_done_users():
    rtdb_users = {
        'user-uuid1': {
            'name': 'user-name1',
            'isDone': True
        },
        'user-uuid2': {
            'name': 'user-name2',
            'isDone': False
        }
    }

    result = is_all_room_users_done(rtdb_users)
    assert result is False


@room_decorator(60000)
def test_get_room_users():
    # TODO: @room_decorator(room_id, call_back)こんなふうに前処理をデコレータ内でできるようにしたい
    room_id = 60000
    user_uuid = 'join_user_uuid'
    user_name = 'join_user_name'
    _join_room(room_id, user_uuid, user_name)

    expected_data = {
        user_uuid: {
            'name': user_name,
            'isDone': False
        },
        'test_user_uuid': {
            'name': 'test_user_name',
            'isDone': False
        }
    }
    rtdb_users = get_room_users(room_id)
    assert rtdb_users == expected_data
