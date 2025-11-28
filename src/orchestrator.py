import os
import json
import subprocess
import time
from datetime import datetime

PLAN_FILE = "workflow_plan.json"

def get_current_utc_hour():
    return datetime.utcnow().hour

def check_time_trigger(trigger_hours):
    """
    检查当前 UTC 小时是否在配置的列表中
    如果 trigger_hours 为空或 None，返回 None (代表跟随模式)
    """
    if not trigger_hours:
        return None # Follow mode
    
    current_hour = get_current_utc_hour()
    if current_hour in trigger_hours:
        return True
    return False

def get_last_run_id(workflow_file):
    time.sleep(5)
    try:
        cmd = ["gh", "run", "list", "--workflow", workflow_file, "--limit", "1", "--json", "databaseId"]
        result = subprocess.check_output(cmd).decode()
        data = json.loads(result)
        if data: return data[0]['databaseId']
    except: pass
    return None

def run_orchestration():
    if not os.path.exists(PLAN_FILE):
        print(f"❌ 找不到计划表 {PLAN_FILE}")
        exit(1)

    with open(PLAN_FILE, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    current_hour = get_current_utc_hour()
    print(f">>> 指挥官巡逻中... (当前 UTC 时间: {current_hour}:00)")

    chain_active = False 

    is_manual_run = os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"

    if is_manual_run:
        print("💡 检测到手动触发，将忽略时间限制，强制运行所有任务！\n")
        chain_active = True

    for task in plan:
        name = task['name']
        filename = task['filename']
        wait = task.get('wait', False)
        trigger_hours = task.get('trigger_hours', [])

        # --- 核心调度逻辑 ---
        
        # 1. 检查是否是“发令枪”任务 (配置了时间)
        time_check = check_time_trigger(trigger_hours)

        if time_check is True:
            print(f"⏰ 时间匹配 (UTC {current_hour}) -> 激活任务链: {name}")
            chain_active = True
        elif time_check is False:
            if not is_manual_run:
                print(f"zzz 休眠中: {name} (计划运行: UTC {trigger_hours}, 当前: {current_hour})")
                chain_active = False
        # 2. 决定是否运行
        if not chain_active:
            continue

        # 3. 执行任务
        print(f"\n▶ [启动] {name} ({filename})...")
        try:
            subprocess.run(["gh", "workflow", "run", filename], check=True)
        except subprocess.CalledProcessError:
            print(f"❌ 无法触发 {filename}")
            if wait: exit(1)
            continue

        if wait:
            print(f"  -> 等待任务完成...")
            run_id = get_last_run_id(filename)
            if run_id:
                try:
                    subprocess.run(["gh", "run", "watch", str(run_id), "--exit-status"], check=True)
                    print(f"  ✅ {name} 成功完成")
                except:
                    print(f"  ❌ {name} 失败！停止后续流程。")
                    exit(1) # 链条断裂
            else:
                print("  ⚠️ 无法监控状态，继续...")
        else:
            print(f"  -> 已触发 (异步)，继续下一个...")

if __name__ == "__main__":
    run_orchestration()
