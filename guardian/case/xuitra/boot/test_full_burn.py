from math import lgamma

import select
import subprocess
import serial.tools.list_ports
import serial
from threading import Timer
import esptool
import platform
from threading import Thread
from pathlib import Path
from tkinter import ttk, font
import sys
import os
import logging
from datetime import datetime
import re
import hashlib
import time
from common.boot_base import ESP32Flasher

# 使用绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 宏定义：设置这些路径为当前目录下的某个子目录中的文件
STABLE_FIRMWARE_FILE_PATH = ""
STABLE_BOOTLOADER_FILE_PATH = "./case/xuitra/boot/base/bootloader.bin"
STABLE_PARTITION_FILE_PATH = "./case/xuitra/boot/base/partitions.bin"
STABLE_OTA_DATA_INITIAL_PATH = "./case/xuitra/boot/base/ota_data_initial.bin"


esp32_line = b''
write_back_result = ""

class TestFullBurn:


    def read_line(self, serialEsp32):
        global esp32_line
        esp32_line += serialEsp32.readline()
        if esp32_line != b'' and esp32_line[-1] == ord('\n'):
            line = esp32_line
            esp32_line = b''
            return line
        else:
            return b''

    def millis(self):
        return round(time.time() * 1000)

    def runCommand(self, command, callback=None):
        global pythonProcess
        global pythonProcessPoll
        pythonProcess = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, stderr=subprocess.STDOUT,
                                         bufsize=0)
        pythonProcessPoll = select.poll()
        pythonProcessPoll.register(pythonProcess.stdout, select.POLLIN)

        def _update():
            output = b''
            isRunning = True
            timer = self.millis()
            while pythonProcessPoll.poll(0):
                line = pythonProcess.stdout.read(1)
                if line == b'':
                    isRunning = False
                    break
                output += line
                if self.millis() - timer > 30:
                    output += pythonProcess.stdout.readline()
                    break
            if output:
                if callback is not None:
                    callback(output.decode('UTF-8'))
            if isRunning:
                Timer(0.03, _update).start()

        Timer(0.03, _update).start()
        pythonProcess.wait()
        time.sleep(0.04)

    def read_file_and_get_size(self, filename):
        with open(filename, 'rb') as file:
            data = file.read()
        file_size = os.path.getsize(filename)
        return data, file_size



    def get_md5(self, filename):
        hash_md5 = hashlib.md5()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    isEsp32Available = 0
    isEsp32Connected = 0

    def split_bytes(self, data, n):
        return [data[i:i + n] for i in range(0, len(data), n)]


    def write_back(self, serialEsp32, commmand, back, timeout, error=None):
        global write_back_result
        try:
            serialEsp32.write(commmand.encode('utf-8'))
        except Exception as e:
            print(e)
        start_time = time.time()
        write_back_result = ""
        while True:
            try:
                line = self.read_line(serialEsp32)
            except Exception as e:
                print(e)
                return False
            if line == b'':
                time.sleep(0.1)
            else:
                try:
                    write_back_result = line.decode('utf-8')
                except Exception as e:
                    print(e)
                if back in write_back_result:
                    return True
                if error is not None:
                    if error in write_back_result:
                        return False
            if time.time() - start_time > timeout:
                return False



    def parse_version(self,filename):
        # 使用正则表达式匹配版本号，假设版本号格式为 1.0.10.0
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', filename)
        if not match:
            return None
        version_str = match.group(1)
        # 将版本号字符串转换为元组，如 "1.0.10.0" -> (1, 0, 10, 0)
        return tuple(map(int, version_str.split('.')))

    def find_latest_version_file_stm(self,directory_path):
        latest_version = ()
        latest_file = None

        for filename in os.listdir(directory_path):
            if "STM32_Compressed_Motor_Firmware" in filename:
                version = self.parse_version(filename)
                if version is not None and version > latest_version:
                    latest_version = version
                    latest_file = filename

        if latest_file != None:
            return latest_file

        for filename in os.listdir(directory_path):
            if "STM32_Motor_Firmware" in filename:
                version = self.parse_version(filename)
                if version is not None and version > latest_version:
                    latest_version = version
                    latest_file = filename
        return latest_file

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

    # 替换为你的目录路径

    # 添加以下函数在文件开头的 import 部分之后
    def resource_path(self,relative_path):
        """ 获取资源的绝对路径 """
        if getattr(sys, 'frozen', False):
            # 如果是打包后的可执行文件
            application_path = os.path.dirname(sys.executable)
        else:
            # 如果是开发环境
            application_path = os.path.dirname(os.path.abspath(__file__))



        return os.path.join(application_path, relative_path)

    def burn_motor(self, path):

        Flag = False

        isEsp32Available = 0
        isEsp32Connected = 0

        directory_path = self.resource_path(path)
        latest_file_stm = self.find_latest_version_file_stm(directory_path)
        logging.info(directory_path)
        logging.info(latest_file_stm)

        ports_lens_last = 0


        while True:

            time.sleep(0.03)
            ports = list(serial.tools.list_ports.comports())

            isEsp32Available = 0

            esp_port = None

            for p in ports:
                if len(ports) != ports_lens_last:
                    print(p)
                logging.info(p)

                if "CP210" in p[1]:

                    isEsp32Available = 1
                    if isEsp32Connected == 0:
                        try:
                            serialEsp32 = serial.Serial(p[0], 3000000, timeout=0.1)
                            serialEsp32.dtr = 0
                            serialEsp32.dtr = 1
                            logging.info("Esp32 conneted!")
                            hall_finished = False
                            esp_port = p[0]
                            isEsp32Connected = 1
                        except:
                            logging.error("error Esp32")
                            isEsp32Connected = 0
                            continue

            ports_lens_last = len(ports)

            if isEsp32Connected == 1:
                time.sleep(1.5)

                if self.write_back(serialEsp32, "ping\n", "ping", 2):
                    logging.info("ping ok")
                else:
                    logging.error("ping error")
                    continue

                logging.info('电机固件上传中')

                time.sleep(1.0)

                serialEsp32.write(b'firmware\n')
                data, size = self.read_file_and_get_size(self.resource_path(path+'/' + latest_file_stm))
                logging.info(f'File Size is : {size} bytes')

                serialEsp32.write((str(size) + '\n').encode('utf-8'))
                logging.info((str(size) + '\n').encode('utf-8'))

                md5_hash = self.get_md5(self.resource_path(path + '/' + latest_file_stm))
                logging.info(f'MD5 Hash is : {md5_hash}')
                logging.info((md5_hash + '\n').encode('utf-8'))
                serialEsp32.write((md5_hash + '\n').encode('utf-8'))

                time.sleep(0.5)

                newdatas = self.split_bytes(data, 4096)
                logging.info(len(newdatas))

                for newdata in newdatas:
                    serialEsp32.write(newdata)

                # serialEsp32.write(data)

                start_time = datetime.now()
                logging.info(f"starttime is : {start_time}")  # 使用f-string格式化字符串

                while True:
                    line = self.read_line(serialEsp32)
                    if line == b'':
                        time.sleep(0.1)
                    else:
                        logging.info(line)
                        if line == b'firmware ok\r\n':
                            logging.info('电机固件更新完成')
                            Flag = True
                            return Flag # exit会直接终止程序，后续break可删除
                        elif line == b'md5 match\r\n':
                            logging.info('电机固件更新中')
                        elif line == b'md5 not match\r\n':
                            logging.info('电机固件md5失败, 重试')
                            break

                    # 修正时间计算逻辑
                    elapsed_time = datetime.now() - start_time
                    if elapsed_time.total_seconds() > 120:  # 直接比较总秒数
                        logging.error("电机更新失败， 更新超時")
                        Flag = False  # 使用正确注释
        return Flag

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


    def burn(self, masterboard):

        Flag = True

        if self.burn_motor(masterboard):
            logging.info("电机烧录完成")
        else:
            logging.error("電機燒錄失敗")
            return False

        port = self.find_cp210_port()
        if not port:
            logging.error("未检测到 CP210x 设备，终止测试")
            assert False, "未找到 CP210x 设备"
            return False

        flasher = ESP32Flasher(port)

        directory_path = self.resource_path(masterboard)
        latest_file_esp = self.find_latest_version_file_esp(directory_path)
        STABLE_FIRMWARE_FILE_PATH = directory_path+rf'\{latest_file_esp}'
        logging.info(STABLE_FIRMWARE_FILE_PATH)

        try:
            download_success = flasher.flash_firmware(
                STABLE_FIRMWARE_FILE_PATH,
                STABLE_BOOTLOADER_FILE_PATH,
                STABLE_PARTITION_FILE_PATH,
                STABLE_OTA_DATA_INITIAL_PATH,
                port
            )
        except Exception as e:
            logging.error(f"主板烧录过程中发生异常: {str(e)}")
            download_success = False

        if download_success:
            logging.info("主板烧录成功")
            return True
        else:
            logging.error("主板烧录异常")
            return False


    def test_excetion(self, case_config):

        assert self.burn("release"), "Release 固件烧录失败"
        assert self.burn("base"), "base 固件烧录失败"



