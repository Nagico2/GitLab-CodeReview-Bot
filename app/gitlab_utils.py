import threading

from flask import jsonify
from retrying import retry

from service.chat_review import review_code_for_mr
from service.gitlab_api import LABEL_DONE, LABEL_FAILED, LABEL_WIP, create_project_labels, get_user_id, set_label_wip
from utils.logger import log


def handle_mr_request(gitlab_payload: dict):
    """
    Handle a merge request event from GitLab
    """
    attr: dict = gitlab_payload.get("object_attributes")
    project_id = attr.get("target_project_id")
    mr_id = attr["iid"]

    # 1. Check reviewer id, draft status, and the mr label
    if (
        get_user_id() not in attr.get("reviewer_ids") or 
        attr.get("draft") or
        (
            LABEL_WIP in attr.get("labels") or
            LABEL_DONE in attr.get("labels") or
            LABEL_FAILED in attr.get("labels")
        )
    ):
        return jsonify({'status': 'success'}), 200

    # 2. Create the project label if necessary
    create_project_labels(project_id)
    set_label_wip(project_id, mr_id)

    log.info("Trigger cr bot handler for mr: ", gitlab_payload)

    thread = threading.Thread(target=review_code_for_mr, args=(project_id, mr_id, gitlab_payload))
    thread.start()

    return jsonify({'status': 'success'}), 200
