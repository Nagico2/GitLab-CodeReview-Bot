import json
from openai import OpenAIError
from app.gitlab_utils import *
from config.config import gitlab_server_url, gitlab_private_token, api_config
from llm_api.load_api import create_llm_api_instance
from utils.logger import log


# Constants
LABEL_WIP = "CrBot WIP"
LABEL_DONE = "CrBot Done"
LABEL_FAILED = "CrBot Failed"


# Default headers for the requests
headers = {
    "PRIVATE-TOKEN": gitlab_private_token,
}


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


def wait_and_retry(exception):
    return isinstance(exception, OpenAIError)


@retry(retry_on_exception=wait_and_retry, stop_max_attempt_number=3, wait_fixed=60000)
def generate_review_note(change: list[dict]) -> str:
    try:
        content = json.dumps(change, ensure_ascii=False)
        
        messages = [
            {"role": "system",
             "content": gpt_message
             },
            {"role": "user",
             "content": f"以下是一次更改的diff信息，请review这部分代码变更。\n\n{content}",
             },
        ]
        log.debug(f"Send to LLM: {messages}")
        api = create_llm_api_instance()
        api.set_config(api_config)
        api.generate_text(messages)
        response_content = api.get_respond_content().replace('\n\n', '\n')
        total_tokens = api.get_respond_tokens()
        review_note = response_content
        if "</think>" in response_content:
            review_note = response_content.split("</think>")[1].strip()
        log.info(f"review result({total_tokens}): {response_content}")
        return review_note
    except Exception as e:
        log.error(f"GPT error:{e}")
        return ""


def chat_review(commit_index, project_id, commit_id, changes, context_info, merge_comment_details):
    log.info("Start to review the code changes")
    result = generate_review_note(changes)
    return result


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def review_code(project_id, commit_ids, merge_request_id, context):
    """
    code review for gitlab commit
    """
    review_summary = ""
    for index, commit_id in enumerate(commit_ids, start=1):
        url = f'{gitlab_server_url}/api/v4/projects/{project_id}/repository/commits/{commit_id}/diff'
        log.info(f"Start to request gitlab's {url}   ,commit: {commit_id}'s diff content")

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            diff_content = response.json()
            log.debug(f"commit_id: {commit_id} diff_content: {diff_content}")
            review_summary += chat_review(index, project_id, commit_id, diff_content, context, "")

        else:
            log.error(f"Fails to request gitlab's {url}commit, status code: {response.status_code}")
            raise Exception(f"Fails to request gitlab's {url}commit, status code: {response.status_code}")
    add_comment_to_mr(project_id, merge_request_id, review_summary)


@retry(stop_max_attempt_number=3, wait_fixed=2000)
def review_code_for_mr(project_id: int, merge_id: int, gitlab_message: dict):
    """
    code review for gitlab merge request
    """
    project_name = gitlab_message['project']['name']
    # Get the changes of the merge request
    changes = get_merge_request_changes(project_id, merge_id)

    if not changes:
        log.error(
            f"Project name:{project_name}\n"
            f"Get merge_request changes failed ❌, project_id:{project_id} | merge_id{merge_id} | mr:{gitlab_message}")
        raise Exception(f"Get merge_request changes failed, project_id:{project_id} | merge_id{merge_id}")
    
    mr_url = gitlab_message['object_attributes']['url']
    branch_from = gitlab_message['object_attributes']['source_branch']
    branch_to = gitlab_message['object_attributes']['target_branch']

    if len(changes) > maximum_files:
        log.error(
            f"Project name:{project_name}\n"
            f"Modify {len(changes)} > {maximum_files} files, do not codereview ⚠️ \n"
            f"Mr url:{mr_url}\n"
            f"From:{branch_from} to:{branch_to}")
        return

    # Get CR from LLM
    review_info = chat_review("", project_id, "", changes, "", "")
    if review_info != "":
        add_comment_to_mr(project_id, merge_id, review_info)
        set_label_done(project_id, merge_id)
        log.info(
            f"Project name:{project_name}\n"
            f"Mr url:{mr_url}\n"
            f"from:{branch_from} to:{branch_to} \n"
            f"Modify files: {len(changes)}\n"
            f"CR status: Success generate ✅")
    else:
        set_label_failed(project_id, merge_id)
        log.error(
            f"Project name:{project_name}\n"
            f"Mr url:{mr_url}\n"
            f"from:{branch_from} to:{branch_to} \n"
            f"Modify files: {len(changes)} \n"
            f"CR status: Failed generate ❌")
