---
name: pm-agent
description: Decentralized Project Management with autonomous subagents. CEO pattern - spawn PMs to execute tasks, coordinate via shared STATE.yaml.
metadata:
  clawdbot:
    emoji: "🎯"
    requires:
      bins: ["python3", "git"]
      pip: ["pyyaml"]
---

# pm-agent

Decentralized project management pattern where subagents work autonomously, coordinating through shared STATE.yaml files.

## Quick Start

```bash
# Initialize a new project with tasks
pm-agent init "project-name" --tasks "task1,task2,task3"

# Check current project status
pm-agent status

# List all active PMs
pm-agent list
```

## Architecture

```
User → CEO (Main Agent) → Spawn PMs → Execute & Update STATE.yaml
                                   ↓
                            Shared STATE.yaml
                                   ↓
                    PM-Research ←→ PM-Illustration ←→ PM-Layout
```

## Core Components

### 1. STATE.yaml

The single source of truth for all projects:

```yaml
project: my-project
updated: 2026-02-23T10:00:00Z

tasks:
  - id: t1-research
    status: done
    owner: pm-research
    completed: 2026-02-23T09:00:00Z
    output: "content/draft.md"
    
  - id: t2-illustration
    status: in_progress
    owner: pm-illustration
    started: 2026-02-23T09:30:00Z
    output_dir: "assets/"
    
  - id: t3-layout
    status: pending
    owner: pm-layout
    blocked_by: t2-illustration

next_actions:
  - "pm-illustration: Complete image generation"
  - "pm-layout: Awaiting assets"
```

### 2. AGENTS.md Template

Store in project root with role definitions:

```markdown
# Role: CEO Agent
你是全局统筹者。你的任务是将复杂项目拆解，并通过 spawn 启动子智能体。
工作流：
1. 收到用户需求后，分析需要哪些步骤。
2. 编写或更新 STATE.yaml，规划任务 (id, owner, blocked_by)。
3. 使用 sessions_spawn 启动 PM 子代理。

# Role: PM-Research
你是研究员。擅长搜索和撰写内容。
工作流：
1. 读取 STATE.yaml，找到分配给你的任务。
2. 如果状态是 blocked，等待直到解除。
3. 执行研究，保存输出到指定文件。
4. 执行 python update_state.py --task <task-id> --status done

# Role: PM-Illustration  
你是插画师。擅长生成配图。
工作流：
1. 读取 STATE.yaml，找到你的任务。
2. 读取 image_needs.txt 或任务要求。
3. 生成图片保存到指定目录。
4. 执行 python update_state.py --task <task-id> --status done

# Role: PM-Layout
你是排版设计师。擅长整合内容与视觉元素。
工作流：
1. 读取 STATE.yaml，找到你的任务。
2. 读取上游输出（文本 + 图片）。
3. 整合排版，输出最终结果。
4. 执行 python update_state.py --task <task-id> --status done
```

### 3. PROJECT_REGISTRY.md

Track active PMs:

```markdown
# Active Project Managers

| Label | Project | Task | Status | Spawned |
|-------|---------|------|--------|---------|
| pm-research-001 | japan-tea-history | t1-research | done | 2026-02-23 |
| pm-illustration-001 | japan-tea-history | t2-illustration | in_progress | 2026-02-23 |
| pm-layout-001 | japan-tea-history | t3-layout | pending | 2026-02-23 |
```

## Workflow Example

**User**: "帮我制作一篇《日本茶道历史》的图文并茂的文章"

### Phase 1: CEO Initializes
1. CEO reads AGENTS.md to understand roles
2. Creates STATE.yaml with tasks:
   - t1-research (owner: pm-research)
   - t2-illustration (blocked_by: t1-research)
   - t3-layout (blocked_by: t2-illustration)
3. Spawns subagents:
   - `sessions_spawn(label="pm-research", task="Execute t1-research")`
   - `sessions_spawn(label="pm-illustration", task="Execute t2-illustration")`
   - `sessions_spawn(label="pm-layout", task="Execute t3-layout")`

### Phase 2: PM-Research Executes
1. Reads STATE.yaml → t1-research is pending
2. Sets status to in_progress
3. Searches web, writes content to content/draft.md
4. Extracts 3 image needs to content/image_needs.txt
5. Runs `python update_state.py --task t1-research --status done`
6. Script auto-unblocks t2-illustration

### Phase 3: PM-Illustration Executes
1. Reads STATE.yaml → t2-illustration is now pending
2. Sets status to in_progress
3. Reads content/image_needs.txt
4. Generates images to assets/
5. Runs `python update_state.py --task t2-illustration --status done`
6. Script auto-unblocks t3-layout

### Phase 4: PM-Layout Executes
1. Reads STATE.yaml → t3-layout is pending
2. Sets status to in_progress
3. Reads content/draft.md + assets/
4. Creates final article with embedded images
5. Runs `python update_state.py --task t3-layout --status done`
6. Project complete!

## Commands

### Initialize Project
```bash
pm-agent init <project-name> --tasks "t1,t2,t3" [--path ./project]
```

### Update Task Status
```bash
python update_state.py --task t1-research --status done
python update_state.py --task t2-illustration --status in_progress
python update_state.py --task t3-layout --status blocked --blocked-by t2-illustration
```

### Check Status
```bash
pm-agent status [--project project-name]
```

## Key Insights

- **STATE.yaml > orchestrator**: File-based coordination scales better
- **Auto-unblock magic**: update_state.py automatically releases blocked tasks when dependencies complete
- **Thin main session**: CEO only spawns; PMs do the work
- **Git as audit log**: Commit STATE.yaml changes for full history
- **Human intervention**: Edit files directly, PMs pick up changes on next read

## Based On

Inspired by [Nicholas Carlini's](https://nicholas.carlini.com/) autonomous coding approach - let agents self-organize.
