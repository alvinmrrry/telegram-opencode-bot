# Telegram OpenCode Bot

🤖 在 Telegram 中直接调用 OpenCode 执行任务的机器人

## 功能

- 📱 在 Telegram 中发送任务，OpenCode 自动执行
- 🗄️ 支持使用 postgres skill 查询数据库
- 📓 支持写入 Obsidian 笔记
- 🧹 自动清理残留进程，避免资源泄漏
- 🔄 执行失败自动重试 (最多 3 次)
- 🧹 自动清理 OpenCode 快照，释放硬盘空间

## 环境要求

- Python 3.12+
- OpenCode CLI
- ngrok (用于接收 Telegram Webhook)
- Telegram Bot Token

## 安装

1. 克隆项目
```bash
git clone https://github.com/alvinmrrry/telegram-opencode-bot.git
cd telegram-opencode-bot
```

2. 安装依赖
```bash
pip install flask
```

3. 配置 Telegram Bot Token

编辑 `telegram_opencode_bot.py`，修改 TOKEN:
```python
TOKEN = "你的TelegramBotToken"
```

4. 配置环境变量 (可选)

创建 `env.txt` 文件，格式如下:
```json
"GOOGLE_CLIENT_ID": "your-client-id",
"SUPABASE_URL": "https://your-project.supabase.co",
"SUPABASE_SERVICE_KEY": "your-key"
```

## 启动项目

### 方式一: 前台运行 (调试用)
```bash
python3 telegram_opencode_bot.py
```

### 方式二: 后台运行 (推荐)
```bash
nohup python3 telegram_opencode_bot.py > /tmp/telegram_bot.log 2>&1 &
```

### 方式三: 使用脚本一键启动
```bash
# 停止现有进程
pkill -f telegram_opencode_bot.py

# 后台启动
nohup python3 telegram_opencode_bot.py > /tmp/telegram_bot.log 2>&1 &

# 查看启动状态
tail -f /tmp/telegram_bot.log
```

## 配置 ngrok (必需)

Telegram Webhook 需要公网 URL，使用 ngrok 进行内网穿透:

### 1. 安装 ngrok
```bash
# macOS
brew install ngrok

# 或访问 https://ngrok.com/download 下载
```

### 2. 配置 ngrok (首次使用)
```bash
ngrok config add-authtoken YOUR_NGROK_AUTHTOKEN
```

### 3. 启动 ngrok
```bash
# 后台启动 ngrok，暴露 8080 端口
nohup ngrok http 8080 > /tmp/ngrok.log 2>&1 &

# 获取公网 URL
curl -s localhost:4040/api/tunnels | python3 -c "import sys,json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])"
```

### 4. 设置 Telegram Webhook
```bash
# 替换为你的 Bot Token 和 ngrok URL
TOKEN="你的BotToken"
NGROK_URL="https://xxxxx.ngrok-free.app"

curl -X POST "https://api.telegram.org/bot${TOKEN}/setWebhook" \
  -d "url=${NGROK_URL}/webhook"
```

### 5. 验证 Webhook 设置
```bash
curl "https://api.telegram.org/bot${TOKEN}/getWebhookInfo"
```

## 查看日志

### 实时查看日志
```bash
# Bot 日志
tail -f /tmp/telegram_bot.log

# ngrok 日志
tail -f /tmp/ngrok.log
```

### 查看最近日志
```bash
# 最近 50 行
tail -50 /tmp/telegram_bot.log

# 搜索特定内容
grep "错误" /tmp/telegram_bot.log
```

### 查看日志文件位置
- Bot 日志: `/tmp/telegram_bot.log`
- ngrok 日志: `/tmp/ngrok.log`
- OpenCode 日志: `~/.local/share/opencode/log/`

## 停止项目

```bash
# 停止 Bot
pkill -f telegram_opencode_bot.py

# 停止 ngrok
pkill -f ngrok

# 停止所有 opencode 进程
pkill -f 'opencode.*run --format'
```

## 在 Telegram 中发送任务

现在可以在 Telegram 中向你的 Bot 发送任务:

示例任务:
- "使用 postgres skill 查询 openclaw 数据库中 locations 表的前5条记录"
- "帮我写一个 hello world Python 脚本"
- "查询数据库并写入 obsidian"

## Bot 命令

- `/start` - 开始使用
- `/help` - 帮助信息
- `/status` - 查看运行状态
- `/reset` - 重启 Bot

## 配置

在 `telegram_opencode_bot.py` 中可修改:
- `PORT` - 服务端口 (默认 8080)
- `TOKEN` - Telegram Bot Token
- `LOG_FILE` - 日志文件路径

## 注意事项

- **每次执行后自动清理快照**: OpenCode 每次运行会产生约 3GB 快照，Bot 会自动清理
- **无超时限制**: 任务会一直执行直到完成
- **自动重试**: 执行失败会自动重试，最多 3 次
- **ngrok URL 会变化**: 免费版 ngrok 每次重启 URL 会变，需要重新设置 Webhook

## 故障排查

### Bot 不响应消息
1. 检查 Bot 是否运行: `ps aux | grep telegram_opencode_bot`
2. 检查 ngrok 是否运行: `ps aux | grep ngrok`
3. 检查日志: `tail -20 /tmp/telegram_bot.log`
4. 检查 Webhook: `curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"`

### 硬盘空间不足
- 手动清理快照: `rm -rf ~/.local/share/opencode/snapshot/*`
- Bot 会自动清理，但如果异常退出可能需要手动清理

## License

MIT
