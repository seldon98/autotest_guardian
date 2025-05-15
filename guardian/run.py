import os
import argparse
import pytest
import shutil
import os
import argparse
import pytest
import shutil
import yaml
import subprocess
import chardet
from typing import List
from datetime import datetime

# 全局编码设置
import sys
import io

sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
reports_path = rf"E:\Jenkins\SWS_Git\autotest_guardian\guardian\reports\{timestamp}"
temps_path = rf"E:\Jenkins\SWS_Git\autotest_guardian\guardian\temps\{timestamp}"

os.makedirs(reports_path, exist_ok=True)
os.makedirs(temps_path, exist_ok=True)


def load_test_plan(product: str, plan_name: str) -> List[str]:
    """加载测试计划YAML文件并返回用例列表（编码安全版）"""
    plan_path = os.path.join("plan", product, f"{plan_name}.yaml")
    print(f"[DEBUG] 尝试加载测试计划路径: {os.path.abspath(plan_path)}")

    # 检测文件编码
    with open(plan_path, 'rb') as f:
        raw = f.read(1024)
        result = chardet.detect(raw)
        encoding = result['encoding'] or 'utf-8'
        print(f"[DEBUG] 检测到文件编码: {encoding} (置信度: {result['confidence']:.0%})")

    try:
        with open(plan_path, 'r', encoding=encoding) as f:
            plan_data = yaml.safe_load(f)
            return plan_data.get('test_cases', [])
    except UnicodeDecodeError as e:
        raise RuntimeError(f"文件解码失败，请将 {plan_path} 转换为 UTF-8 编码")
    except Exception as e:
        raise RuntimeError(f"YAML加载失败: {str(e)}")

def build_pytest_args(product: str, plan_name: str) -> List[str]:
    """根据测试计划构造pytest执行参数"""
    # 加载测试计划
    test_cases = load_test_plan(product, plan_name)

    # 构造用例路径（确保唯一性）
    case_paths = []
    for case in test_cases:
        module = case.get('module', '')
        case_file = f"test_{case['name']}.py" if not case['name'].startswith('test_') else f"{case['name']}.py"
        path = os.path.join("case", product, module, case_file)
        if os.path.exists(path):
            case_paths.append(path)
        else:
            print(f"[WARNING] 用例文件不存在: {path}")

    if not case_paths:
        raise RuntimeError("没有找到有效的测试用例路径")

    return [
        *case_paths,
        f"--product={product}",
        f"--plan={plan_name}",
        f"--alluredir=temps/{timestamp}",
        "-v",
        "--capture=fd",  # 确保捕获所有输出
        "--log-level=DEBUG",
        "--show-capture=all"
    ]


def generate_allure_report() -> None:
    """生成Allure报告并验证结果"""
    #  确保报告目录存在
    # os.makedirs("reports", exist_ok=True)

    # 执行Allure命令
    allure_cmd = f"allure generate temps/{timestamp} -o reports/{timestamp} --clean"
    if os.system(allure_cmd) == 0:
        report_path = os.path.abspath(f"reports/{timestamp}/index.html")
        print(f"\n[SUCCESS] 报告路径：file://{report_path}")
    else:
        print("[ERROR] 报告生成失败，请检查：")
        print("1. Allure是否安装且版本 > 2.13")
        print("2. 环境变量PATH是否包含Allure路径")


def main():
    parser = argparse.ArgumentParser(description="自动化测试执行引擎")
    parser.add_argument("-P", "--product", required=True, help="产品名称 (e.g. xuitra)")
    parser.add_argument("-M", "--plan", required=True, help="测试计划名称 (e.g. upgrade)")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="日志详细级别")
    args = parser.parse_args()

    # 构造 pytest 参数
    pytest_args = [
        "-s",
        "-v",
        f"--log-level={args.log_level}",
        f"--product={args.product}",
        f"--plan={args.plan}"
    ]

    try:
        # 构造 pytest 执行参数
        pytest_args = build_pytest_args(args.product, args.plan)

        # 添加必要参数（确保不重复）
        base_args = [
            "-s",
            "-v",
            f"--log-level={args.log_level}",
            f"--alluredir={temps_path}"
        ]
        full_args = base_args + pytest_args

        print("\n=== 测试执行参数 ===")
        print("pytest " + " ".join(full_args))

        # 执行测试（同步阻塞执行）
        print("\n=== 开始执行测试 ===")
        exit_code = pytest.main(full_args)

        # 结果状态码处理
        if exit_code == pytest.ExitCode.OK:
            print("\n[SUCCESS] 所有测试用例执行完成")
        elif exit_code == pytest.ExitCode.TESTS_FAILED:
            print(f"\n[WARNING] 测试失败 (失败用例数: {exit_code})")
        else:
            print(f"\n[ERROR] 异常退出 (代码: {exit_code})")

        # 生成Allure报告（无论结果如何）
        print("\n=== 生成测试报告 ===")
        generate_allure_report()

        # 清理临时文件（按需开启）
        if os.path.exists(temps_path):
            shutil.rmtree(temps_path)
            print(f"已清理临时文件: {temps_path}")

    except Exception as e:
        print(f"\n[CRITICAL] 主程序异常: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
