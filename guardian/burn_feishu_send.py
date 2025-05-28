import sys
import requests
import json as jsonlib
import os


build_number = os.getenv("BUILD_NUMBER")
JOB_URL = sys.argv[1]
TIMESTAMP = sys.argv[2]

# 飞书按钮链接
allure_report_url = f"{JOB_URL.rstrip('/')}/allure"

base_dir = os.path.dirname(os.path.abspath(__file__))
summary_path = os.path.join(base_dir, "reports", TIMESTAMP, "widgets", "summary.json")

# 默认值
passed = failed = skipped = broken = unknown = total = 0

if os.path.exists(summary_path):
    with open(summary_path, 'r', encoding='utf-8') as f:
        data = jsonlib.load(f)
        stats = data.get("statistic", {})
        passed = stats.get("passed", 0)
        failed = stats.get("failed", 0)
        skipped = stats.get("skipped", 0)
        broken = stats.get("broken", 0)
        unknown = stats.get("unknown", 0)
        total = stats.get("total", 0)
else:
    print(f"[WARN] summary.json not found at: {summary_path}")

url = 'https://open.feishu.cn/open-apis/bot/v2/hook/3d50eb4e-1db3-4e58-9b92-9d5c77fa9528'
headers = {'Content-Type': 'application/json'}

message = {
    "msg_type": "interactive",
    "card": {
        "config": {
            "wide_screen_mode": True,
            "enable_forward": True
        },
        "header": {
            "title": {
                "content": "🔥 烧录自动化测试完成",
                "tag": "plain_text"
            },
            "template": "green" if failed == 0 else "red"
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"🕓 **测试时间**：{TIMESTAMP}"
                }
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**构建号**：{build_number}"
                }
            },
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"""📊 **用例统计**
- ✅ 通过：{passed}
- ❌ 失败：{failed}
- ⚠️ 跳过：{skipped}
- 🧨 崩溃：{broken}
- ❓ 未知：{unknown}
- 📦 总数：{total}"""
                }
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {
                            "tag": "lark_md",
                            "content": "📄 查看 burn 报告"
                        },
                        "url": rf"http://10.1.0.66:8083/job/XUItra/job/boot/HTML_20Report/",
                        "type": "primary",
                        "value": {}
                    }
                ]
            }
        ]
    }
}

resp = requests.post(url, headers=headers, json=message)
if resp.status_code != 200:
    print(f"[ERROR] 飞书通知发送失败: {resp.status_code} - {resp.text}")
else:
    print("[INFO] 飞书通知已发送成功。")
