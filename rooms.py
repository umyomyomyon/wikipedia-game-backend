from random import randint

from firebase_admin import db

from exceptions import RoomIdDuplicateException, RoomNotExistException, NotHostException, RoomAlreadyClosedException
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


class RoomValidator:
    room_ref = None
    _room_data = None

    def __init__(self, room_id: int):
        room_path = f'{room_id}/'
        self.room_ref = db.reference(room_path)

    def _fetch_room_data(self):
        if self._room_data is None:
            self._room_data = self.room_ref.get()

    def check_room_exists(self):
        self._fetch_room_data()
        is_room_exists = bool(self._room_data)
        if not is_room_exists:
            raise RoomNotExistException

    def check_room_closed(self):
        self._fetch_room_data()
        status = self._room_data.get('status')
        is_room_closed = status == RoomStatuses.ENDED
        if is_room_closed:
            raise RoomAlreadyClosedException

    @property
    def room_data(self):
        self._fetch_room_data()
        return self._room_data


def create_room_id():
    max_retry_count = 5
    room_ids = [randint(MIN_ROOM_ID, MAX_ROOM_ID) for _ in range(max_retry_count)]
    # forループの中でRoomValidatorをインスタンス化しているのは良くないが、ほとんど1度目の処理で終わるので良しとする
    # (2週目、３週目に行くことはほぼ無い)
    for room_id in room_ids:
        try:
            rv = RoomValidator(room_id)
            rv.check_room_exists()
            continue
        except RoomNotExistException:
            return room_id
    raise RoomIdDuplicateException


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
                'isDone': False,
                'isSurrendered': False
            }
        },
        'host': user_uuid
    })


def _join_room(room_id: int, user_uuid: str, user_name: str):
    rv = RoomValidator(room_id)
    rv.check_room_exists()
    rv.check_room_closed()
    room_users_ref = db.reference(f'{room_id}/users/')
    current_users = room_users_ref.get()
    room_users_ref.set(current_users | {user_uuid: {'name': user_name, 'isDone': False, 'isSurrendered': False}})


def change_room_status(room_id: int, user_uuid: str, start=True, force_change=False):
    rv = RoomValidator(room_id)
    rv.check_room_exists()
    room_ref = rv.room_ref

    if not force_change:
        room_data = get_room_data(room_id)
        is_host = user_uuid == room_data.get('host')
        if not is_host:
            raise NotHostException

    next_status = RoomStatuses.ONGOING if start else RoomStatuses.ENDED
    room_ref.update({
        'status': next_status
    })


def _destroy_room(room_id: int, user_uuid: str = None, force_destroy=True):
    if force_destroy:
        # TODO: テスト環境でだけforce_destroyが許可されるようにしたい
        pass
    rv = RoomValidator(room_id)
    rv.check_room_exists()

    if not force_destroy:
        room_data = rv.room_data
        host = room_data.get('host')
        if user_uuid != host:
            raise NotHostException

    ref = rv.room_ref
    ref.delete()


def setting_article(room_id: int, url: str, is_start: bool):
    rv = RoomValidator(room_id)
    rv.check_room_exists()
    target = 'start' if is_start else 'goal'
    ref = db.reference(f'{room_id}/{target}/')
    ref.set(url)


def change_player_progress(room_id: int, uuid: str, is_done: bool, is_surrendered: bool):
    rv = RoomValidator(room_id)
    rv.check_room_exists()
    ref = db.reference(f'{room_id}/users/{uuid}/')
    player_data = ref.get()
    player_data['isDone'] = is_done
    player_data['isSurrendered'] = is_surrendered
    ref.set(player_data)


def get_room_users(room_id: int):
    ref = db.reference(f'{room_id}/users')
    rtdb_users = ref.get()
    return rtdb_users


def is_all_room_users_done(rtdb_users):
    is_done_list = [rtdb_user_data.get('isDone') for rtdb_user_data in rtdb_users.values()]
    return False not in is_done_list
