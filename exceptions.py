class RoomIdDuplicateException(Exception):
    status_code = 400
    message = 'create room id limit.'


class RoomNotExistException(Exception):
    status_code = 404
    message = 'room not exists.'


class URLValidationException(Exception):
    status_code = 400
    message = None

    def __init__(self, parent_url, child_url):
        self.message = f'{child_url}は{parent_url}からたどれません'


class NotInRoomUserException(Exception):
    status_code = 403
    message = '参加中のユーザー以外にこの操作は許可されていません'


class NotHostException(Exception):
    status_code = 403
    message = 'ルームホスト以外にこの操作は許可されていません'
