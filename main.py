from flask import Flask, jsonify, request
from flask_cors import CORS

from rooms import (create_room_id, init_room, _join_room, setting_article, change_room_status, change_player_progress,
                   get_room_users, is_all_room_users_done)
from firestore import (record_player_progress, cancel_player_progress, record_game_result,
                       delete_all_document_in_collection)
from validation import validate_urls
from exceptions import (RoomNotExistException, RoomIdDuplicateException, URLValidationException, NotInRoomUserException,
                        NotHostException)
from conf import CORS_WHITELIST, fs, logging_client, resource

app = Flask(__name__)
CORS(app, origins=CORS_WHITELIST)
logger = logging_client.logger(__name__)


@app.route('/room', methods=['POST'])
def create_room():
    try:
        room_id = create_room_id()
        data = request.get_json()
        user_uuid, user_name = data['uuid'], data['name']
        init_room(room_id, user_uuid, user_name)
        return jsonify({'room_id': room_id}), 201
    except RoomIdDuplicateException as e:
        return jsonify({'message': e.message}), e.status_code
    except Exception as e:
        logger.log_struct(
            {'error': str(e)},
            resource=resource,
            severity='ERROR'
        )
        return jsonify({'message': 'create_room failed.'}), 400


@app.route('/room/start', methods=['POST'])
def start_room():
    try:
        data = request.get_json()
        user_uuid, room_id = data['uuid'], data['room_id']
        change_room_status(room_id, user_uuid, start=True)
        return jsonify({'message': 'game started.'}), 200
    except RoomNotExistException as e:
        return jsonify({'message': e.message}), e.status_code
    except NotInRoomUserException as e:
        return jsonify({'message': e.message}), e.status_code
    except Exception as e:
        logger.log_struct(
            {'error': str(e)},
            resource=resource,
            severity='ERROR'
        )
        return jsonify({'message': 'game start failed.'}), 400


@app.route('/room/end', methods=['POST'])
def end_room():
    try:
        data = request.get_json()
        user_uuid, room_id = data['uuid'], data['room_id']
        change_room_status(room_id, user_uuid, start=False)
        record_game_result(room_id)
    except NotHostException as e:
        return jsonify({'message': e.message}), e.status_code
    except NotInRoomUserException as e:
        return jsonify({'message': e.message}), e.status_code
    except Exception as e:
        logger.log_struct(
            {'error': str(e)},
            resource=resource,
            severity='ERROR'
        )
        return jsonify({'message': 'end room failed.'}), 400


#
# @app.route('/room', methods=['DELETE'])
# def destroy_room():
#     try:
#         room_id = 11111
#         _destroy_room(room_id)
#         return jsonify({'message': 'room deleted.'}), 204
#     except RoomNotExistException as e:
#         return jsonify({'message': e.message}), e.status_code
#     except Exception as e:
#         return jsonify({'message': 'error'}), 400


@app.route('/room/join', methods=['POST'])
def join_room():
    try:
        data = request.get_json()
        room_id, user_name, user_uuid = data['room_id'], data['name'], data['uuid']
        _join_room(room_id, user_uuid, user_name)
        return jsonify({'room_id': room_id}), 201
    except RoomNotExistException as e:
        return jsonify({'message': e.message}), e.status_code
    except Exception as e:
        logger.log_struct(
            {'error': str(e)},
            resource=resource,
            severity='ERROR'
        )
        return jsonify({'message': 'join room failed.'}), 400


@app.route('/room/articles', methods=['POST'])
def set_article():
    try:
        data = request.get_json()
        room_id, target, url = data['room_id'], data['target'], data['url']
        is_start = True if target == 'start' else False
        setting_article(room_id, url, is_start)
        return jsonify(), 201
    except RoomNotExistException as e:
        return jsonify({'message': e.message}), e.status_code
    except Exception as e:
        logger.log_struct(
            {'error': str(e)},
            resource=resource,
            severity='ERROR'
        )
        return jsonify({'message': 'set_article failed.'}), 400


@app.route('/room/player-progress', methods=['POST'])
def done():
    # required request params: room_id, user_uuid, is_done
    try:
        data = request.get_json()
        room_id, urls, user_uuid, name, is_done \
            = data.get('room_id'), data.get('urls'), data.get('uuid'), data.get('name'), data.get('is_done')
        change_player_progress(room_id, user_uuid, is_done)
        if is_done:
            if not room_id or not urls or not user_uuid or not name:
                raise
            record_player_progress(room_id, user_uuid, name, urls)
            room_users = get_room_users(room_id)
            if is_all_room_users_done(room_users):
                record_game_result(room_id)
                change_room_status(room_id, user_uuid, start=False, force_change=True)
                delete_all_document_in_collection(fs.collection('progress').document(str(room_id)).collection('users'))
        else:
            cancel_player_progress(room_id, user_uuid)
        return jsonify({'message': 'urls is valid.'}), 200
    except RoomNotExistException as e:
        return jsonify({'message': e.message}), e.status_code
    except URLValidationException as e:
        return jsonify({'message': e.message}), e.status_code
    except Exception as e:
        logger.log_struct(
            {'error': str(e)},
            resource=resource,
            severity='ERROR'
        )
        return jsonify({'message': 'validation error.'}), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
