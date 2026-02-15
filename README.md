# Telegram OpenCode Bot

🤖 在 Telegram 中直接调用 OpenCode 执行任务的机器人

## 功能

- 📱 在 Telegram 中发送任务，OpenCode 自动执行
- 🗄️ 支持使用 postgres skill 查询数据库
- 📓 支持写入 Obsidian 笔记
- 🧹 自动清理残留进程，避免资源泄漏

## 环境要求

- Python 3.12+
- OpenCode CLI
- ngrok (可选，用于内网穿透)
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

## 使用

1. 启动机器人
```bash
python3 telegram_opencode_bot.py
```

2. 配置 ngrok (可选)
```bash
ngrok http 8080
```

3. 设置 Telegram Webhook
```bash
curl -X POST "https://api.telegram.org/bot<你的TOKEN>/setWebhook" \
  -d "url=https://你的ngrok地址/webhook"
```

4. 在 Telegram 中发送任务

示例任务:
- "使用 postgres skill 查询 openclaw 数据库中 locations 表的前5条记录"
- "帮我写一个 hello world Python 脚本"
- "查询数据库并写入 obsidian"

## 命令

- `/start` - 开始使用
- `/help` - 帮助信息
- `/new` - 新会话
- `/status` - 运行状态

## 配置

在 `telegram_opencode_bot.py` 中可修改:
- `PORT` - 服务端口 (默认 8080)
- `TOKEN` - Telegram Bot Token

## 注意事项

- 每次执行完成后自动清理残留的 opencode 进程
- 任务执行超时设置为 300 秒
- 使用 shlex 确保命令参数安全

## License

MIT
