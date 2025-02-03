import json
from os import abort
from flask import Blueprint, request, jsonify
from app.gitlab_utils import handle_mr_request
from config.config import gitlab_webhook_verify_token
from utils.logger import log

git = Blueprint('git', __name__)


@git.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'success'}), 200


@git.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # check verify token if it is set
    if gitlab_webhook_verify_token is not None:
        webhook_token = request.headers.get('X-Gitlab-Token')
        if webhook_token != gitlab_webhook_verify_token:
            return jsonify({'status': 'bad verify token'}), 401

    if request.method == 'GET':
        return jsonify({'status': 'success'}), 200

    elif request.method == 'POST':
        gitlab_payload = request.data.decode('utf-8')
        gitlab_payload = json.loads(gitlab_payload)
        log.debug(f"🌈 : {gitlab_payload}")
        event_type = gitlab_payload.get('object_kind')

        if event_type == 'merge_request':
            # check reviewer id
            return handle_mr_request(gitlab_payload)
        else:
            log.error("Not support event type")
            return jsonify({'status': 'success'}), 200

    else:
        abort(400)
