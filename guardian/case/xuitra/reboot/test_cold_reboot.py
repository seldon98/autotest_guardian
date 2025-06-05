import serial
import time
import logging

# 初始化日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 全局串口对象
ser = serial.Serial(
    port='COM14',
    baudrate=3000000,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1
)

class TestColdReboot:

    def esp32_reset_by_dtr(self):
        try:
            if not ser.is_open:
                ser.open()
            time.sleep(0.1)

            logging.info("Triggering ESP32 reset via DTR/RTS...")

            # 清空缓冲区
            ser.reset_input_buffer()

            # 先强制进入下载模式（拉低 EN 和 IO0）
            ser.dtr = True  # DTR = 1 → EN = LOW（复位）
            ser.rts = True  # RTS = 1 → IO0 = LOW（进入下载模式）
            time.sleep(0.1)

            # 然后释放 EN（EN = HIGH），但保持 IO0 = LOW
            ser.dtr = False  # DTR = 0 → EN = HIGH（复位释放）
            time.sleep(2)

            # 再释放 IO0（IO0 = HIGH），进入正常运行
            ser.rts = False  # RTS = 0 → IO0 = HIGH
            time.sleep(2)

            logging.info("ESP32 reset released.")
        except Exception as e:
            logging.error(f"ESP32 reset failed: {e}")
            assert False

    def send_command(self, command: str, wait_time: float = 2.0) -> str:
        try:
            """
                    向 ESP32 发送命令，等待固定时间后读取回包。
                    :param command: 要发送的命令字符串
                    :param wait_time: 发送后等待的秒数（默认 2 秒）
                    """
            if not ser.is_open:
                ser.open()

            full_cmd = command.strip().encode('utf-8') + b'\n'
            ser.write(full_cmd)
            logging.info(f"发送指令: {command}")

            # ⏱️ 等待一段时间再读取串口内容
            time.sleep(wait_time)

            response = ser.read_all().decode('utf-8', errors='ignore')
            logging.info(f"回包内容:\n{response}")
            return response
        except  Exception as e:
            logging.error(f"发送指令异常: {e}")
            assert False

    def find_esp32(self):
        try:
            """
                    按顺序发送一组指令并记录每条回包
                    """
            commands = ['lf', 'p 12', 's', 'd', 'clear']
            for cmd in commands:
                self.send_command(cmd, 2.0)
        except Exception as e:
            logging.error(f"查找 ESP32 指令异常: {e}")
            assert False

    def read_boot_log(self, duration=3):
        try:
            if not ser.is_open:
                ser.open()
            logging.info("开始读取启动日志...")
            ser.reset_input_buffer()

            start_time = time.time()
            boot_log = b''

            while time.time() - start_time < duration:
                data = ser.read_all()
                if data:
                    boot_log += data
                time.sleep(0.1)

            decoded = boot_log.decode('utf-8', errors='ignore')
            logging.info("启动日志如下：\n" + decoded)
            return decoded
        except Exception as e:
            logging.error(f"读取启动日志异常: {e}")
            assert False

    def test_execution(self, case_config=None):

        try:
            if not ser.is_open:
                ser.open()


            logging.info("开始测试...")
            ser.reset_input_buffer()

            self.esp32_reset_by_dtr()
            self.read_boot_log(duration=3)
            self.find_esp32()
            ser.close()

        except Exception as e:
            logging.error(f"测试执行异常: {e}")
            assert False

        time.sleep(5)
