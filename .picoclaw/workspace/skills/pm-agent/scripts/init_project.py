#!/usr/bin/env python3
import argparse
import datetime
import os
import sys

try:
    import yaml
except ImportError:
    print("❌ PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


def create_state_yaml(project_name, tasks, output_dir="."):
    state = {
        "project": project_name,
        "updated": datetime.datetime.now().isoformat() + "Z",
        "tasks": [],
        "next_actions": [],
    }

    task_owners = {
        "research": "pm-research",
        "illustration": "pm-illustration",
        "layout": "pm-layout",
    }

    for i, task in enumerate(tasks):
        task_id = f"t{i + 1}-{task}"
        owner = task_owners.get(task, "pm-general")
        status = "pending"

        if i > 0:
            prev_task = f"t{i}-{tasks[i - 1]}"
            status = "blocked"
            blocked_by = prev_task
            task_entry = {
                "id": task_id,
                "status": status,
                "blocked_by": blocked_by,
                "owner": owner,
            }
        else:
            task_entry = {"id": task_id, "status": status, "owner": owner}

        state["tasks"].append(task_entry)

    os.makedirs(output_dir, exist_ok=True)
    state_path = os.path.join(output_dir, "STATE.yaml")

    with open(state_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            state, f, allow_unicode=True, default_flow_style=False, sort_keys=False
        )

    print(f"✅ Created {state_path}")
    print(f"\n📋 Tasks:")
    for task in state["tasks"]:
        blocked = (
            f" (blocked by: {task.get('blocked_by')})" if task.get("blocked_by") else ""
        )
        print(f"   - {task['id']}: {task['status']}{blocked} → {task['owner']}")

    return state_path


def create_agents_md(output_dir="."):
    agents_content = """# Project Agents

## CEO (Main Agent)
你是全局统筹者。你的任务是将复杂项目拆解，并通过 `sessions_spawn` 启动子智能体。
- 不写代码，不查资料，不画图
- 只负责拆解任务、更新 STATE.yaml、spawn PMs

工作流：
1. 收到用户需求后，分析需要哪些步骤
2. 编写或更新 STATE.yaml，规划任务 (id, owner, blocked_by)
3. 使用 sessions_spawn 启动 PM 子代理
4. 定期检查状态，调整优先级

## PM-Research
你是研究员。擅长搜索和撰写内容。

工作流：
1. 读取 STATE.yaml，找到分配给你的任务
2. 如果状态是 blocked，等待直到解除
3. 标记为 in_progress
4. 执行研究，保存输出到指定文件
5. 执行 `python update_state.py --task <task-id> --status done`

## PM-Illustration
你是插画师。擅长生成配图。

工作流：
1. 读取 STATE.yaml，找到你的任务
2. 如果 blocked，定期检查直到解除
3. 标记为 in_progress
4. 读取 image_needs.txt 或任务要求
5. 生成图片保存到指定目录
6. 执行 `python update_state.py --task <task-id> --status done`

## PM-Layout
你是排版设计师。擅长整合内容与视觉元素。

工作流：
1. 读取 STATE.yaml，找到你的任务
2. 如果 blocked，定期检查直到解除
3. 标记为 in_progress
4. 读取上游输出（文本 + 图片）
5. 整合排版，输出最终结果
6. 执行 `python update_state.py --task <task-id> --status done`
"""

    agents_path = os.path.join(output_dir, "AGENTS.md")
    with open(agents_path, "w", encoding="utf-8") as f:
        f.write(agents_content)

    print(f"✅ Created {agents_path}")


def create_project_registry(output_dir="."):
    registry_content = """# Active Project Managers

| Label | Project | Task | Status | Spawned |
|-------|---------|------|--------|---------|
"""
    registry_path = os.path.join(output_dir, "PROJECT_REGISTRY.md")
    with open(registry_path, "w", encoding="utf-8") as f:
        f.write(registry_content)

    print(f"✅ Created {registry_path}")


def main():
    parser = argparse.ArgumentParser(description="Initialize PM-Agent project")
    parser.add_argument("project", help="Project name")
    parser.add_argument(
        "--tasks", default="research,illustration,layout", help="Comma-separated tasks"
    )
    parser.add_argument("--path", default=".", help="Output directory")

    args = parser.parse_args()

    tasks = [t.strip() for t in args.tasks.split(",")]

    print(f"🚀 Initializing project: {args.project}")
    print(f"   Tasks: {tasks}")
    print()

    create_state_yaml(args.project, tasks, args.path)
    create_agents_md(args.path)
    create_project_registry(args.path)

    print(f"\n✨ Project ready! Next:")
    print(f"   1. cd {args.path}")
    print(f"   2. Review STATE.yaml and AGENTS.md")
    print(f"   3. Spawn PMs with sessions_spawn")


if __name__ == "__main__":
    main()
