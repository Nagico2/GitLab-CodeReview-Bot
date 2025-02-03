from abc import ABC, abstractmethod


class LLMApiError(Exception):
    def __init__(self, inner: Exception):
        super().__init__(str(inner))
        self.inner = inner

    def __str__(self):
        return f"LLM API error: {self.inner}"


class LLMApiInterface(ABC):

    @abstractmethod
    def set_config(self, api_config: dict) -> bool:
        """设置模型配置"""
        pass

    @abstractmethod
    def generate_text(self, messages: str) -> bool:
        """根据提示生成文本"""
        pass

    @abstractmethod
    def get_respond_content(self) -> str:
        """获取模型返回内容"""
        pass

    @abstractmethod
    def get_respond_tokens(self) -> int:
        """获取模型返回token数"""
        pass