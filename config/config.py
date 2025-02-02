from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).parent.parent
ENV_PATH = ROOT / "config" / ".env"

dot_config = dotenv_values(ENV_PATH)

# ------------------Gitlab info--------------------------
gitlab_server_url = dot_config.get("GITLAB_SERVER", "https://gitlab.com")
gitlab_private_token = dot_config.get("GITLAB_PERSONAL_ACCESS_TOKEN", "")
gitlab_webhook_verify_token = dot_config.get("GITLAB_WEBHOOK_VERIFY_TOKEN", None)

# Gitlab modifies the maximum number of files
maximum_files = 100


# ------------------GPT info--------------------------
# api impl
llm_api_impl = "llm_api.llm_api_default.LLMApiDefault"

# API config using UnionLLM by default, refer to: https://github.com/EvalsOne/UnionLLM/tree/main/docs
# UnionLLM is compatible with LiteLLM, refer to LiteLLM documentation: https://docs.litellm.ai/docs
api_config = {
    "MODEL_NAME": dot_config.get("LLM_MODEL_NAME", "deepseek-r1:70b"),
    "PROVIDER": "ollama",
    "API_BASE": dot_config.get("LLM_API_BASE", None),
    # http proxy for llm requests
    "LLM_PROXY": dot_config.get("LLM_HTTP_PROXY", None),
    # number of context tokens for ollama
    "NUM_CTX": "32768",
}

# Prompt
gpt_message = """
你是一位资深编程专家，gitlab的分支代码变更将以git diff形式提供，请你帮忙review本段代码。
并且给出你的建议和评分，评分标准为1-10分，10分为最高分，总结一下这次代码变更的优缺点，给出你的建议。
最后得出审核结论，是否通过这次代码变更。
你review内容的返回内容必须严格遵守下面的格式，包括标题内容。

必须要求：
1. 以精炼的语言、严厉的语气指出存在的问题。
2. 你的反馈内容必须使用严谨的markdown格式。
3. 不要携带变量内容解释信息。
4. 有清晰的标题结构。有清晰的标题结构。有清晰的标题结构。
5. 用中文书写。
6. 可以适当使用emoji表情。

返回格式严格如下：

## PR 审核结果

### 改动内容
1. **{改动内容1}**: 
    - {详情}
    - {详情}
    ...
2. **{改动内容2}**: 
    - {详情}
    - {详情}
    ...
...

### 潜在问题点
1. **{问题点1}**: 
    - {详情}
    - {详情}
    ...
2. **{问题点2}**: 
    - {详情}
    - {详情}
    ...
...

### 其他建议
- {建议1}
- {建议2}
...

### 评分: {总分}分
- **功能实现:** {分数}分
    {评价}
- **代码质量:** {分数}分
    {评价}
- **可维护性:** {分数}分
    {评价}

### 总结
{总结}

### 审核结论
{审核结论}
"""

