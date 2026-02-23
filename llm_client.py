# llm_client.py
from openai import OpenAI
import streamlit as st

class LLMClient:
    def __init__(self, api_key):

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.gptsapi.net/v1"  # 代理地址
        )

    def chat(self, prompt, model="gpt-4o-mini"):

        try:

            messages = [
                {"role": "system", "content": "你是一个乐于助人的AI助手。如果用户发给你的是一串看似乱码的字符或带有特殊格式的内容，请尝试理解其上下文逻辑进行回答。"},
                {"role": "user", "content": prompt}
            ]

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.1 
            )

            return response.choices[0].message.content

        except Exception as e:

            return f" LLM 调用失败: {str(e)}"