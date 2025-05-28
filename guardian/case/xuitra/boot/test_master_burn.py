import logging
import serial
import serial.tools.list_ports
import os
from common.boot_base import ESP32Flasher
import re
import sys

# 使用绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 宏定义：设置这些路径为当前目录下的某个子目录中的文件
STABLE_FIRMWARE_FILE_PATH = ""
STABLE_BOOTLOADER_FILE_PATH = "./case/xuitra/boot/base/bootloader.bin"
STABLE_PARTITION_FILE_PATH = "./case/xuitra/boot/base/partitions.bin"
STABLE_OTA_DATA_INITIAL_PATH = "./case/xuitra/boot/base/ota_data_initial.bin"

class TestMasterBurn:
    @staticmethod
    def find_cp210_port():
        """检测 CP210x 设备的串口"""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "CP210x" in port.description:
                logging.info(f"找到 CP210x 设备: {port.device}")
                return port.device
        logging.warning("未找到 CP210x 设备")
        return None

    def parse_version(self,filename):
        # 使用正则表达式匹配版本号，假设版本号格式为 1.0.10.0
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', filename)
        if not match:
            return None
        version_str = match.group(1)
        # 将版本号字符串转换为元组，如 "1.0.10.0" -> (1, 0, 10, 0)
        return tuple(map(int, version_str.split('.')))

    def find_latest_version_file_esp(self, directory_path):
        latest_version = ()
        latest_file = None

        for filename in os.listdir(directory_path):
            if "ESP32_Masterboard_Firmware" in filename:
                version = self.parse_version(filename)
                if version is not None and version > latest_version:
                    latest_version = version
                    latest_file = filename

        return latest_file

    def resource_path(self,relative_path):
        """ 获取资源的绝对路径 """
        if getattr(sys, 'frozen', False):
            # 如果是打包后的可执行文件
            application_path = os.path.dirname(sys.executable)
        else:
            # 如果是开发环境
            application_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(application_path, relative_path)

    def burn_master(self, masterboard_type):  # masterboard_type: "release" or "base"
        port = self.find_cp210_port()
        if not port:
            logging.error("未检测到 CP210x 设备，终止测试")
            assert False, "未找到 CP210x 设备"
            return

        # 正确拼接路径

        directory_path = os.path.join(BASE_DIR, masterboard_type)
        if not os.path.exists(directory_path):
            logging.error(f"目录不存在: {directory_path}")
            assert False, f"路径错误，目录不存在: {directory_path}"
            return

        latest_file_esp = self.find_latest_version_file_esp(directory_path)
        if not latest_file_esp:
            logging.error(f"{directory_path} 未找到固件文件")
            assert False, "未找到主控固件文件"
            return

        STABLE_FIRMWARE_FILE_PATH = os.path.join(directory_path, latest_file_esp)
        logging.info(f"将烧录固件: {STABLE_FIRMWARE_FILE_PATH}")

        flasher = ESP32Flasher(port)
        try:
            download_success = flasher.flash_firmware(
                STABLE_FIRMWARE_FILE_PATH,
                STABLE_BOOTLOADER_FILE_PATH,
                STABLE_PARTITION_FILE_PATH,
                STABLE_OTA_DATA_INITIAL_PATH,
                port
            )
        except Exception as e:
            logging.error(f"烧录过程中发生异常: {str(e)}")
            return False

        if download_success:
            logging.info("主控固件烧录成功")
            return True
        else:
            logging.error("主控固件烧录失败")
            return False

    def test_execution(self, case_config):
        assert self.burn_master("base"), "Release 固件烧录失败"
        assert self.burn_master("release"), "Base 固件烧录失败"

