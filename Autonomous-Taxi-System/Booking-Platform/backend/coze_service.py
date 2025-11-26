import requests
import json
import re
from typing import Dict, Any

class CozeService:
    def __init__(self):
        self.api_base = "https://api.coze.cn/v3"
        self.token = "pat_HAvxvWrx3fMtrDy9Mgqu8Q37HuxV2Ypl5vcJltF6w6H88UgVaPPQs7Yb0kn72Uoe"
        self.bot_id = "7507952190926241844"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def chat(self, user_id: str, message: str) -> Dict[str, Any]:
        """调用Coze API进行对话"""
        try:
            url = f"{self.api_base}/chat"
            payload = {
                "bot_id": self.bot_id,
                "user_id": user_id,
                "stream": True,
                "additional_messages": [
                    {
                        "content": message,
                        "content_type": "text",
                        "role": "user",
                        "type": "question"
                    }
                ]
            }
            
            print(f"调用Coze API: {url}")
            print(f"请求参数: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=30, stream=True)
            
            print(f"响应状态码: {response.status_code}")
            print(f"DEBUG: 响应头: {response.headers}")
            
            if response.status_code == 200:
                # 处理流式响应
                content_parts = []
                event_lines = []
                data_lines = []
                complete_messages = []
                
                print("DEBUG: 开始处理流式响应")
                line_counter = 0
                
                for line in response.iter_lines():
                    line_counter += 1
                    if not line:
                        print(f"DEBUG: 第{line_counter}行为空，跳过")
                        continue
                        
                    line_str = line.decode('utf-8')
                    print(f"DEBUG [{line_counter}]: 原始数据: {line_str}")
                    
                    # 分类保存event行
                    if line_str.startswith('event:'):
                        event_lines.append(line_str)
                        print(f"DEBUG [{line_counter}]: 事件行: {line_str}")
                        continue
                    
                    # 只处理data行 - 宽松匹配，不要求精确的空格
                    if not line_str.startswith('data:'):
                        print(f"DEBUG [{line_counter}]: 非data行: {line_str}")
                        continue
                        
                    data_lines.append(line_str)
                    
                    # 从data行中提取JSON部分 - 使用正则表达式提取括号内的内容
                    data_str = line_str[5:].strip()  # 去掉 'data:' 前缀并修剪空格
                    print(f"DEBUG [{line_counter}]: data前缀处理后: {data_str}")
                    
                    # 检查是否是结束标记
                    if data_str.strip() == '"[DONE]"':
                        print(f"DEBUG [{line_counter}]: 遇到[DONE]，结束处理")
                        break
                    
                    try:
                        # 提取JSON部分（寻找第一个有效的JSON对象）
                        json_match = re.search(r'({.*?})(?:\s*\S*)?', data_str)
                        if json_match:
                            clean_json = json_match.group(1)
                            print(f"DEBUG [{line_counter}]: 提取的JSON: {clean_json}")
                            data = json.loads(clean_json)
                        else:
                            # 尝试直接解析，如果失败则跳过
                            data = json.loads(data_str)
                            
                        print(f"DEBUG [{line_counter}]: JSON解析成功，类型: {type(data)}")
                        
                        msg_id = data.get('id', 'unknown')
                        msg_type = data.get('type', 'unknown')
                        msg_role = data.get('role', 'unknown')
                        msg_content = data.get('content', '')
                        
                        print(f"DEBUG [{line_counter}]: 消息ID: {msg_id}")
                        print(f"DEBUG [{line_counter}]: 消息类型: {msg_type}")
                        print(f"DEBUG [{line_counter}]: 消息角色: {msg_role}")
                        print(f"DEBUG [{line_counter}]: 消息内容: {msg_content}")
                        
                        # 保存所有类型为answer且角色为assistant的消息
                        if msg_type == 'answer' and msg_role == 'assistant':
                            print(f"DEBUG [{line_counter}]: ✓ 符合条件: type=answer, role=assistant")
                            if not msg_content:
                                print(f"DEBUG [{line_counter}]: ⚠ 内容为空，跳过")
                            else:
                                print(f"DEBUG [{line_counter}]: ✓ 收集内容 (长度:{len(msg_content)}): '{msg_content}'")
                                content_parts.append(msg_content)
                                
                                # 检查是否是completed事件中的完整消息
                                if any('completed' in line for line in event_lines[-3:]):
                                    print(f"DEBUG [{line_counter}]: ✓ 这可能是一个完整消息(近期有completed事件)")
                                    complete_messages.append(msg_content)
                        else:
                            print(f"DEBUG [{line_counter}]: ✗ 不符合条件: type={msg_type}, role={msg_role}")
                            
                    except json.JSONDecodeError as e:
                        print(f"DEBUG [{line_counter}]: JSON解析错误: {e}")
                        print(f"DEBUG [{line_counter}]: 错误数据: {data_str}")
                        continue
                
                print(f"DEBUG: 流式处理结束，总行数: {line_counter}")
                print(f"DEBUG: 总事件行数: {len(event_lines)}")
                print(f"DEBUG: 总数据行数: {len(data_lines)}")
                print(f"DEBUG: content_parts长度: {len(content_parts)}")
                if content_parts:
                    print(f"DEBUG: content_parts内容: {content_parts}")
                    print(f"DEBUG: content_parts各元素长度: {[len(p) for p in content_parts]}")
                
                print(f"DEBUG: complete_messages长度: {len(complete_messages)}")
                if complete_messages:
                    print(f"DEBUG: complete_messages内容: {complete_messages}")
                    print(f"DEBUG: complete_messages各元素长度: {[len(p) for p in complete_messages]}")
                
                print(f"总共收集到 {len(content_parts)} 个内容片段")
                
                # 首先尝试使用complete_messages
                if complete_messages:
                    full_content = max(complete_messages, key=len)
                    print(f"DEBUG: 使用complete_messages中的最长内容: {full_content}")
                    print(f"成功获取回复: {full_content}")
                    return {
                        "success": True,
                        "content": full_content
                    }
                # 然后尝试使用content_parts
                elif content_parts:
                    full_content = max(content_parts, key=len)
                    print(f"DEBUG: 使用content_parts中的最长内容: {full_content}")
                    print(f"成功获取回复: {full_content}")
                    return {
                        "success": True,
                        "content": full_content
                    }
                else:
                    print("DEBUG: 未获取到有效内容")
                    return {
                        "success": False,
                        "error": "未获取到有效回复内容",
                        "content": "抱歉，智能客服暂时无法回复，请稍后再试。"
                    }
            else:
                print(f"DEBUG: HTTP错误: {response.status_code}")
                print(f"DEBUG: 错误响应: {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP请求失败: {response.status_code}",
                    "content": "网络连接异常，请检查网络后重试。"
                }
                
        except requests.exceptions.Timeout:
            print("DEBUG: 请求超时")
            return {
                "success": False,
                "error": "请求超时",
                "content": "网络连接超时，请检查网络后重试。"
            }
        except Exception as e:
            print(f"DEBUG: 调用异常: {str(e)}")
            print(f"DEBUG: 异常类型: {type(e)}")
            import traceback
            print(f"DEBUG: 异常堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"调用异常: {str(e)}",
                "content": "网络连接异常，请检查网络后重试。"
            }

# 全局实例
coze_service = CozeService() 