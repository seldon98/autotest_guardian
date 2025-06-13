import logging
import serial
import serial.tools.list_ports
import os
from common.boot_base import ESP32Flasher
import re
import sys

# 使用绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

    def parse_version(self, filename):
        # 匹配类似 1.0.10.0 的版本号
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', filename)
        if not match:
            return None
        version_str = match.group(1)
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

    def resource_path(self, relative_path):
        """ 获取资源的绝对路径 """
        if getattr(sys, 'frozen', False):
            # PyInstaller 打包后路径
            application_path = os.path.dirname(sys.executable)
        else:
            # 开发环境
            application_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(application_path, relative_path)

    def get_base_firmware_paths(self):
        """返回基础 bootloader/partition/ota 的路径字典"""
        paths = {
            "bootloader": self.resource_path("case/xuitra/boot/base/bootloader.bin"),
            "partition": self.resource_path("case/xuitra/boot/base/partitions.bin"),
            "ota": self.resource_path("case/xuitra/boot/base/ota_data_initial.bin"),
        }

        for name, path in paths.items():
            if not os.path.exists(path):
                logging.error(f"缺少基础固件文件: {name} 路径无效: {path}")
                raise FileNotFoundError(f"{name} 路径无效: {path}")

        return paths

    def burn_master(self, masterboard_type):  # masterboard_type: "release" or "base"
        port = self.find_cp210_port()
        if not port:
            logging.error("未检测到 CP210x 设备，终止测试")
            assert False, "未找到 CP210x 设备"
            return

        # 查找主控固件文件
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

        firmware_path = os.path.join(directory_path, latest_file_esp)
        logging.info(f"将烧录固件: {firmware_path}")

        # 获取 bootloader/partition/ota 文件路径
        try:
            base_paths = self.get_base_firmware_paths()
        except FileNotFoundError as e:
            assert False, str(e)
            return False

        # 执行烧录
        flasher = ESP32Flasher(port)
        try:
            download_success = flasher.flash_firmware(
                firmware_path,
                base_paths["bootloader"],
                base_paths["partition"],
                base_paths["ota"],
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
        assert self.burn_master("release"), "Release 固件烧录失败"
