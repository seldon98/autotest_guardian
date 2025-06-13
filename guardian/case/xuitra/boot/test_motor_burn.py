import os
import re
import sys
import time
import logging
import hashlib
import serial
import serial.tools.list_ports
from datetime import datetime
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class TestMotorBurn:
    def prepare(self):
        self.esp32_line = b''
        self.write_back_result = ''

    def read_line(self, ser):
        self.esp32_line += ser.readline()
        if self.esp32_line and self.esp32_line[-1] == ord('\n'):
            line = self.esp32_line
            self.esp32_line = b''
            return line
        return b''

    def get_md5(self, filename):
        hash_md5 = hashlib.md5()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def read_file_and_get_size(self, filename):
        with open(filename, 'rb') as file:
            data = file.read()
        return data, len(data)

    def parse_version(self, filename):
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', filename)
        return tuple(map(int, match.group(1).split('.'))) if match else None

    def get_latest_firmware(self,release_type: str) -> str:
        """
        device_type: "stm32"
        release_type: "release" or "base"
        """
        folder = os.path.join(BASE_DIR,  release_type)
        if not os.path.exists(folder):
            raise FileNotFoundError(f"路径不存在: {folder}")

        latest_version = ()
        latest_file = None

        for filename in os.listdir(folder):
            if "Compressed" in filename or "Motor_Firmware" in filename:
                version = self.parse_version(filename)
                if version and version > latest_version:
                    latest_version = version
                    latest_file = filename

        if not latest_file:
            raise FileNotFoundError(f" 固件未找到 in {folder}")
        return os.path.join(folder, latest_file)

    def split_bytes(self, data, n):
        return [data[i:i + n] for i in range(0, len(data), n)]

    def write_back(self, ser, command, expected, timeout=5, error=None):
        try:
            ser.write(command.encode('utf-8'))
        except Exception as e:
            logging.error(f"串口写入失败: {e}")
            return False

        self.write_back_result = ""
        start_time = time.time()
        while True:
            try:
                line = self.read_line(ser)
            except Exception as e:
                logging.error(f"串口读取异常: {e}")
                return False

            if line:
                try:
                    decoded = line.decode('utf-8').strip()
                    logging.info(f"[ESP32] {decoded}")
                    self.write_back_result = decoded
                except:
                    continue
                if expected in self.write_back_result:
                    return True
                if error and error in self.write_back_result:
                    return False

            if time.time() - start_time > timeout:
                logging.error("串口等待超时")
                return False

    def burn_motor(self, release_type="release", max_retries=2):
        try:
            firmware_path = self.get_latest_firmware(release_type)
        except FileNotFoundError as e:
            logging.error(e)
            return False

        logging.info(f"使用固件: {firmware_path}")

        ports_last = 0
        retries = 0

        while retries <= max_retries:
            ports = list(serial.tools.list_ports.comports())
            esp_port = None

            for p in ports:
                if "CP210" in p.description:
                    esp_port = p.device
                    break

            if not esp_port:
                logging.warning("未找到 ESP32 串口 (CP210x)")
                time.sleep(1)
                continue

            try:
                with serial.Serial(esp_port, 3000000, timeout=0.0) as ser:
                    logging.info(f"连接 ESP32 串口: {esp_port}")
                    ser.dtr = 0
                    ser.dtr = 1
                    time.sleep(1.5)

                    if not self.write_back(ser, "ping\n", "ping", timeout=2):
                        logging.warning("ESP32 无响应 ping")
                        continue

                    ser.write(b'firmware\n')

                    data, size = self.read_file_and_get_size(firmware_path)
                    md5 = self.get_md5(firmware_path)

                    ser.write(f"{size}\n".encode('utf-8'))
                    ser.write(f"{md5}\n".encode('utf-8'))

                    time.sleep(0.5)

                    for chunk in self.split_bytes(data, 4096):
                        ser.write(chunk)

                    start_time = datetime.now()

                    while True:
                        line = self.read_line(ser)
                        if not line:
                            time.sleep(0.1)
                            continue
                        decoded = line.decode('utf-8').strip()
                        logging.info(f"[ESP32] {decoded}")
                        if decoded == "firmware ok":
                            logging.info("固件烧录成功")
                            return True
                        if decoded == "md5 not match":
                            logging.warning("MD5 校验失败，重试")
                            break
                        if (datetime.now() - start_time).total_seconds() > 120:
                            logging.error("烧录超时")
                            return False
            except Exception as e:
                logging.error(f"ESP32 串口连接失败: {e}")

            retries += 1
            logging.info(f"重试中... (第 {retries}/{max_retries} 次)")

        logging.error("超过最大重试次数，烧录失败")
        return False

    def burn(self, release_type):
        if self.burn_motor(release_type):
            logging.info(f"{release_type} 烧录成功")
            return True
        else:
            logging.error(f"{release_type} 烧录失败")
            return False

    def test_execution(self):
        self.prepare()
        # assert self.burn("base"), "Base 电机固件烧录失败"
        assert self.burn("release"), "Release 电机固件烧录失败"
