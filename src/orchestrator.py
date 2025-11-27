import os
import json
import subprocess
import time
from datetime import datetime

PLAN_FILE = "workflow_plan.json"

def check_condition(condition):
    """
    根据条件判断今天是否应该运行
    支持: always, daily, weekly (周一), monthly (1号)
    """
    if not condition or condition == "always" or condition == "daily":
        return True
    
    today = datetime.utcnow()
    
    if condition == "weekly":
        # 0 = Monday. 只有周一运行
        return today.weekday() == 0
        
    if condition == "monthly":
        # 只有1号运行
        return today.day == 1
        
    return False

def get_last_run_id(workflow_file):
    """获取指定工作流刚才触发的 Run ID (用于追踪状态)"""
    # 等待几秒让 GitHub 生成记录
    time.sleep(5)
    try:
        # 获取最新的一条正在运行(in_progress)或排队(queued)的记录
        cmd = [
            "gh", "run", "list", 
            "--workflow", workflow_file, 
            "--limit", "1", 
            "--json", "databaseId,status"
        ]
        result = subprocess.check_output(cmd).decode()
        data = json.loads(result)
        if data:
            return data[0]['databaseId']
    except:
        pass
    return None

def run_orchestration():
    if not os.path.exists(PLAN_FILE):
        print(f"❌ 找不到计划表 {PLAN_FILE}")
        exit(1)

    with open(PLAN_FILE, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    print(f">>> 指挥官启动，计划任务数: {len(plan)}")

    for task in plan:
        name = task['name']
        filename = task['filename']
        wait = task.get('wait', False)
        condition = task.get('condition', 'always')

        # 1. 检查时间条件
        if not check_condition(condition):
            print(f"⏭️ [跳过] {name} ({filename}) - 条件不满足 ({condition})")
            continue

        print(f"\n▶ [启动] {name} ({filename})...")

        # 2. 触发工作流
        try:
            # 使用 gh cli 触发
            subprocess.run(["gh", "workflow", "run", filename], check=True)
        except subprocess.CalledProcessError:
            print(f"❌ 触发失败: {filename}，请检查文件名是否正确。")
            # 如果触发都失败了，为了安全起见，停止后续依赖任务
            if wait: 
                print("🛑 因关键任务启动失败，终止后续流程。")
                exit(1)
            continue

        # 3. 如果不需要等待，直接下一个
        if not wait:
            print(f"  -> 已触发 (异步模式)，不等待结果，继续下一个...")
            continue

        # 4. 等待任务完成 (同步模式)
        print(f"  -> 正在等待任务完成...")
        # 获取 Run ID 用于 watch
        run_id = get_last_run_id(filename)
        
        if run_id:
            # 这里的 gh run watch 会一直卡住，直到那边的任务跑完
            # --exit-status 表示：如果那边跑输了，这边也会返回错误码
            try:
                subprocess.run(["gh", "run", "watch", str(run_id), "--exit-status"], check=True)
                print(f"  ✅ {name} 执行成功！")
            except subprocess.CalledProcessError:
                print(f"  ❌ {name} 执行失败！")
                print("🛑 关键任务失败，终止后续流程。")
                exit(1)
        else:
            print("  ⚠️ 无法获取状态，假定已启动，继续...")

if __name__ == "__main__":
    run_orchestration()
