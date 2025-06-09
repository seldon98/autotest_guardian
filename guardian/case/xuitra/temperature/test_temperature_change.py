import serial
import time
import logging
import re
import matplotlib
matplotlib.use('Agg')  # 适配无图形界面环境
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os

# 初始化日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 串口配置
ser = serial.Serial(
    port='COM5',  # 根据实际修改
    baudrate=3000000,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1
)

class TestTemperatureChange:

    def send_command(self, command: str, wait_time: float = 2.0) -> str:
        """
        发送指令到串口，循环读取数据直到超时，确保返回完整数据。
        """
        try:
            if not ser.is_open:
                ser.open()
            full_cmd = command.strip().encode('utf-8') + b'\n'
            ser.write(full_cmd)
            logging.info(f"发送指令: {command}")

            response = ''
            start = time.time()
            while time.time() - start < wait_time:
                bytes_waiting = ser.in_waiting
                if bytes_waiting > 0:
                    chunk = ser.read(bytes_waiting).decode('utf-8', errors='ignore')
                    response += chunk
                time.sleep(0.05)
            logging.info(f"回包内容:\n{response.strip()}")
            return response
        except Exception as e:
            logging.error(f"发送指令异常: {e}")
            return ''

    def parse_extended_response(self, response: str) -> dict:
        """
        解析设备返回字符串，提取键值对，支持中英文键名，数值带单位（单位忽略）。
        """
        data = {}
        pattern = re.compile(r'([\w\u4e00-\u9fa5]+)\s*[:=]\s*(-?[\d\.]+)([a-zA-Z%]*)')
        for line in response.strip().splitlines():
            for match in pattern.finditer(line):
                key, value, _ = match.groups()
                try:
                    data[key.strip().lower()] = float(value)
                except ValueError:
                    data[key.strip().lower()] = value
        return data

    def plot_temperature_trend(self, timestamps: list, data: list[float], title: str, output_dir: str):
        """
        绘制趋势图，timestamps为datetime对象列表，data为数值列表。
        """
        if not data or not timestamps or len(data) != len(timestamps):
            logging.warning(f"{title} 数据与时间戳不匹配，无法绘图")
            return
        if all(np.isnan(d) for d in data):
            logging.warning(f"{title} 全部为空，跳过绘图")
            return

        plt.figure(figsize=(8, 4))
        plt.plot(timestamps, data, marker='o', linestyle='-', label=title.upper())
        plt.title(f'{title.upper()} 趋势图')
        plt.xlabel('时间')
        plt.ylabel(title.upper())
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()

        plt.gcf().autofmt_xdate()  # 自动格式化时间标签

        file_path = os.path.join(output_dir, f"{title.lower()}_trend.png")
        plt.savefig(file_path)
        plt.close()
        logging.info(f"{title.upper()} 曲线图保存至: {file_path}")

    def main_test(self, duration_seconds=60, sampling_interval=5):
        """
        主测试函数，持续采样duration_seconds秒，每隔sampling_interval秒采集一次数据。
        """
        try:
            if not ser.is_open:
                ser.open()

            # 所有key统一用小写
            collected_data = {
                'hyper': [], 'fitness': [], 'mode': [], 'vibration': [], 'temperature': [],
                'left_temperature': [], 'right_temperature': [], 'cell_temperature': [], 'fet_temperature': [],
                'all_step': [], 'all_h': [], 'hyper_state': [], 'battery_percentage': [],
            }

            timestamps = []

            start_time = time.time()
            while (time.time() - start_time) < duration_seconds:
                current_time = datetime.now()
                timestamps.append(current_time)

                raw_response = self.send_command('get_all', wait_time=2)
                parsed = self.parse_extended_response(raw_response)
                logging.info(f"当前采样数据: {parsed}")

                for key in collected_data:
                    value = parsed.get(key)
                    try:
                        collected_data[key].append(float(value) if value is not None else np.nan)
                    except Exception:
                        collected_data[key].append(np.nan)

                # 采样关键字段打印（调试用）
                logging.info(
                    f"采样时间: {current_time.strftime('%H:%M:%S')}, rawsoc: {parsed.get('rawsoc')}, soc: {parsed.get('soc')}")

                time.sleep(sampling_interval)

            ser.close()

            # 创建图像目录
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            output_dir = os.path.join('.', 'image', timestamp)
            os.makedirs(output_dir, exist_ok=True)
            logging.info(f"图像将保存至: {output_dir}")

            for key, values in collected_data.items():
                self.plot_temperature_trend(timestamps, values, title=key, output_dir=output_dir)

        except Exception as e:
            logging.error(f"测试执行异常: {e}")

    def test_execution(self, case_config=None):
        logging.info("开始执行测试")
        self.main_test(duration_seconds=20*60, sampling_interval=5)


