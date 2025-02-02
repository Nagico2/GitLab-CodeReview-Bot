import requests
from retrying import retry

from config.config import *
from utils.logger import log


# Constants
LABEL_WIP = "CrBot WIP"
LABEL_DONE = "CrBot Done"
LABEL_FAILED = "CrBot Failed"


headers = {"Private-Token": gitlab_private_token}


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
def post_comments(project_id: int, commit_id: int, content: str):
    """
    add comment for gitlab's commits
    :param project_id: gitlab peoject id
    :param commit_id: gitlab commit id
    :param content: comment info
    :return: None
    """
    data = {
        'note': content
    }
    comments_url = f'{gitlab_server_url}/api/v4/projects/{project_id}/repository/commits/{commit_id}/comments'
    response = requests.post(comments_url, headers=headers, json=data)
    log.debug(f"Response: {response.json}")
    if response.status_code == 201:
        comment_data = response.json()
        log.info(f"Succeed to add comment for commit {commit_id}, comment id: {comment_data['id']}")
    else:
        log.error(f"Fails to add comment for commit {commit_id}, status code: {response.status_code}")


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def set_approve(project_id: int, merge_request_id: int):
    """
    Set the merge request to approved
    :param project_id:
    :param merge_request_id:
    :return:
    """
    url = f"{gitlab_server_url}/api/v4/projects/{project_id}/merge_requests/{merge_request_id}/approve"
    response = requests.post(url, headers=headers)
    if response.status_code == 201:
        log.info(f"Succeed to approve merge request {merge_request_id}")
    else:
        log.error(f"Fails to approve merge request {merge_request_id}, status code: {response.status_code}")
        raise Exception(f"Fails to approve merge request {merge_request_id}, status code: {response.status_code}")
    

def set_project_label(project_id: int, merge_request_id: int, add_labels: list[str], remove_labels: list[str]):
    """
    Set the merge request to WIP
    :param project_id:
    :param merge_request_id:
    :return:
    """
    url = f"{gitlab_server_url}/api/v4/projects/{project_id}/merge_requests/{merge_request_id}"
    data = {
        "add_labels": add_labels,
        "remove_labels": remove_labels
    }
    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 200:
        log.info(f"Succeed to set labels for merge request {merge_request_id}")
    else:
        log.error(f"Fails to set labels for merge request {merge_request_id}, status code: {response.status_code}")
        raise Exception(f"Fails to set labels for merge request {merge_request_id}, status code: {response.status_code}")


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def set_label_wip(project_id: int, merge_request_id: int):
    """
    Set the merge request to WIP
    :param project_id:
    :param merge_request_id:
    :return:
    """
    set_project_label(project_id, merge_request_id, [LABEL_WIP], [LABEL_DONE, LABEL_FAILED])


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def set_label_done(project_id: int, merge_request_id: int):
    """
    Set the merge request to Done
    :param project_id:
    :param merge_request_id:
    :return:
    """
    set_project_label(project_id, merge_request_id, [LABEL_DONE], [LABEL_WIP, LABEL_FAILED])


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def set_label_failed(project_id: int, merge_request_id: int):
    """
    Set the merge request to Failed
    :param project_id:
    :param merge_request_id:
    :return:
    """
    set_project_label(project_id, merge_request_id, [LABEL_FAILED], [LABEL_WIP, LABEL_DONE])


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def get_merge_request_changes(project_id, merge_id):
    # URL for the GitLab API endpoint
    url = f"{gitlab_server_url}/api/v4/projects/{project_id}/merge_requests/{merge_id}/changes"

    # Make the GET request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        return response.json()["changes"]
    else:
        return None
