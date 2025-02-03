import json
from retrying import retry

from config.config import maximum_files, api_config, gpt_message
from llm_api.llm_api_interface import LLMApiError
from llm_api.load_api import create_llm_api_instance
from service.gitlab_api import add_comment_to_mr, get_merge_request_changes, set_label_done, set_label_failed
from utils.logger import log

def wait_and_retry(exception):
    return isinstance(exception, LLMApiError)


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
def review_code_for_mr(project_id: int, merge_id: int, gitlab_message: dict):
    """
    code review for gitlab merge request
    """
    project_name = gitlab_message['project']['name']
    # Get the changes of the merge request
    changes = get_merge_request_changes(project_id, merge_id)

    if not changes:
        log.error(
            f"Project name: {project_name}\n"
            f"Get merge_request changes failed ❌, project_id: {project_id} | merge_id: {merge_id} | mr: {gitlab_message}")
        raise Exception(f"Get merge_request changes failed, project_id: {project_id} | merge_id: {merge_id}")
    
    mr_url = gitlab_message['object_attributes']['url']
    branch_from = gitlab_message['object_attributes']['source_branch']
    branch_to = gitlab_message['object_attributes']['target_branch']

    if len(changes) > maximum_files:
        log.error(
            f"Project name: {project_name}\n"
            f"Modify {len(changes)} > {maximum_files} files, do not codereview ⚠️ \n"
            f"Mr url: {mr_url}\n"
            f"From: {branch_from} to: {branch_to}")
        return

    # Get CR from LLM
    review_info = chat_review("", project_id, "", changes, "", "")
    if review_info != "":
        add_comment_to_mr(project_id, merge_id, review_info)
        set_label_done(project_id, merge_id)
        log.info(
            f"Project name: {project_name}\n"
            f"Mr url: {mr_url}\n"
            f"from: {branch_from} to: {branch_to} \n"
            f"Modify files: {len(changes)}\n"
            f"CR status: Success generate ✅")
    else:
        set_label_failed(project_id, merge_id)
        log.error(
            f"Project name: {project_name}\n"
            f"Mr url: {mr_url}\n"
            f"from: {branch_from} to: {branch_to} \n"
            f"Modify files: {len(changes)} \n"
            f"CR status: Failed generate ❌")
