import os
import json
import subprocess
import time
import sys
from datetime import datetime

PLAN_FILE = "workflow_plan.json"
SUMMARY_FILE = os.getenv("GITHUB_STEP_SUMMARY")

# --- UI 工具函数 ---

def log_header(message):
    """打印显眼的标题"""
    print(f"\n\033[1;36m{'='*60}\033[0m")
    print(f"\033[1;36m ▶ {message}\033[0m")
    print(f"\033[1;36m{'='*60}\033[0m\n")

def start_group(title):
    """开启日志折叠组"""
    print(f"::group::{title}")
    sys.stdout.flush()

def end_group():
    """结束日志折叠组"""
    print("::endgroup::")
    sys.stdout.flush()

def log_error(message):
    """打印错误并创建 GitHub 注解"""
    print(f"::error::{message}")

def write_summary(content):
    """写入 GitHub Actions摘要页面 (Markdown)"""
    if SUMMARY_FILE:
        with open(SUMMARY_FILE, "a", encoding="utf-8") as f:
            f.write(content + "\n")

# --- 核心逻辑 ---

def get_current_utc_hour():
    return datetime.utcnow().hour

def check_time_trigger(trigger_hours):
    if not trigger_hours:
        return None  # 跟随模式
    return get_current_utc_hour() in trigger_hours

def get_latest_run_info(workflow_file):
    """获取最后一次运行的ID和URL"""
    time.sleep(5) # 等待 GitHub API 刷新
    try:
        cmd = ["gh", "run", "list", "--workflow", workflow_file, "--limit", "1", "--json", "databaseId,url,status,conclusion"]
        result = subprocess.check_output(cmd).decode()
        data = json.loads(result)
        if data:
            return data[0]
    except Exception as e:
        print(f"⚠️ 获取运行信息失败: {e}")
    return None

def generate_plan_dashboard(plan, current_hour, is_manual):
    """在摘要页面生成初始计划表"""
    mode = "🔴 手动强制模式" if is_manual else f"🕒 定时巡逻模式 (UTC {current_hour}:00)"
    
    md_table = f"## 🚀 任务编排控制台\n\n**当前模式:** {mode}\n\n"
    md_table += "| 顺序 | 任务名称 | 文件名 | 计划触发时间 (UTC) | 预判状态 | 下一步 |\n"
    md_table += "|---|---|---|---|---|---|\n"

    chain_active = is_manual
    
    for idx, task in enumerate(plan):
        trigger_hours = task.get('trigger_hours', [])
        time_check = check_time_trigger(trigger_hours)
        
        # 逻辑预判
        status_icon = "⚪ 跳过"
        if is_manual:
            status_icon = "🔵 准备运行"
            chain_active = True
        elif time_check is True:
            status_icon = "🟢 **激活 (时间匹配)**"
            chain_active = True
        elif time_check is False:
            if not chain_active:
                status_icon = "⚪ 休眠"
            else:
                # 之前有任务激活了，但这个任务时间不匹配且不是跟随模式？
                # 逻辑修正：如果上一步激活了，但这步显式写了时间且不匹配，通常应该跳过，
                # 但根据你之前的逻辑，chain_active 一旦开启，后续如果是跟随(空数组)则跑。
                if not trigger_hours:
                    status_icon = "🔵 **跟随运行**"
                else: 
                    status_icon = "⚪ 时间不符"
        elif time_check is None: # 跟随模式
             status_icon = "🔵 **跟随运行**" if chain_active else "⚪ 等待上游"

        next_step = plan[idx+1]['name'] if idx + 1 < len(plan) else "🏁 (结束)"
        hours_str = str(trigger_hours) if trigger_hours else "🔄 跟随上一步"
        
        md_table += f"| {idx+1} | **{task['name']}** | `{task['filename']}` | {hours_str} | {status_icon} | {next_step} |\n"

    write_summary(md_table)
    write_summary("\n---\n### 📋 执行实时日志\n")

def run_orchestration():
    if not os.path.exists(PLAN_FILE):
        log_error(f"找不到计划表 {PLAN_FILE}")
        exit(1)

    with open(PLAN_FILE, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    current_hour = get_current_utc_hour()
    is_manual = os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"

    # 1. 生成可视化预览
    generate_plan_dashboard(plan, current_hour, is_manual)

    chain_active = is_manual
    if is_manual:
        log_header("检测到手动触发，强制执行全流程")

    # 2. 遍历执行
    for i, task in enumerate(plan):
        name = task['name']
        filename = task['filename']
        wait = task.get('wait', False)
        trigger_hours = task.get('trigger_hours', [])
        time_check = check_time_trigger(trigger_hours)

        # 决策逻辑
        should_run = False
        skip_reason = ""

        if is_manual:
            should_run = True
        elif time_check is True:
            should_run = True
            chain_active = True # 激活链条
            log_header(f"时间匹配 (UTC {current_hour}) -> 激活任务链")
        elif time_check is False:
            if not is_manual:
                skip_reason = f"非预定时间 (当前: {current_hour}, 计划: {trigger_hours})"
                should_run = False
        else: # time_check is None (跟随模式)
            if chain_active:
                should_run = True
            else:
                skip_reason = "上游任务未激活"
                should_run = False

        # 如果决定不运行，且链条未断裂（如果是时间不匹配，可能导致后续也不跑）
        # 这里逻辑沿用你之前的：只要 chain_active 没开，就不跑
        if not should_run:
            print(f"💤 任务 [{name}] 已跳过: {skip_reason}")
            continue

        # --- 开始执行任务 ---
        start_group(f"▶ 正在执行: {name}")
        
        print(f"配置文件: {filename}")
        print(f"同步等待: {'是' if wait else '否'}")
        
        try:
            # 触发工作流
            subprocess.run(["gh", "workflow", "run", filename], check=True)
            print(f"🚀 已发送触发信号...")
            
            # 获取运行链接
            run_info = get_latest_run_info(filename)
            run_url = run_info['url'] if run_info else "N/A"
            run_id = run_info['databaseId'] if run_info else None
            
            print(f"🔗 运行详情页: {run_url}")
            
            # 更新摘要
            write_summary(f"- 🚀 **{name}**: 已触发 [查看日志]({run_url})")

            # 如果需要等待
            if wait and run_id:
                print(f"⏳ 正在监控运行状态 (ID: {run_id})...")
                try:
                    subprocess.run(["gh", "run", "watch", str(run_id), "--exit-status"], check=True)
                    print(f"✅ {name} 执行成功！")
                    write_summary(f"  - ✅ 状态: **成功**")
                except subprocess.CalledProcessError:
                    error_msg = f"❌ {name} 执行失败！"
                    log_error(error_msg)
                    write_summary(f"  - ❌ 状态: **失败** (流程终止)")
                    end_group()
                    exit(1) # 终止流程
            elif wait and not run_id:
                print("⚠️ 无法获取 Run ID，无法监控，默认继续...")
            else:
                print(f"⚡ 异步任务，不等待结果，继续下一步...")
                write_summary(f"  - ⚡ 状态: **异步提交** (不追踪结果)")

        except subprocess.CalledProcessError as e:
            log_error(f"❌ 无法触发工作流 {filename}: {str(e)}")
            exit(1)
        
        end_group()
        
        # 预告下一步
        if i + 1 < len(plan):
            next_task = plan[i+1]['name']
            print(f"🔜 准备进入下一步: {next_task}")
        else:
            print("🏁 所有预定任务已完成。")

if __name__ == "__main__":
    run_orchestration()
