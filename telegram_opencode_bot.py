#!/usr/bin/env python3
"""
Telegram Bot with OpenCode Integration

使用方式:
1. 设置环境变量或修改下面的配置
2. 运行: python3 telegram_opencode_bot.py
3. 在 Telegram 中发送消息给机器人
"""

import os
import sys
import json
import time
import signal
import subprocess
import urllib.request
import urllib.error
from flask import Flask, request, Response, jsonify
from threading import Thread
from datetime import datetime

# ============ 配置 ============
TOKEN = "8134791400:AAGP4mWwbiQbDH4HKbNBFQcUUZpfySrQR1c"
PORT = 8080
LOG_FILE = "/tmp/opencode_bot.log"
OPENCODE_MODEL = "opencode/minimax-m2.5-free"
# OPENCODE_MODEL = "opencode/kimi-k2.5-free"    

# 加载环境变量
OPENCODE_ENV = {}
env_file = "/Users/jiancao/env.txt"
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if content:
            import re
            # 解析 key: "value" 格式
            for match in re.finditer(r'"([^"]+)":\s*"([^"]*)"', content):
                key, value = match.groups()
                OPENCODE_ENV[key] = value

def build_prompt(user_text):
    prompt = f"{user_text}，配置文件在 /Users/jiancao/env.txt"
    return prompt

def build_prompt_with_memory(user_text, chat_id):
    """构建带记忆的 prompt"""
    memory = CONVERSATION_MEMORY.get(chat_id, [])
    
    if not memory:
        # 没有记忆，直接使用原始 prompt
        return build_prompt(user_text)
    
    # 构建记忆上下文
    memory_context = "\n\n".join([
        f"上一轮任务: {m['task']}\n上一轮结果: {m['result']}"
        for m in memory[-MEMORY_ROUNDS:]
    ])
    
    prompt = f"{memory_context}\n\n当前任务: {user_text}，配置文件在 /Users/jiancao/env.txt"
    return prompt

def save_to_memory(chat_id, task, result):
    """保存任务和结果到记忆"""
    if chat_id not in CONVERSATION_MEMORY:
        CONVERSATION_MEMORY[chat_id] = []
    
    CONVERSATION_MEMORY[chat_id].append({
        "task": task,
        "result": result
    })
    
    # 保留最近的记忆轮数
    if len(CONVERSATION_MEMORY[chat_id]) > MEMORY_ROUNDS:
        CONVERSATION_MEMORY[chat_id] = CONVERSATION_MEMORY[chat_id][-MEMORY_ROUNDS:]

# ============ 配置 ============
MEMORY_ROUNDS = 0  # 记忆轮数

# ============ Flask App ============
app = Flask(__name__)

# 运行状态
RUNNING_TASKS = {}  # chat_id -> is_running
CONVERSATION_MEMORY = {}  # chat_id -> [{"task": "...", "result": "..."}, ...]

# ============ 日志 ============
def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp} {msg}\n")
    print(f"{timestamp} {msg}")



MAX_MESSAGE_LENGTH = 4000

def clean_text(text):
    """清理文本，移除 markdown 格式"""
    if not text:
        return text
    import re
    # 移除 **bold**, __italic__, `code`
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'```[\s\S]*?```', '', text)
    # 移除 markdown 链接 [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # 移除标题 ### Title -> Title
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # 移除列表符号 - 或 * 开头
    text = re.sub(r'^[\-\*]\s+', '', text, flags=re.MULTILINE)
    # 移除数字列表 1. 2. 开头
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    return text

def split_message(text):
    """将长文本分割成多条消息"""
    if len(text) <= MAX_MESSAGE_LENGTH:
        return [text]
    
    messages = []
    while len(text) > MAX_MESSAGE_LENGTH:
        # 找到最后一个换行符位置，避免在单词中间截断
        split_pos = text[:MAX_MESSAGE_LENGTH].rfind('\n')
        if split_pos == -1:
            split_pos = MAX_MESSAGE_LENGTH
        
        messages.append(text[:split_pos])
        text = text[split_pos:]
    
    if text:
        messages.append(text)
    
    return messages

