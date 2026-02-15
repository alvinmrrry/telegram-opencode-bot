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

# ============ Flask App ============
app = Flask(__name__)

# 运行状态
RUNNING_TASKS = {}  # chat_id -> is_running

# ============ 日志 ============
def log(msg):
    """写入日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp} {msg}\n")
    print(f"{timestamp} {msg}")

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
def run_opencode(prompt, chat_id):
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
    """处理 Telegram Webhook"""
    # 必须立即返回 200
    try:
        update = request.get_json()
        
        if not update:
            return Response(status=200)
        
        # 提取消息
        if 'message' in update:
            msg = update['message']
            chat_id = msg['chat']['id']
            text = msg.get('text', '')
            
            log(f"收到消息: {text[:30]}... (chat_id: {chat_id})")
            
            # 处理命令
            if text == '/start':
                send_message(chat_id, 
                    "欢迎使用 OpenCode Bot!\n\n"
                    "发送任何任务，我会使用 OpenCode 来执行。\n\n"
                    "示例:\n"
                    "- 查询数据库\n"
                    "- 创建一个文件\n"
                    "- 帮我写代码")
                    
            elif text == '/help':
                send_message(chat_id,
                    "可用命令:\n"
                    "/start - 欢迎\n"
                    "/help - 帮助\n"
                    "/new - 新会话\n"
                    "/status - 运行状态")
                    
            elif text == '/new':
                send_message(chat_id, "✅ 已开始新会话")
                
            elif text == '/status':
                if RUNNING_TASKS.get(chat_id):
                    send_message(chat_id, "⏳ 任务运行中...")
                else:
                    send_message(chat_id, "✅ 空闲")
                    
            elif text.startswith('/'):
                send_message(chat_id, f"未知命令: {text}")
                
            else:
                # 检查是否已在运行
                if RUNNING_TASKS.get(chat_id):
                    send_message(chat_id, "⏳ 已有任务在运行，请稍等...")
                else:
                    # 开始新任务
                    RUNNING_TASKS[chat_id] = True
                    Thread(target=run_opencode, args=(text, chat_id)).start()
                    
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
