import os
import argparse
import pytest
import shutil


def clean_directory(dir_path: str):
    """通用目录清理函数"""
    try:
        shutil.rmtree(dir_path)
        print(f"[INFO] 成功清理目录: {dir_path}")
    except FileNotFoundError:
        print(f"[INFO] 目录不存在: {dir_path}")
    except Exception as e:
        print(f"[WARNING] 清理目录 {dir_path} 失败: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description='运行测试')
    parser.add_argument('-P', '--product', required=True, help='产品名称，如 wm630')
    parser.add_argument('-M', '--module', required=True, help='测试模块，如 reboot')
    args = parser.parse_args()

    # 阶段1：运行测试前清理
    print("\n=== 预清理阶段 ===")
    clean_directory('temps')
    clean_directory('reports')

    # 确保临时目录存在
    os.makedirs("temps", exist_ok=True)

    # 执行测试
    pytest_args = [
        f"--product={args.product}",
        f"--module={args.module}",
        "case/",
        "--alluredir=temps"
    ]
    print("\n[DEBUG] 传递给 pytest 的参数:", pytest_args)
    exit_code = pytest.main(pytest_args)

    # 阶段2：生成报告前再次清理（冗余保障）
    print("\n=== 报告生成前清理 ===")
    clean_directory('reports')

    # 生成Allure报告（使用--clean参数三重保障）
    print("\n=== 报告生成阶段 ===")
    if not os.listdir("temps"):
        print("[ERROR] 测试数据为空，可能原因：")
        print("1. 测试用例未执行成功")
        print("2. 用例路径配置错误")
        return

    allure_cmd = "allure generate temps -o reports --clean"
    if os.system(allure_cmd) == 0:
        report_path = os.path.abspath("reports/index.html")
        print(f"\n[SUCCESS] 报告路径：file://{report_path}")
    else:
        print("[ERROR] 报告生成失败，请检查：")
        print("1. Allure是否安装且版本 > 2.13")
        print("2. 环境变量PATH是否包含Allure路径")


if __name__ == '__main__':
    main()