# ============ Telegram API ============
def send_message(chat_id, text, retry=3):
    # 清理文本
    text = clean_text(text)
    
    # 分割成长消息
    messages = split_message(text)
    
    for msg in messages:
        for attempt in range(retry):
            try:
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": msg
                }
                
                json_data = json.dumps(data)
                log(f"发送数据: {json_data[:200]}")
                
                req = urllib.request.Request(
                    url,
                    data=json_data.encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )
                
                with urllib.request.urlopen(req, timeout=15) as response:
                    result = response.read().decode('utf-8')
                    log(f"发送结果: {result[:200]}")
                
                time.sleep(0.3)
                break
                    
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8') if e.fp else str(e)
                log(f"HTTP错误 {e.code}: {error_body[:300]}")
                if attempt < retry - 1:
                    time.sleep(2)
                else:
                    return None
            except Exception as e:
                log(f"发送消息失败 (尝试 {attempt+1}/{retry}): {e}")
                if attempt < retry - 1:
                    time.sleep(2)
                else:
                    return None
    
    return True

def send_typing(chat_id):
    """发送 typing 状态"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendChatAction"
        data = {"chat_id": chat_id, "action": "typing"}
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req, timeout=5)
    except:
        pass

# ============ OpenCode 执行 ============
def send_update(chat_id, event_type, content, buffer, force_send=False):
    """实时发送更新到 Telegram"""
    if not content:
        return buffer
    
    emoji_map = {
        "thinking": "💭",
        "reasoning": "💭",
        "text": "📝",
        "tool": "🔧",
        "info": "▶️",
        "error": "❌"
    }
    emoji = emoji_map.get(event_type, "📝")
    
    # 累积内容
    if event_type in buffer:
        buffer[event_type] += content
    else:
        buffer[event_type] = content
    
    current = buffer[event_type]
    
    # 内容太长时分段发送
    if len(current) > 1000 or force_send:
        send_message(chat_id, f"{emoji} {current[:1000]}")
        buffer[event_type] = current[1000:] if len(current) > 1000 else ""
    elif force_send and current:
        send_message(chat_id, f"{emoji} {current}")
        buffer[event_type] = ""
    
    return buffer

def run_opencode(prompt, chat_id, original_prompt=None, max_retries=2):
    if original_prompt is None:
        original_prompt = prompt
    
    attempt = 0
    last_error = None
    
    while attempt <= max_retries:
        if attempt > 0:
            log(f"第 {attempt} 次重试: {prompt[:50]}...")
            send_message(chat_id, f"🔄 第 {attempt} 次重试...")
            send_typing(chat_id)
            time.sleep(2)
        else:
            log(f"开始执行: {prompt[:50]}...")
            # 显示任务描述
            display_prompt = original_prompt[:100] + "..." if len(original_prompt) > 100 else original_prompt
            send_message(chat_id, f"🔄 正在执行: {display_prompt}")
            send_typing(chat_id)
        
        import shlex
        safe_prompt = shlex.quote(prompt)
        cmd = f'opencode run --model {OPENCODE_MODEL} --format json -- {safe_prompt}'
        log(f"CMD: {cmd}")
        
        try:
            env = os.environ.copy()
            env.update(OPENCODE_ENV)
            
            # 使用 Popen 实现流式输出
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            
            # 内容缓冲
            content_buffer = {}
            last_update_time = time.time()
            update_interval = 60  # 每 60 秒发送一次保底更新
            first_tool_completed = False  # 跟踪第一个工具调用完成
            
            # 流式读取输出
            while True:
                # 检查进程是否结束
                if process.poll() is not None:
                    # 处理剩余内容
                    for event_type, content in content_buffer.items():
                        if content:
                            if event_type == "thinking":
                                send_message(chat_id, f"💭 {content}")
                            elif event_type == "text":
                                send_message(chat_id, f"📝 {content}")
                            elif event_type == "tool":
                                send_message(chat_id, f"🔧 {content}")
                            elif event_type == "error":
                                send_message(chat_id, f"❌ {content}")
                    break
                
                # 实时读取输出
                line = None
                if process.stdout:
                    line = process.stdout.readline()
                if line:
                    try:
                        event = json.loads(line.strip())
                        event_type = event.get('type', '')
                        part = event.get('part', {})
                        part_type = part.get('type', '')
                        
                        # 处理不同类型的事件
                        # thinking/reasoning
                        if part_type in ['thinking', 'reasoning']:
                            thinking = part.get('text', '')
                            if thinking:
                                content_buffer = send_update(chat_id, "thinking", thinking, content_buffer)
                        
                        # text output
                        elif event_type == "text" or part_type == "text":
                            text = part.get('text', '')
                            if text:
                                content_buffer = send_update(chat_id, "text", text, content_buffer)
                        
                        # tool use
                        elif event_type == "tool_use":
                            tool_name = part.get('tool', '')
                            if tool_name:
                                state = part.get('state', {})
                                status = state.get('status', '')
                                
                                if status == "completed":
                                    if not first_tool_completed:
                                        # 第一个工具完成，跳过显示内容（通常是读取配置）
                                        first_tool_completed = True
                                        content_buffer = send_update(chat_id, "tool", f"🔧 {tool_name} 完成", content_buffer, force_send=True)
                                    else:
                                        # 其他工具调用显示内容
                                        result = state.get('output', '')[:500] if state.get('output') else ''
                                        content_buffer = send_update(chat_id, "tool", f"🔧 {tool_name} 完成\n{result}", content_buffer, force_send=True)
                                else:
                                    content_buffer = send_update(chat_id, "tool", f"🔧 调用 {tool_name}...", content_buffer, force_send=True)
                        
                        # step start
                        elif event_type == "step_start":
                            content_buffer = send_update(chat_id, "info", "▶️ 开始新步骤", content_buffer, force_send=True)
                        
                        # error
                        elif event_type == "error":
                            error = part.get('error', '')
                            if not error:
                                error = event.get('error', {})
                            if error:
                                content_buffer = send_update(chat_id, "error", str(error)[:500], content_buffer, force_send=True)
                        
                        send_typing(chat_id)
                    
                    except json.JSONDecodeError:
                        pass
                
                # 定期发送保底更新
                current_time = time.time()
                if current_time - last_update_time > update_interval:
                    elapsed_minutes = (attempt * 1800 + int(current_time - last_update_time)) // 60
                    
                    # 发送当前缓冲的内容
                    for event_type, content in content_buffer.items():
                        if content:
                            emoji_map = {"thinking": "💭", "text": "📝", "tool": "🔧", "info": "▶️", "error": "❌"}
                            emoji = emoji_map.get(event_type, "📝")
                            send_message(chat_id, f"{emoji} {content[:500]}")
                    
                    content_buffer = {}
                    send_message(chat_id, f"⏳ 仍在运行中... ({elapsed_minutes} 分钟)")
                    send_typing(chat_id)
                    last_update_time = current_time
                
                time.sleep(0.05)
            
            # 等待进程完全结束
            process.wait()
            
            # 清理残留进程
            subprocess.run("pkill -f 'opencode.*run --format'", shell=True, capture_output=True)
            
            full_output = process.stdout.read() if process.stdout else ""
            output_lines = full_output.split('\n') if full_output else []
            log(f"输出长度: {len(full_output)}")
            
            # 解析输出
            final_text = parse_opencode_output(output_lines)
            log(f"解析结果: {len(final_text)}")
            
            # 发送完成消息 (内容已在实时流中发送，简短提示即可)
            if final_text and len(final_text) > 100:
                send_message(chat_id, f"✅ 执行完成\n\n{final_text[:500]}...")
            elif final_text:
                send_message(chat_id, f"✅ 执行完成\n\n{final_text}")
            else:
                send_message(chat_id, "✅ 执行完成")
            
            # 保存到记忆
            save_to_memory(chat_id, original_prompt, final_text if final_text else "")
            
            log(f"执行完成")
            break
            
        except subprocess.TimeoutExpired:
            log(f"执行超时 (尝试 {attempt + 1}/{max_retries + 1})")
            last_error = "执行超时"
            # 清理残留进程
            subprocess.run("pkill -f 'opencode.*run --format'", shell=True, capture_output=True)
            attempt += 1
            if attempt > max_retries:
                send_message(chat_id, "❌ 执行超时，已重试多次")
        except Exception as e:
            log(f"执行错误: {e}")
            last_error = str(e)
            # 清理残留进程
            subprocess.run("pkill -f 'opencode.*run --format'", shell=True, capture_output=True)
            attempt += 1
            if attempt > max_retries:
                send_message(chat_id, f"❌ 错误:\n\n{last_error}")
            else:
                time.sleep(2)
    
    # 清理快照目录
    try:
        snapshot_dir = os.path.expanduser("~/.local/share/opencode/snapshot")
        if os.path.exists(snapshot_dir):
            for item in os.listdir(snapshot_dir):
                item_path = os.path.join(snapshot_dir, item)
                if os.path.isdir(item_path):
                    subprocess.run(["rm", "-rf", item_path], capture_output=True)
            log("已清理快照目录")
    except Exception as e:
        log(f"清理快照失败: {e}")
    
    RUNNING_TASKS[chat_id] = False

def parse_opencode_output(output_lines):
    try:
        texts = []
        for line in output_lines:
            if not line:
                continue
            line_str = line.strip() if isinstance(line, str) else str(line).strip()
            if not line_str:
                continue
            try:
                event = json.loads(line_str)
                event_type = event.get('type', '')
                part = event.get('part', {})
                part_type = part.get('type', '')
                
                # text output
                if event_type == 'text' or part_type == 'text':
                    text = part.get('text', '')
                    if text:
                        texts.append(text)
                
                # step_finish - get final text if available
                elif event_type == 'step_finish':
                    # Check if there's any final content
                    reason = part.get('reason', '')
                    if reason == 'stop':
                        # This is the final step, could contain summary
                        pass
            except (json.JSONDecodeError, TypeError):
                if line_str and not line_str.startswith('{'):
                    texts.append(line_str)
        
        result = ''.join(texts)
        
        # 如果没有 JSON 输出，尝试使用原始行
        if not result.strip():
            result = '\n'.join([l for l in output_lines if l and l.strip() and not l.strip().startswith('{')])
        
        return result.strip()
        
    except Exception as e:
        log(f"解析输出错误: {e}")
        return '\n'.join(str(o) for o in output_lines)

# ============ Webhook 路由 ============
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        
        if not update:
            return Response(status=200)
        
        if 'message' in update:
            msg = update['message']
            chat_id = msg['chat']['id']
            text = msg.get('text', '')
            
            # 去除 @bot_username 前缀
            import re
            text = re.sub(r'^@\S+\s+', '', text)
            
            log(f"收到消息: {text[:30]}... (chat_id: {chat_id})")
            
            # 处理命令
            if text == '/start':
                send_message(chat_id, 
                    "欢迎使用 OpenCode Bot!\n\n"
                    "发送任何任务，我会使用 OpenCode 来执行。\n"
                    "配置文件: /Users/jiancao/env.txt")
                
            elif text == '/help':
                send_message(chat_id,
                    "可用命令:\n"
                    "/start - 欢迎\n"
                    "/help - 帮助\n"
                    "/status - 运行状态\n"
                    "/memory - 查看记忆\n"
                    "/clearmemory - 清除记忆\n"
                    "/reset - 重启 bot")
                
            elif text == '/status':
                if RUNNING_TASKS.get(chat_id):
                    send_message(chat_id, "⏳ 任务运行中...")
                else:
                    send_message(chat_id, "✅ 空闲")
                    
            elif text == '/memory':
                memory = CONVERSATION_MEMORY.get(chat_id, [])
                if not memory:
                    send_message(chat_id, "暂无记忆")
                else:
                    msg = "📋 记忆内容:\n\n"
                    for i, m in enumerate(memory):
                        msg += f"第 {i+1} 轮:\n任务: {m['task'][:100]}...\n结果: {m['result'][:200]}...\n\n"
                    send_message(chat_id, msg)
            
            elif text == '/clearmemory':
                CONVERSATION_MEMORY[chat_id] = []
                send_message(chat_id, "🗑️ 记忆已清除")
                
            elif text == '/reset':
                send_message(chat_id, "🔄 正在重启 bot...")
                def restart_bot():
                    func = request.environ.get('werkzeug.server.shutdown')
                    if func:
                        func()
                    time.sleep(2)
                    subprocess.Popen(
                        ["python3", "/Users/jiancao/telegram_opencode_bot.py"],
                        stdout=open("/tmp/opencode_bot.log", "a"),
                        stderr=subprocess.STDOUT
                    )
                    time.sleep(1)
                    exit(0)
                Thread(target=restart_bot).start()
                    
            elif text.startswith('/'):
                send_message(chat_id, f"未知命令: {text}")
                
            else:
                # 忽略空消息
                if not text or not text.strip():
                    return Response(status=200)
                
                if RUNNING_TASKS.get(chat_id):
                    send_message(chat_id, "⏳ 已有任务在运行，请稍等...")
                else:
                    # 使用带记忆的 prompt
                    prompt = build_prompt_with_memory(text, chat_id)
                    full_prompt = prompt
                    
                    RUNNING_TASKS[chat_id] = True
                    Thread(target=run_opencode, args=(full_prompt, chat_id, text)).start()
                    
    except Exception as e:
        log(f"处理错误: {e}")
    
    return Response(status=200)

@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({"status": "ok"})

# ============ 主程序 ============
if __name__ == "__main__":
    log("=" * 50)
    log("OpenCode Telegram Bot 启动")
    log(f"监听端口: {PORT}")
    log("=" * 50)
    
    # 设置信号处理
    def signal_handler(sig, frame):
        log("收到退出信号，正在关闭...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动 Flask
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
