import os
import json
import subprocess
import time
import sys

PLAN_FILE = "workflow_plan.json"
SUMMARY_FILE = os.getenv("GITHUB_STEP_SUMMARY")

def start_group(title):
    print(f"::group::{title}")
    sys.stdout.flush()

def end_group():
    print("::endgroup::")
    sys.stdout.flush()

def write_summary(content):
    if SUMMARY_FILE:
        with open(SUMMARY_FILE, "a", encoding="utf-8") as f:
            f.write(content + "\n")

def get_latest_run_info(workflow_file):
    time.sleep(5) 
    try:
        cmd = ["gh", "run", "list", "--workflow", workflow_file, "--limit", "1", "--json", "databaseId,url"]
        result = subprocess.check_output(cmd).decode()
        data = json.loads(result)
        if data: return data[0]
    except: pass
    return None

def run_orchestration():
    if not os.path.exists(PLAN_FILE):
        print(f"::error::找不到计划表 {PLAN_FILE}")
        exit(1)

    with open(PLAN_FILE, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    print(f"🚀 收到启动指令，开始执行 {len(plan)} 个任务链...")
    
    write_summary(f"## 🚀 任务执行报告\n")
    write_summary("| 顺序 | 任务名称 | 对应文件 | 模式 |")
    write_summary("|---|---|---|---|")

    for idx, task in enumerate(plan):
        mode = "⏳ 同步等待" if task.get('wait') else "⚡ 异步触发"
        write_summary(f"| {idx+1} | **{task['name']}** | `{task['filename']}` | {mode} |")
    
    write_summary("\n---\n### 📋 详细执行日志")

    for i, task in enumerate(plan):
        name = task['name']
        filename = task['filename']
        wait = task.get('wait', False)

        start_group(f"▶ [{i+1}/{len(plan)}] 正在执行: {name}")
        
        try:
            print(f"命令: gh workflow run {filename}")
            subprocess.run(["gh", "workflow", "run", filename], check=True)
            run_info = get_latest_run_info(filename)
            run_url = run_info['url'] if run_info else "#"
            run_id = run_info['databaseId'] if run_info else None
            
            print(f"🔗 任务已送达: {run_url}")
            write_summary(f"- 🚀 **{name}**: [查看运行详情]({run_url})")

            if wait and run_id:
                print(f"⏳ 模式为同步等待，正在监控运行状态 (ID: {run_id})...")
                subprocess.run(["gh", "run", "watch", str(run_id), "--exit-status"], check=True)
                print(f"✅ {name} 执行成功！")
                write_summary(f"  - ✅ 状态: **执行成功**")
            elif wait:
                print("⚠️ 无法获取 ID，跳过等待...")
            else:
                print(f"⚡ 模式为异步，已触发，立即进行下一步。")
                write_summary(f"  - ⚡ 状态: **后台运行中**")

        except subprocess.CalledProcessError:
            print(f"::error::{name} 执行失败或触发失败！")
            write_summary(f"  - ❌ 状态: **失败** (流程已中断)")
            end_group()
            exit(1)
        
        end_group()

    print("\n🏁 所有计划任务已完成。")

if __name__ == "__main__":
    run_orchestration()
