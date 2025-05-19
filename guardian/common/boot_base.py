import logging

import serial
import serial.tools.list_ports
import time
import esptool
from threading import Thread



class ESP32Flasher:
    port = None
    baudrate = 2000000

    def __init__(self, port, baudrate=2000000):
        self.port = port
        self.baudrate = baudrate

    def flash_firmware(self, firmware_path, bootloader_path, partition_table_path, ota_data_initial_path, PORT):
        result = [None]  # 用于存储结果的列表，因字符串是不可变的

        try:
            ser = serial.Serial(self.port)
            ser.close()
        except Exception as e:
            logging.error(f"关闭串口失败: {e}")

        def run_esptool():
            try:
                esptool.main([  # 传递参数列表
                    '--chip', 'esp32',
                    '--port', PORT,
                    '--baud', '2000000',
                    '--before', 'default_reset',
                    '--after', 'hard_reset',
                    'write_flash', '-z',
                    '--flash_mode', 'dio',
                    '--flash_freq', '80m',
                    '--flash_size', '8MB',
                    '0x1000', bootloader_path,
                    '0x8000', partition_table_path,
                    '0xe000', ota_data_initial_path,
                    '0x10000', firmware_path
                ])
                result[0] = True  # 表示成功
            except Exception as e:
                logging.error(f"固件烧录失败: {e}")
                result[0] = False  # 表示失败

        thread = Thread(target=run_esptool)
        start_time = time.time()  # 记录开始时间
        thread.start()
        thread.join()  # 等待线程完成
        end_time = time.time()  # 记录结束时间
        download_duration = end_time - start_time
        logging.info(f"固件下载时长: {download_duration:.2f} 秒")

        # 检查结果
        if result[0]:
            logging.info("固件烧录成功！")
        else:
            logging.error("固件烧录失败！")

        return result[0]  # 返回成功与否的状态