from math import trunc

from ollama import Client

from llm_api.llm_api_interface import LLMApiInterface, LLMApiError


class LLMApiOllama(LLMApiInterface):

    def __init__(self):
        self.model_name = None
        self.response = None
        self.provider = None
        self.api_base = None
        self.num_ctx = None
        self.proxy = None

    def set_config(self, api_config: dict) -> bool:
        if api_config is None:
            raise ValueError("api_config is None")
        
        self.provider = api_config.get("PROVIDER", "")
        if self.provider != "ollama":
            raise ValueError("The provider must be ollama")
        
        self.model_name = api_config.get("MODEL_NAME", "")

        self.api_base = api_config.get("API_BASE", None)
        self.num_ctx = int(api_config.get("NUM_CTX", "8192"))

        self.proxy = api_config.get("LLM_PROXY", None)

        self.client = Client(
            host=self.api_base,
            proxy=self.proxy
        )

        return True

    def generate_text(self, messages: list) -> bool:
        try:
            self.response = self.client.chat(
                model=self.model_name, 
                messages=messages,
                options={"num_ctx": self.num_ctx}
            )
        except Exception as e:
            raise LLMApiError(e)
        return True

    def get_respond_content(self) -> str:
        return self.response['message']['content']

    def get_respond_tokens(self) -> int:
        return trunc(int(self.response['eval_count']))
