import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SRC_ROOT = ROOT / 'src'
sys.path.append(ROOT.as_posix())
sys.path.append(SRC_ROOT.as_posix())

from math import trunc

from ollama import Client

from config.config import api_config as out_config
from llm_api.llm_api_interface import LLMApiInterface
from llm_api.load_api import create_llm_api_instance


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
            raise e
        return True

    def get_respond_content(self) -> str:
        return self.response['message']['content']

    def get_respond_tokens(self) -> int:
        return trunc(int(self.response['eval_count']))


# 示例使用
if __name__ == "__main__":
    api = create_llm_api_instance()
    api.set_config(out_config)
    api.generate_text([
        {"role": "system",
         "content": "你是一位作家"
         },
        {"role": "user",
         "content": "请写一首抒情的诗",
         }
    ])
    print(api.get_respond_content())
    print(api.get_respond_tokens())
