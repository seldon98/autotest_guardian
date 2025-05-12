# test_boot.py
import logging
import serial
import serial.tools.list_ports
import time
import os
import esptool
from common.boot_common import ESP32Flasher

# 使用绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 宏定义：设置这些路径为当前目录下的某个子目录中的文件
STABLE_FIRMWARE_FILE_PATH = "./esp32/stable/firmware.bin"
STABLE_BOOTLOADER_FILE_PATH = "./esp32/stable/bootloader.bin"
STABLE_PARTITION_FILE_PATH = "./esp32/stable/partitions.bin"
STABLE_OTA_DATA_INITIAL_PATH = "./esp32/stable/ota_data_initial.bin"

class TestBoot:
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

    def test_execution(self, case_config):
        port = TestBoot.find_cp210_port()
        if not port:
            logging.error("未检测到 CP210x 设备，终止测试")
            assert False, "未找到 CP210x 设备"
            return

        print('================')
        print(STABLE_BOOTLOADER_FILE_PATH)

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
            download_success = False

        if download_success:
            logging.info("固件下载成功")
        else:
            logging.error("固件下载失败")
            assert False, "固件烧录失败"
