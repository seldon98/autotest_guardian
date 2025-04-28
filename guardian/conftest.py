import yaml
import importlib
import sys
import allure
from datetime import datetime
import os
import pytest
import serial
from serial import SerialException

def pytest_addoption(parser):
    """统一注册所有自定义命令行参数"""
    # 产品参数组
    parser.addoption(
        "--product", "-P",
        action="store",
        default="wm630",
        help="指定产品名称，如 wm630"
    )
    parser.addoption(
        "--module", "-M",
        action="store",
        default="smoke",
        help="指定测试模块，如 smoke"
    )

    # 废弃参数组（如需保留需调整逻辑）
    parser.addoption(
        "--project-name",
        help="[已废弃] 指定项目名称（对应plan目录下的子目录名）",
        default=None
    )
    parser.addoption(
        "--device-config",
        help="[已废弃] 直接指定配置文件绝对路径（覆盖--project-name）",
        default=None
    )


# 创建新建日志文件，文件名以时间戳_atf.log格式
def pytest_configure(config):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_dir = "./logs"
    log_filename = f"{timestamp}_atf.log"

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file_path = os.path.join(log_dir, log_filename)
    config.option.log_file = log_file_path


@pytest.fixture(scope="session")
def product_config(request):
    """加载产品配置"""
    product = request.config.getoption("--product")
    config_path = f"D:\\Jenkins\\SWS_Git\\guradian\\plan\\{product}\\device.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        pytest.exit(f"产品配置加载失败: {str(e)}")


@pytest.fixture
def load_test_config(request):
    """加载YAML测试配置（带编码修复）"""
    product = request.config.getoption('--product')
    module = request.config.getoption('--module')
    config_path = os.path.join(os.path.dirname(__file__), f'D:\\Jenkins\\SWS_Git\\guradian\\plan\\{product}\\{module}.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except UnicodeDecodeError:
        # 如果UTF-8失败，尝试其他编码
        with open(config_path, 'r', encoding='gb18030') as f:
            return yaml.safe_load(f)


def load_device_config(request):
    product = request.config.getoption("--product")
    base_dir = os.path.abspath(os.path.dirname(__file__))  # 获取项目根目录
    config_path = os.path.join(base_dir, f'D:\\Jenkins\\SWS_Git\\guradian\\plan\\{product}\\device.yaml')
    # ...保持后续逻辑不变
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise ValueError(f"设备配置文件不存在: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"配置文件解析失败: {str(e)}")


@pytest.fixture(scope="session")
def device_config(request):
    """设备配置信息fixture"""
    try:
        return load_device_config(request)
    except Exception as e:
        pytest.exit(f"配置加载失败: {str(e)}")


@pytest.fixture(scope="function")
def serial_connection(device_config) -> serial.Serial:
    """串口连接fixture"""
    config = device_config.get('serial', {})
    required_keys = ['serial_port', 'baud_rate', 'parity', 'stop_bits', 'data_bits']
    missing = [k for k in required_keys if k not in config]
    if missing:
        pytest.fail(f"串口配置缺失必要字段: {missing}")
    try:
        conn = serial.Serial(
            port=config['serial_port'],
            baudrate=config['baud_rate'],
            parity=config['parity'],
            stopbits=config['stop_bits'],
            bytesize=config['data_bits'],
            timeout=2
        )
        if not conn.is_open:
            raise SerialException(f"无法打开串口 {config['serial_port']}")
        yield conn
    except KeyError as e:
        pytest.fail(f"缺失关键配置项: {str(e)}")
    except SerialException as e:
        pytest.fail(f"串口连接失败: {str(e)}\n当前配置: {config}")
    finally:
        if 'conn' in locals() and conn.is_open:
            conn.close()


def pytest_generate_tests(metafunc):
    if 'case_config' in metafunc.fixturenames:
        try:
            product = metafunc.config.getoption("--product")
            module = metafunc.config.getoption("--module")

            config_path = os.path.join(
                os.path.dirname(__file__),
                f'D:\\Jenkins\\SWS_Git\\guardian\\plan\\{product}\\{module}.yaml'
            )

            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                print(f"Loaded config: {config}")

            test_cases = []
            if 'test_cases' in config:
                for case in config['test_cases']:
                    module = importlib.import_module(
                        f"case.{case['product']}.{case['module']}.{case['name']}"
                    )
                    for i in range(1, case['loops'] + 1):
                        test_cases.append({
                            'name': case['name'],
                            'module': module,
                            'loop': i,
                            'desc': case['description']
                        })
            else:
                pytest.exit(f"配置文件中缺少 'test_cases' 键: {config_path}")

            metafunc.parametrize('case_config', test_cases)

        except FileNotFoundError:
            pytest.exit(f"配置文件不存在: {config_path}")
        except yaml.YAMLError as e:
            pytest.exit(f"YAML解析失败: {str(e)}")
        except KeyError as e:
            pytest.exit(f"配置字段缺失: {str(e)}")
        except Exception as e:
            pytest.exit(f"未知错误: {str(e)}")


@pytest.fixture
def allure_metadata(case_config):
    """Allure元数据注入"""
    with allure.step(f"Test {case_config['name']} iteration {case_config['loop']}"):
        allure.dynamic.title(f"{case_config['name']} - Iter {case_config['loop']}")
        yield
