#!/usr/bin/env python3
import argparse
import os
import sys
import time
import yaml

STATE_FILE = "STATE.yaml"
POLL_INTERVAL = 30


def wait_for_task(task_id, timeout=3600):
    if not os.path.exists(STATE_FILE):
        print(f"❌ {STATE_FILE} not found")
        sys.exit(1)

    print(f"⏳ Waiting for task '{task_id}' to be unblocked...")

    elapsed = 0
    while elapsed < timeout:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f)

        for task in state.get("tasks", []):
            if task.get("id") == task_id:
                status = task.get("status")

                if status == "pending":
                    print(f"✅ Task '{task_id}' is now pending! Ready to work.")
                    return True
                elif status == "done":
                    print(f"⚠️ Task '{task_id}' is already done!")
                    return False
                elif status == "blocked":
                    blocker = task.get("blocked_by", "unknown")
                    print(
                        f"🔒 Still blocked by '{blocker}'. Waiting {POLL_INTERVAL}s..."
                    )
                    break
                elif status == "in_progress":
                    print(f"⚠️ Task '{task_id}' is in progress by another agent!")
                    return False

        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

    print(f"⏱️ Timeout after {timeout}s")
    return False


def main():
    parser = argparse.ArgumentParser(description="Wait for task to be unblocked")
    parser.add_argument("--task", required=True, help="Task ID to wait for")
    parser.add_argument("--timeout", type=int, default=3600, help="Timeout in seconds")

    args = parser.parse_args()
    wait_for_task(args.task, args.timeout)


if __name__ == "__main__":
    main()
