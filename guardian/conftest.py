import os
import yaml
import importlib
import pytest
import serial
import allure
from pathlib import Path
from typing import Dict, Any, Generator
from datetime import datetime
from serial import SerialException
import logging

# 环境常量定义
PROJECT_ROOT = Path(__file__).parent.resolve()  # 项目根目录
CONFIG_BASE = PROJECT_ROOT / "plan"  # 配置基准目录


def pytest_addoption(parser):
    """注册自定义命令行参数 (兼容旧版本写法)"""
    # 产品参数组
    parser.addoption(
        "--product", "-P",
        action="store",
        default="XUTra",  # 直接设置默认值，不从 ini 读取
        help="指定产品名称，如 XUTra"
    )
    parser.addoption(
        "--plan", "-M",
        action="store",
        default="smoke",  # 直接设置默认值
        help="指定测试计划名称，如 smoke"
    )


def pytest_configure(config):
    """强制设置动态日志文件路径"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dynamic_log_path = log_dir / f"atf_{timestamp}.log"

    # 关键操作：覆盖pytest配置
    config.option.log_file = str(dynamic_log_path)
    config.option.log_file_level = "DEBUG"

    # 初始化基础日志配置
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)-8s %(asctime)s [%(name)s:%(lineno)s] : %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True  # 覆盖已有配置
    )


def resolve_config_path(product: str, plan: str) -> Path:
    """解析配置文件路径"""
    config_path = CONFIG_BASE / product / f"{plan}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"测试计划文件不存在: {config_path}")
    return config_path


@pytest.fixture(scope="session")
def device_config(request: pytest.FixtureRequest) -> Dict[str, Any]:
    """加载设备配置（session级）"""
    product = request.config.getoption("--product")
    config_path = CONFIG_BASE / product / "device.yaml"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 配置项完整性校验
        required = {"serial_port", "baud_rate", "parity", "stop_bits", "data_bits"}
        if missing := required - config.keys():
            pytest.fail(f"设备配置缺失必要字段: {missing}")

        return config
    except Exception as e:
        pytest.exit(f"设备配置加载失败: {str(e)}")


@pytest.fixture(scope="module")
def serial_conn(device_config: Dict) -> Generator[serial.Serial, None, None]:
    """串口连接fixture（模块级复用）"""
    conn = None
    try:
        conn = serial.Serial(
            port=device_config["serial_port"],
            baudrate=device_config["baud_rate"],
            parity=device_config["parity"],
            stopbits=device_config["stop_bits"],
            bytesize=device_config["data_bits"],
            timeout=2.0
        )
        if not conn.is_open:
            raise SerialException("Serial port not open after initialization")

        yield conn
    except SerialException as e:
        pytest.fail(f"串口连接失败: {str(e)}\n当前配置: {device_config}")
    finally:
        if conn and conn.is_open:
            conn.close()


def load_test_cases(config_path: Path) -> list:
    """从YAML加载测试用例配置（修复版）"""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if "test_cases" not in config:
        pytest.exit(f"配置文件缺少 'test_cases' 节点: {config_path}")

    test_cases = []
    for case in config["test_cases"]:
        # 强制统一产品名称为小写
        case['product'] = case['product'].strip().lower()

        # 构建模块物理路径
        module_file = (
                PROJECT_ROOT /
                "case" /
                case['product'] /
                case['module'] /
                f"{case['name']}.py"
        )

        # 文件存在性检查
        if not module_file.exists():
            pytest.exit(f"测试文件不存在: {module_file}")

        # 构建导入路径
        module_path = f"case.{case['product']}.{case['module']}.{case['name']}"

        try:
            importlib.import_module(module_path)
        except Exception as e:
            pytest.exit(f"模块加载失败: {module_path} - {str(e)}")

        test_cases.extend(
            [{"name": case["name"], "loop": i, "desc": case["description"]}
             for i in range(1, case["loops"] + 1)]
        )

    return test_cases


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """动态生成参数化测试"""
    if "case_config" in metafunc.fixturenames:
        product = metafunc.config.getoption("--product")
        plan = metafunc.config.getoption("--plan")

        try:
            config_path = resolve_config_path(product, plan)
            test_cases = load_test_cases(config_path)
            metafunc.parametrize("case_config", test_cases)
        except Exception as e:
            pytest.exit(f"测试用例生成失败: {str(e)}")


@pytest.fixture(autouse=True)
def allure_logger(case_config: Dict) -> None:
    """自动注入Allure元数据"""
    allure.dynamic.title(f"{case_config['name']} - Loop {case_config['loop']}")
    allure.dynamic.description(case_config.get("desc", ""))

