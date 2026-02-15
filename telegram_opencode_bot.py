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

# ============ 意图识别配置 ============
INTENTS = {
    "查数据库": {
        "keywords": ["查数据库", "数据库", "query", "查询", "sql", "locations表"],
        "template": "使用 postgres skill 查询 openclaw 数据库 locations 表的前 {limit} 条记录"
    },
    "写obsidian": {
        "keywords": ["写obsidian", "笔记", "记录", "obsidian", "保存"],
        "template": "使用 obsidian skill 将结果写入 notes/OpenCode 目录的 {note} 笔记"
    },
    "查表": {
        "keywords": ["查看表", "show tables", "表结构"],
        "template": "使用 postgres skill 查询 openclaw 数据库的所有表"
    },
    "写代码": {
        "keywords": ["写代码", "帮我写", "创建文件", "新建文件"],
        "template": "{detail}"
    },
    "解释代码": {
        "keywords": ["解释", "分析", "review", "代码"],
        "template": "分析并解释以下代码: {detail}"
    }
}

INTENT_HINTS = """
💡 常用指令:
• 查数据库 / 数据库 / query → 查询数据库
• 写obsidian / 笔记 → 写入 Obsidian
• 查看表 / show tables → 查看数据库表
• 写代码 / 创建文件 → 写代码
• 解释代码 → 分析代码
"""

# ============ 会话记忆 ============
SESSION_HISTORY = {}  # chat_id -> [{"role": "user/assistant", "content": "..."}]
MAX_HISTORY = 10

# ============ Flask App ============
app = Flask(__name__)

# 运行状态
RUNNING_TASKS = {}  # chat_id -> is_running

# ============ 日志 ============
def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp} {msg}\n")
    print(f"{timestamp} {msg}")

# ============ 意图识别 ============
def detect_intent(text):
    text_lower = text.lower()
    for intent_name, intent_data in INTENTS.items():
        for keyword in intent_data["keywords"]:
            if keyword.lower() in text_lower:
                return intent_name, intent_data["template"]
    return None, None

def build_prompt(user_text):
    intent_name, template = detect_intent(user_text)
    
    if intent_name and template:
        if "{detail}" in template:
            prompt = template.format(detail=user_text)
        elif "{limit}" in template:
            prompt = template.format(limit="5")
        elif "{note}" in template:
            prompt = template.format(note="result")
        else:
            prompt = template
        log(f"意图识别: {intent_name} -> {prompt[:50]}...")
        return prompt
    
    return user_text

# ============ 会话记忆 ============
def add_to_history(chat_id, role, content):
    if chat_id not in SESSION_HISTORY:
        SESSION_HISTORY[chat_id] = []
    
    SESSION_HISTORY[chat_id].append({"role": role, "content": content})
    
    if len(SESSION_HISTORY[chat_id]) > MAX_HISTORY:
        SESSION_HISTORY[chat_id] = SESSION_HISTORY[chat_id][-MAX_HISTORY:]

def get_history_context(chat_id):
    if chat_id not in SESSION_HISTORY:
        return ""
    
    history = SESSION_HISTORY[chat_id]
    if not history:
        return ""
    
    context_parts = []
    for item in history[-5:]:
        role_emoji = "👤" if item["role"] == "user" else "🤖"
        context_parts.append(f"{role_emoji} {item['content'][:100]}")
    
    return "\n".join(context_parts)

def clear_history(chat_id):
    if chat_id in SESSION_HISTORY:
        SESSION_HISTORY[chat_id] = []
        log(f"已清除会话历史: {chat_id}")

