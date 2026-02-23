#!/usr/bin/env python3
import argparse
import datetime
import os
import sys

STATE_FILE = "STATE.yaml"

try:
    import yaml
except ImportError:
    print("❌ PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


def load_state():
    if not os.path.exists(STATE_FILE):
        print(f"❌ {STATE_FILE} not found")
        sys.exit(1)
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            state, f, allow_unicode=True, default_flow_style=False, sort_keys=False
        )


def update_task(state, task_id, status, blocked_by=None):
    task_found = False
    now = datetime.datetime.now().isoformat() + "Z"

    for task in state.get("tasks", []):
        if task.get("id") == task_id:
            task_found = True
            old_status = task.get("status", "unknown")
            task["status"] = status

            if status == "in_progress":
                task["started"] = now
            elif status == "done":
                task["completed"] = now
                task.pop("blocked_by", None)

                for other in state.get("tasks", []):
                    if other.get("blocked_by") == task_id:
                        other["status"] = "pending"
                        other.pop("blocked_by", None)
                        print(f"🔓 Unblocked: {other['id']}")

            if blocked_by:
                task["blocked_by"] = blocked_by

            print(f"✅ Task '{task_id}': {old_status} → {status}")
            break

    if not task_found:
        print(f"❌ Task '{task_id}' not found in STATE.yaml")
        sys.exit(1)

    state["updated"] = now
    return state


def show_status():
    state = load_state()
    print(f"\n📊 Project: {state.get('project', 'unknown')}")
    print(f"   Updated: {state.get('updated', 'unknown')}")
    print("\nTasks:")
    for task in state.get("tasks", []):
        status_emoji = {
            "pending": "⏳",
            "in_progress": "🔄",
            "done": "✅",
            "blocked": "🚫",
        }.get(task.get("status"), "❓")
        blocked = (
            f" (blocked by: {task.get('blocked_by')})" if task.get("blocked_by") else ""
        )
        print(f"   {status_emoji} {task.get('id')}: {task.get('status')}{blocked}")
        print(f"      Owner: {task.get('owner', 'unassigned')}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Update STATE.yaml task status")
    parser.add_argument("--task", required=True, help="Task ID to update")
    parser.add_argument(
        "--status",
        required=True,
        choices=["pending", "in_progress", "done", "blocked"],
        help="New status",
    )
    parser.add_argument("--blocked-by", help="Task ID that blocks this task")
    parser.add_argument("--show", action="store_true", help="Show current state")

    args = parser.parse_args()

    if args.show:
        show_status()
        return

    state = load_state()
    state = update_task(state, args.task, args.status, args.blocked_by)
    save_state(state)
    print(f"💾 State saved to {STATE_FILE}")


if __name__ == "__main__":
    main()
