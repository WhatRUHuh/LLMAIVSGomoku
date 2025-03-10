# llm_interface.py

from abc import ABC, abstractmethod

class LLMInterface(ABC):
    @abstractmethod
    def create_prompt(self, board_state):
        """创建发送给 LLM 的 Prompt"""
        pass

    @abstractmethod
    def get_llm_response_stream(self, prompt): # 修改为 get_llm_response_stream
        """获取 LLM 的流式回复"""
        pass

    @abstractmethod
    def parse_response(self, response_text):
        """解析 LLM 的回复，提取坐标"""
        pass

