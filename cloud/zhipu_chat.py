#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智谱AI对话系统
使用智谱AI的免费LLM API进行对话
"""

import json
import requests
import time
from typing import Dict, List, Optional, Any


class ZhipuChat:
    """智谱AI对话类"""
    
    def __init__(self, api_key: str):
        """
        初始化智谱AI对话
        
        Args:
            api_key: 智谱AI的API密钥
        """
        self.api_key = api_key
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.conversation_history: List[Dict[str, str]] = []
    
    def add_message(self, role: str, content: str):
        """
        添加消息到对话历史
        
        Args:
            role: 角色 ('user', 'assistant', 'system')
            content: 消息内容
        """
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
    
    def chat(self, message: str, model: str = "glm-4-flash", 
             temperature: float = 0.7, max_tokens: int = 1024) -> Optional[str]:
        """
        发送消息并获取回复
        
        Args:
            message: 用户消息
            model: 模型名称，默认使用glm-4-flash (免费模型)
            temperature: 温度参数，控制回复的随机性
            max_tokens: 最大token数
            
        Returns:
            AI的回复内容，如果出错返回None
        """
        # 添加用户消息到历史
        self.add_message("user", message)
        
        # 构建请求数据
        data = {
            "model": model,
            "messages": self.conversation_history,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            # 发送请求
            response = requests.post(
                self.base_url, 
                headers=self.headers, 
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                reply = result["choices"][0]["message"]["content"]
                # 添加AI回复到历史
                self.add_message("assistant", reply)
                return reply
            else:
                print(f"API响应格式异常: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"请求错误: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return None
        except Exception as e:
            print(f"未知错误: {e}")
            return None
    
    def chat_stream(self, message: str, model: str = "glm-4-flash", 
                   temperature: float = 0.7, max_tokens: int = 1024):
        """
        流式对话，实时返回回复内容
        
        Args:
            message: 用户消息
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            流式返回的文本片段
        """
        # 添加用户消息到历史
        self.add_message("user", message)
        
        # 构建请求数据
        data = {
            "model": model,
            "messages": self.conversation_history,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        try:
            # 发送流式请求
            response = requests.post(
                self.base_url, 
                headers=self.headers, 
                json=data,
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            
            full_reply = ""
            
            # 处理流式响应
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]  # 去掉 'data: ' 前缀
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            data_json = json.loads(data_str)
                            if "choices" in data_json and len(data_json["choices"]) > 0:
                                delta = data_json["choices"][0].get("delta", {})
                                if "content" in delta:
                                    content = delta["content"]
                                    full_reply += content
                                    yield content
                        except json.JSONDecodeError:
                            continue
            
            # 添加完整回复到历史
            if full_reply:
                self.add_message("assistant", full_reply)
                
        except requests.exceptions.RequestException as e:
            print(f"流式请求错误: {e}")
        except Exception as e:
            print(f"流式处理错误: {e}")
    
    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history.copy()
    
    def save_history(self, filename: str):
        """保存对话历史到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            print(f"对话历史已保存到: {filename}")
        except Exception as e:
            print(f"保存对话历史失败: {e}")
    
    def load_history(self, filename: str):
        """从文件加载对话历史"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.conversation_history = json.load(f)
            print(f"对话历史已从 {filename} 加载")
        except Exception as e:
            print(f"加载对话历史失败: {e}")


def load_future_self_prompt():
    """加载未来自己的经历内容"""
    try:
        # 尝试读取0_@zlj.txt文件
        file_path = "received_files/0_@zlj.txt"
        with open(file_path, 'r', encoding='utf-16') as f:
            content = f.read().strip()
        return content
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到")
        return None
    except UnicodeDecodeError:
        try:
            # 尝试使用gbk编码
            with open(file_path, 'r', encoding='utd-8') as f:
                content = f.read().strip()
            return content
        except Exception as e:
            print(f"读取文件时出错: {e}")
            return None
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None


def interactive_chat():
    """交互式对话测试函数"""
    print("=== 智谱AI对话测试 ===")

    # 这里需要替换为实际的API密钥
    api_key = "c17166d25b2142e3bde3649d1bd38d97.cixb4bTLpHjFMmH4"  # 请替换为实际的API密钥
    
    if not api_key:
        print("API密钥不能为空！")
        return
    
    # 创建对话实例
    chat = ZhipuChat(api_key)
    
    # 加载未来自己的经历内容
    future_self_content = load_future_self_prompt()
    if future_self_content:
        system_prompt = f"你要扮演未来的我，和现在的我对话，这是你的经历：{future_self_content}"
        chat.add_message("system", system_prompt)
        print("已加载未来自己的经历作为系统提示")
    else:
        # 如果加载失败，允许用户手动输入
        system_prompt = input("请输入系统提示（可选，直接回车跳过）: ").strip()
        if system_prompt:
            chat.add_message("system", system_prompt)
    
    print("\n开始对话！输入 'quit' 退出，输入 'clear' 清空历史，输入 'history' 查看历史")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\n你: ").strip()
            
            if user_input.lower() == 'quit':
                print("再见！")
                break
            elif user_input.lower() == 'clear':
                chat.clear_history()
                print("对话历史已清空")
                continue
            elif user_input.lower() == 'history':
                history = chat.get_history()
                print("\n=== 对话历史 ===")
                for i, msg in enumerate(history):
                    print(f"{i+1}. [{msg['role']}]: {msg['content']}")
                print("=== 历史结束 ===")
                continue
            elif not user_input:
                continue
            
            print("\nAI: ", end="", flush=True)
            
            # 使用流式对话获得更好的体验
            reply_parts = []
            for part in chat.chat_stream(user_input):
                print(part, end="", flush=True)
                reply_parts.append(part)
            
            if not reply_parts:
                # 如果流式失败，尝试普通对话
                reply = chat.chat(user_input)
                if reply:
                    print(reply)
                else:
                    print("抱歉，获取回复失败，请检查网络连接和API密钥")
            
        except KeyboardInterrupt:
            print("\n\n程序被中断，再见！")
            break
        except Exception as e:
            print(f"\n发生错误: {e}")


def simple_test():
    """简单测试函数"""
    print("=== 智谱AI简单测试 ===")
    
    # 这里需要替换为实际的API密钥
    api_key = "c17166d25b2142e3bde3649d1bd38d97.cixb4bTLpHjFMmH4"  # 请替换为实际的API密钥
    
    # if api_key == "your_api_key_here":
    #     print("请先在代码中设置正确的API密钥！")
    #     return
    
    # 创建对话实例
    chat = ZhipuChat(api_key)
    
    # 加载未来自己的经历内容
    future_self_content = load_future_self_prompt()
    if future_self_content:
        system_prompt = f"你要扮演未来的我，和现在的我对话，这是你的经历：{future_self_content}"
        chat.add_message("system", system_prompt)
        print("已加载未来自己的经历作为系统提示")
    
    # 测试对话
    test_messages = [
        "你好，请介绍一下自己",
        "什么是人工智能？",
        "用Python写一个Hello World程序"
    ]
    
    for message in test_messages:
        print(f"\n用户: {message}")
        reply = chat.chat(message)
        if reply:
            print(f"AI: {reply}")
        else:
            print("AI: 回复失败")
        time.sleep(1)  # 避免请求过快


if __name__ == '__main__':
    print("智谱AI对话系统")
    print("1. 交互式对话测试")
    print("2. 简单测试")
    
    choice = input("请选择测试模式 (1/2): ").strip()
    
    if choice == '1':
        interactive_chat()
    elif choice == '2':
        simple_test()
    else:
        print("无效选择，默认运行交互式对话测试")
        interactive_chat()