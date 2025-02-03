import importlib
import warnings

from config.config import llm_api_impl
from llm_api.llm_api_interface import LLMApiInterface


def get_llm_api_class():
    module_name, class_name = llm_api_impl.rsplit('.', 1)
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    return cls


# 使用工厂函数获取类实例
def create_llm_api_instance() -> LLMApiInterface:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        cls = get_llm_api_class()
        return cls()
