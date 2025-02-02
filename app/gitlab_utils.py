import threading
from flask import jsonify
import requests
from retrying import retry
from config.config import *
from service.chat_review import review_code_for_mr, LABEL_DONE, LABEL_FAILED, LABEL_WIP, set_label_wip
from utils.logger import log

headers = {"Private-Token": gitlab_private_token}


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def get_merge_request_changes(project_id, merge_id):
    # URL for the GitLab API endpoint
    url = f"{gitlab_server_url}/api/v4/projects/{project_id}/merge_requests/{merge_id}/changes"

    # Headers for the request
    headers = {
        "PRIVATE-TOKEN": gitlab_private_token
    }

    # Make the GET request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        return response.json()["changes"]
    else:
        return None


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def add_comment_to_mr(project_id, merge_request_id, comment):
    """
    Add a comment to a GitLab Merge Request

    :param gitlab_url: Base URL of the GitLab instance
    :param project_id: Project ID
    :param merge_request_id: Merge Request ID
    :param token: GitLab API token
    :param comment: Comment to add
    :return: Response JSON
    """
    headers = {
        "Private-Token": gitlab_private_token,
        "Content-Type": "application/json"
    }

    url = f"{gitlab_server_url}/api/v4/projects/{project_id}/merge_requests/{merge_request_id}/notes"
    data = {
        "body": comment
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        log.info(f"Send comment success: project_id:{project_id}  merge_request_id:{merge_request_id}")
        return response.json()
    else:
        log.error(f"Send comment failed: project_id:{project_id}  merge_request_id:{merge_request_id} response:{response}")
        response.raise_for_status()



@retry(stop_max_attempt_number=3, wait_fixed=2000)
def get_merge_request_comments(project_id, merge_request_iid):
    url = f"{gitlab_server_url}/api/v4/projects/{project_id}/merge_requests/{merge_request_iid}/notes"

    response = requests.get(url, headers=headers)

    comments_content = ""
    if response.status_code == 200:
        comments = response.json()
        for comment in comments:
            author_username = comment['author']['username']
            comment_body = comment['body']
            print(f"Author: {author_username}")
            print(f"Comment: {comment_body}")
            comments_content += comment_body

    else:
        log.error(f"Failed to get comments. Status code: {response.status_code}")
    return comments_content


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def get_commit_change_file(push_info):
    commit_list = push_info['commits']
    added_files_list = []
    modified_files_list = []
    for commit in commit_list:
        added_files = commit.get('added', [])
        modified_files = commit.get('modified', [])
        added_files_list += added_files
        modified_files_list += modified_files

    return added_files_list + modified_files_list


__gitlab_user_id = None

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def get_user_id():
    global __gitlab_user_id
    if __gitlab_user_id:
        return __gitlab_user_id
    url = f"{gitlab_server_url}/api/v4/user"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        user_info = response.json()
        __gitlab_user_id = user_info['id']
        return __gitlab_user_id
    else:
        log.error(f"Falied to get user id. Status code: {response.status_code}")
        raise Exception(f"Falied to get user id. Status code: {response.status_code}")


def get_project_labels(project_id: int) -> list[str]:
    """
    Get the labels of the project
    :param project_id:
    :return:
    """
    url = f"{gitlab_server_url}/api/v4/projects/{project_id}/labels"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return [label["name"] for label in response.json()]
    else:
        log.error(f"Fails to get labels, status code: {response.status_code}")
        raise Exception(f"Fails to get labels, status code: {response.status_code}")


def add_project_label(project_id: int, name: str, color: str):
    """
    Add a label to the project
    :param project_id:
    :param name:
    :param color:
    :return:
    """
    url = f"{gitlab_server_url}/api/v4/projects/{project_id}/labels"
    data = {
        "name": name,
        "color": color
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        log.info(f"Succeed to add label {name}")
    else:
        log.error(f"Fails to add label {name}, status code: {response.status_code}")
        raise Exception(f"Fails to add label {name}, status code: {response.status_code}")



@retry(stop_max_attempt_number=3, wait_fixed=2000)
def create_project_labels(project_id: int):
    """
    Create labels for the project
    :param project_id:
    :return:
    """
    labels = get_project_labels(project_id)
    if LABEL_WIP not in labels:
        add_project_label(project_id, LABEL_WIP, "#eee600")
    if LABEL_DONE not in labels:
        add_project_label(project_id, LABEL_DONE, "#009966")
    if LABEL_FAILED not in labels:
        add_project_label(project_id, LABEL_FAILED, "#dc143c")


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