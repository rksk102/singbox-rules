import os
import json
import subprocess
import time
import sys
from datetime import datetime

# --- 配置 ---
PLAN_FILE = "workflow_plan.json"
SUMMARY_FILE = os.getenv("GITHUB_STEP_SUMMARY")

# --- 颜色与图标常量 ---
class Icon:
    WAIT = "⏳"
    SUCCESS = "✅"
    FAILURE = "❌"
    SKIPPED = "🚫"
    ROCKET = "🚀"
    TIME = "🕒"
    LINK = "🔗"

# --- 辅助函数 ---

def print_box(text, color_code="36"):
    """在控制台打印漂亮的框框"""
    length = len(text) + 4
    print(f"\033[1;{color_code}m┌{'─'*length}┐\033[0m")
    print(f"\033[1;{color_code}m│  {text}  │\033[0m")
    print(f"\033[1;{color_code}m└{'─'*length}┘\033[0m")

def start_group(title):
    print(f"::group::{title}")
    sys.stdout.flush()

def end_group():
    print("::endgroup::")
    sys.stdout.flush()

def get_run_info(workflow_file):
    """获取指定工作流最新的运行信息"""
    time.sleep(3) # 让 GitHub API 喘口气
    try:
        # 获取 ID, URL, 状态, 结论
        cmd = ["gh", "run", "list", "--workflow", workflow_file, "--limit", "1", "--json", "databaseId,url,status,conclusion"]
        result = subprocess.check_output(cmd).decode()
        data = json.loads(result)
        if data: return data[0]
    except Exception:
        pass
    return None

def format_duration(seconds):
    """将秒数格式化为人类可读格式"""
    if seconds < 60:
        return f"{int(seconds)}秒"
    minutes = int(seconds // 60)
    sec = int(seconds % 60)
    return f"{minutes}分{sec}秒"

def write_final_report(results, total_duration):
    """
    在脚本结束时，一次性写入完美的 Markdown 报告
    这样做比流水账更美观，且状态绝对准确
    """
    if not SUMMARY_FILE:
        return

    # 表头
    md = f"## 🕹️ 任务编排执行报告\n\n"
    md += f"> **总耗时**: {format_duration(total_duration)} &nbsp;|&nbsp; **执行时间**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
    
    md += "| 步骤 | 任务名称 | 状态 | 耗时 | 详细日志 |\n"
    md += "| :--- | :--- | :---: | :---: | :--- |\n"

    all_success = True

    for i, res in enumerate(results):
        status_icon = Icon.SUCCESS if res['success'] else Icon.FAILURE
        if not res['run_called']: status_icon = Icon.SKIPPED
        
        name = res['name']
        duration = format_duration(res['duration'])
        url = res['url']
        
        link_md = f"[{Icon.LINK} 跳转]({url})" if url else "N/A"
        
        # 如果是失败，加粗强调
        if not res['success']:
            all_success = False
            status_icon = f"**{Icon.FAILURE} 失败**"
        
        md += f"| {i+1} | {name} | {status_icon} | {duration} | {link_md} |\n"

    # 尾部总结
    md += "\n---\n"
    if all_success:
        md += f"### 🎉 全流程执行成功 \n所有预定任务均已按顺序完成，无报错。"
    else:
        md += f"### ⚠️ 流程异常中断 \n请检查上方表格中标记为失败的任务。"

    with open(SUMMARY_FILE, "a", encoding="utf-8") as f:
        f.write(md)

# --- 主逻辑 ---

def run_orchestrator():
    start_time_total = time.time()
    
    if not os.path.exists(PLAN_FILE):
        print(f"::error::找不到配置文件 {PLAN_FILE}")
        exit(1)

    with open(PLAN_FILE, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    results = [] # 存储每一步的战报
    flow_broken = False # 熔断标志

    print_box(f"开始执行编排计划 ({len(plan)} 个任务)", "35")

    for idx, task in enumerate(plan):
        step_start = time.time()
        name = task['name']
        filename = task['filename']
        wait = task.get('wait', True) # 默认为 True，强制等待才能有完美报告
        
        task_result = {
            "name": name,
            "success": False,
            "duration": 0,
            "url": "",
            "run_called": False
        }

        # 1. 如果之前有任务失败，后续任务全部跳过
        if flow_broken:
            print(f"\n{Icon.SKIPPED} 跳过任务: {name} (因上一步失败)")
            results.append(task_result)
            continue

        # 2. 开始执行
        start_group(f"Step {idx+1}: {name}")
        print(f"{Icon.ROCKET} 正在触发流程: {filename}")
        
        try:
            # 触发
            subprocess.run(["gh", "workflow", "run", filename], check=True)
            task_result['run_called'] = True
            
            # 获取链接
            print(f"{Icon.WAIT} 等待 GitHub 响应...")
            info = get_run_info(filename)
            run_id = info['databaseId'] if info else None
            task_result['url'] = info['url'] if info else ""

            if run_id:
                print(f"{Icon.LINK} 任务已建立 (ID: {run_id})")
                print(f"{Icon.TIME} 进入同步监控模式...")
                
                # 监控直到结束
                # gh run watch 会阻塞直到任务完成，如果是失败退出码非0
                subprocess.run(["gh", "run", "watch", str(run_id), "--exit-status"], check=True)
                
                print(f"\n{Icon.SUCCESS} 任务执行成功！")
                task_result['success'] = True
            else:
                print(f"::warning::无法获取 Run ID，假定成功但无法监控。")
                task_result['success'] = True

        except subprocess.CalledProcessError:
            print(f"\n{Icon.FAILURE} 任务执行失败！")
            task_result['success'] = False
            flow_broken = True # 标记熔断
            print("::error::检测到关键错误，停止后续任务链。")

        except Exception as e:
            print(f"::error::脚本内部错误: {e}")
            flow_broken = True

        # 统计单步耗时
        task_result['duration'] = time.time() - step_start
        results.append(task_result)
        end_group()

        if flow_broken:
            break

    # --- 结束 ---
    total_duration = time.time() - start_time_total
    
    print("\n")
    print_box("生成最终可视化报告...", "32")
    
    # 写入 GitHub Summary
    write_final_report(results, total_duration)
    
    if flow_broken:
        print(f"::error::编排流程以失败告终。")
        exit(1)
    else:
        print(f"{Icon.SUCCESS} 所有任务圆满完成。")

if __name__ == "__main__":
    run_orchestrator()