# ============ Telegram API ============
def send_message(chat_id, text, retry=3):
    for attempt in range(retry):
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text
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
                return json.loads(result)
                
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
    return None

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
def run_opencode(prompt, chat_id, original_prompt=None):
    if original_prompt is None:
        original_prompt = prompt
    
    log(f"开始执行: {prompt[:50]}...")
    
    send_message(chat_id, f"🔄 正在执行...")
    send_typing(chat_id)
    
    import shlex
    safe_prompt = shlex.quote(prompt)
    cmd = f'opencode run --model opencode/minimax-m2.5-free --format json -- {safe_prompt}'
    log(f"CMD: {cmd}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300,
            env=os.environ.copy()
        )
        
        # 执行完成后清理可能残留的 opencode 进程
        subprocess.run("pkill -f 'opencode.*run --format'", shell=True, capture_output=True)
        
        full_output = result.stdout
        log(f"输出长度: {len(full_output)}")
        
        # 解析输出
        final_text = parse_opencode_output(full_output.split('\n'))
        log(f"解析结果: {len(final_text)}")
        
        # 发送完成消息
        if len(final_text) > 3800:
            send_message(chat_id, f"✅ 完成!\n\n{final_text[:3800]}")
            time.sleep(0.5)
            send_message(chat_id, f"{final_text[3800:]}\n...(过长)")
        else:
            send_message(chat_id, f"✅ 完成!\n\n{final_text}")
        
        add_to_history(chat_id, "assistant", final_text[:500])
        
        log(f"执行完成")
        
    except subprocess.TimeoutExpired:
        log("执行超时")
        send_message(chat_id, "❌ 执行超时")
    except Exception as e:
        log(f"执行错误: {e}")
        send_message(chat_id, f"❌ 错误:\n\n{str(e)}")
    
    finally:
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
                
                if event_type == 'text':
                    text = part.get('text', '')
                    if text:
                        texts.append(text)
                elif event_type == 'text_delta':
                    text = part.get('text', '')
                    if text:
                        texts.append(text)
            except (json.JSONDecodeError, TypeError):
                if line_str:
                    texts.append(line_str)
        
        result = ''.join(texts)
        
        # 如果没有 JSON 输出，尝试使用原始行
        if not result.strip():
            result = '\n'.join([l for l in output_lines if l and l.strip()])
        
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
            
            log(f"收到消息: {text[:30]}... (chat_id: {chat_id})")
            
            # 处理命令
            if text == '/start':
                add_to_history(chat_id, "user", text)
                send_message(chat_id, 
                    "欢迎使用 OpenCode Bot!\n\n"
                    "发送任何任务，我会使用 OpenCode 来执行。\n\n"
                    + INTENT_HINTS)
                    
            elif text == '/help':
                add_to_history(chat_id, "user", text)
                send_message(chat_id,
                    "可用命令:\n"
                    "/start - 欢迎\n"
                    "/help - 帮助\n"
                    "/new - 清除会话记忆\n"
                    "/history - 查看会话历史\n"
                    "/status - 运行状态\n\n"
                    + INTENT_HINTS)
                    
            elif text == '/new':
                clear_history(chat_id)
                send_message(chat_id, "✅ 已清除会话记忆，开始新会话")
                
            elif text == '/history':
                context = get_history_context(chat_id)
                if context:
                    send_message(chat_id, f"📝 会话历史:\n\n{context}")
                else:
                    send_message(chat_id, "暂无会话历史")
                    
            elif text == '/status':
                if RUNNING_TASKS.get(chat_id):
                    send_message(chat_id, "⏳ 任务运行中...")
                else:
                    send_message(chat_id, "✅ 空闲")
                    
            elif text.startswith('/'):
                send_message(chat_id, f"未知命令: {text}")
                
            else:
                if RUNNING_TASKS.get(chat_id):
                    send_message(chat_id, "⏳ 已有任务在运行，请稍等...")
                else:
                    add_to_history(chat_id, "user", text)
                    prompt = build_prompt(text)
                    context = get_history_context(chat_id)
                    
                    if context:
                        full_prompt = f"上下文:\n{context}\n\n当前任务: {prompt}"
                    else:
                        full_prompt = prompt
                    
                    RUNNING_TASKS[chat_id] = True
                    Thread(target=run_opencode, args=(full_prompt, chat_id, prompt)).start()
                    
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
