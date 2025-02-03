import os
from math import trunc

from config.config import api_config as out_config
from llm_api.llm_api_interface import LLMApiInterface
from llm_api.load_api import create_llm_api_instance
from unionllm import unionchat


class LLMApiDefault(LLMApiInterface):

    def __init__(self):
        self.model_name = None
        self.response = None
        self.provider = None
        self.api_base = None
        self.num_ctx = None

    def set_config(self, api_config: dict) -> bool:
        if api_config is None:
            raise ValueError("api_config is None")
        for key in api_config:
            if key == "MODEL_NAME":
                self.model_name = api_config[key]
            if key == "PROVIDER":
                self.provider = api_config[key]
            os.environ[key] = api_config[key]
        
        if self.provider == "ollama":
            self.api_base = os.getenv("API_BASE", None)
            self.num_ctx = int(os.getenv("NUM_CTX", "8192"))

        return True

    def generate_text(self, messages: list) -> bool:
        try:
            self.response = unionchat(
                provider=self.provider, 
                model=self.model_name, 
                messages=messages,
                api_base=self.api_base,
                num_ctx=self.num_ctx
            )
        except Exception as e:
            raise e
        return True

    def get_respond_content(self) -> str:
        return self.response['choices'][0]['message']['content']

    def get_respond_tokens(self) -> int:
        return trunc(int(self.response['usage']['total_tokens']))
