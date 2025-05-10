import os
import yaml
import importlib
import pytest
import serial
import allure
from pathlib import Path
from typing import Dict, Any, Generator, List
from datetime import datetime
from serial import SerialException
import logging
import chardet

# --------------------------
# 环境常量与基础配置
# --------------------------
PROJECT_ROOT = Path(__file__).parent.resolve()
CONFIG_BASE = PROJECT_ROOT / "plan"
CONFIG_LOGGER = logging.getLogger("config_loader")


def pytest_addoption(parser):
    """注册自定义命令行参数"""
    parser.addoption("--product", "-P", default="xuitra", help="指定产品名称")
    parser.addoption("--plan", "-M", default="smoke", help="指定测试计划名称")


def pytest_configure(config):
    """动态配置日志系统"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dynamic_log_path = log_dir / f"atf_{timestamp}.log"

    # 强制覆盖pytest日志配置
    config.option.log_file = str(dynamic_log_path)
    config.option.log_file_level = "DEBUG"

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)-8s %(asctime)s [%(name)s:%(lineno)s] : %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True
    )


# --------------------------
# 配置加载与验证
# --------------------------
def resolve_config_path(product: str, plan: str) -> Path:
    """解析测试计划路径"""
    config_path = CONFIG_BASE / product / f"{plan}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"测试计划文件不存在: {config_path}")
    return config_path


def load_test_cases(config_path: Path) -> List[Dict]:
    """安全加载测试用例配置"""
    # 检测文件编码
    with open(config_path, "rb") as f:
        encoding = chardet.detect(f.read(1024))["encoding"] or "utf-8"

    try:
        with open(config_path, "r", encoding=encoding, errors="strict") as f:
            config = yaml.safe_load(f)
    except UnicodeError as e:
        pytest.exit(f"文件解码失败: {config_path}\n编码: {encoding}\n错误: {str(e)}")

    # 结构验证
    if not isinstance(config.get("test_cases"), list):
        pytest.exit(f"配置文件结构错误: test_cases 必须是列表类型")

    CONFIG_LOGGER.debug(f"成功加载测试用例数量: {len(config['test_cases'])}")
    return config["test_cases"]


# --------------------------
# 核心参数化逻辑
# --------------------------
# 修改 conftest.py 中的 pytest_generate_tests 函数
def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """动态生成参数化测试（带类过滤及循环扩展）"""
    if "case_config" in metafunc.fixturenames:
        product = metafunc.config.getoption("--product")
        plan = metafunc.config.getoption("--plan")

        try:
            # 加载测试用例配置
            config_path = resolve_config_path(product, plan)
            all_cases = load_test_cases(config_path)

            # 获取当前测试类名
            current_class = metafunc.cls.__name__ if metafunc.cls else None
            if not current_class:
                return  # 非类测试不处理

            filtered_cases = []
            for case in all_cases:
                if case.get("class") == current_class:
                    loops = case.get("loops", 1)
                    # 根据循环次数扩展用例
                    for loop_num in range(loops):
                        new_case = case.copy()
                        new_case['loop'] = loop_num + 1  # 记录当前循环次数
                        filtered_cases.append(new_case)

            CONFIG_LOGGER.debug(
                f"类 [{current_class}] 生成 {len(filtered_cases)} 个测试实例 | "
                f"原始用例数: {len(all_cases)}"
            )

            metafunc.parametrize("case_config", filtered_cases)

        except Exception as e:
            pytest.exit(f"测试用例生成失败: {str(e)}")



# --------------------------
# 设备连接与Allure集成
# --------------------------
@pytest.fixture(scope="session")
def device_config(request: pytest.FixtureRequest) -> Dict[str, Any]:
    """加载设备配置（会话级）"""
    product = request.config.getoption("--product")
    config_path = CONFIG_BASE / product / "device.yaml"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 配置项校验
        required_fields = {"serial_port", "baud_rate", "parity", "stop_bits", "data_bits"}
        if missing := required_fields - config.keys():
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
            raise SerialException("串口初始化后未打开")

        yield conn
    except SerialException as e:
        pytest.fail(f"串口连接失败: {str(e)}\n当前配置: {device_config}")
    finally:
        if conn and conn.is_open:
            conn.close()


@pytest.fixture(autouse=True)
def allure_logger(case_config: Dict) -> None:
    """自动注入Allure元数据（含循环信息）"""
    base_desc = f"用例循环次数: {case_config.get('loops', 1)}"
    if 'loop' in case_config:
        base_desc += f" | 当前循环: {case_config['loop']}"

    allure.dynamic.title(case_config["name"])
    allure.dynamic.description(base_desc)
