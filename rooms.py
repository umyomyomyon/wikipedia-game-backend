from random import randint

from firebase_admin import db

from exceptions import RoomIdDuplicateException, RoomNotExistException, NotInRoomUserException, NotHostException
from conf import MIN_ROOM_ID, MAX_ROOM_ID, RoomStatuses

# roomのデータ構造
# {
#     'isReady': bool,
#     'status': str,
#     'start': str,
#     'goal': str,
#     'users': [],
#     'host': str
# }


def check_room_exists(room_id: int, return_ref=False):
    ref = db.reference(f'{room_id}/')
    if return_ref:
        return bool(ref.get()), ref
    return bool(ref.get())


def create_room_id():
    room_id = None
    is_room_already_exists = False
    retry_count = 0
    while retry_count < 5:
        room_id = randint(MIN_ROOM_ID, MAX_ROOM_ID)
        is_room_already_exists = check_room_exists(room_id)
        if not is_room_already_exists:
            break
        retry_count += 1
    if is_room_already_exists:
        raise RoomIdDuplicateException
    return room_id


def get_room_data(room_id: int):
    db_path = f'{room_id}/'
    ref = db.reference(db_path)
    data = ref.get()
    if data is None:
        raise RoomNotExistException
    return data


def init_room(room_id: int, user_uuid: str, user_name: str):
    ref = db.reference(f'{room_id}/')
    ref.set({
        'isReady': False,
        'status': RoomStatuses.PREPARATION,
        'users': {
            user_uuid: {
                'name': user_name,
                'isDone': False
            }
        },
        'host': user_uuid
    })


def _join_room(room_id: int, user_uuid: str, user_name: str):
    is_room_exists = check_room_exists(room_id)
    if not is_room_exists:
        raise RoomNotExistException
    room_users_ref = db.reference(f'{room_id}/users/')
    current_users = room_users_ref.get()
    room_users_ref.set(current_users | {user_uuid: {'name': user_name, 'isDone': False}})


def change_room_status(room_id: int, user_uuid: str, start=True, force_change=False):
    is_room_exists, room_ref = check_room_exists(room_id, return_ref=True)
    if not is_room_exists:
        raise RoomNotExistException

    if not force_change:
        room_data = get_room_data(room_id)
        is_host = user_uuid == room_data.get('host')
        if not is_host:
            raise NotHostException

    next_status = RoomStatuses.ONGOING if start else RoomStatuses.ENDED
    room_ref.update({
        'status': next_status
    })


def _destroy_room(room_id: int):
    is_exists_room_id, ref = check_room_exists(room_id, return_ref=True)
    if not is_exists_room_id:
        raise RoomNotExistException
    ref.delete()


def setting_article(room_id: int, url: str, is_start: bool):
    is_room_exists = check_room_exists(room_id)
    if not is_room_exists:
        raise RoomNotExistException
    target = 'start' if is_start else 'goal'
    ref = db.reference(f'{room_id}/{target}/')
    ref.set(url)


def change_player_progress(room_id: int, uuid: str, is_done: bool):
    is_room_exists = check_room_exists(room_id)
    if not is_room_exists:
        raise RoomNotExistException
    ref = db.reference(f'{room_id}/users/{uuid}/')
    player_data = ref.get()
    player_data['isDone'] = is_done
    ref.set(player_data)


def get_room_users(room_id: int):
    ref = db.reference(f'{room_id}/users')
    rtdb_users = ref.get()
    return rtdb_users


def is_all_room_users_done(rtdb_users):
    is_done_list = [rtdb_user_data.get('isDone') for rtdb_user_data in rtdb_users.values()]
    return False not in is_done_list
