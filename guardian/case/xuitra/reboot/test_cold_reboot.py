import serial
import time
import logging

# 全局串口对象
ser = serial.Serial(
    port='COM6',
    baudrate=3000000,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=1
)

class TestColdReboot:

    def esp32_reset_by_dtr(self, ser):
        if not ser.is_open:
            ser.open()
        time.sleep(0.1)

        logging.info("Triggering reset via DTR...")
        ser.dtr = True
        time.sleep(0.1)
        ser.dtr = False
        time.sleep(0.1)

        logging.info("ESP32 has been reset.")

    def find_esp32(self):
        if not ser.is_open:
            ser.open()

        try:
            ser.write(b'Hello Device\n')
            time.sleep(0.5)
            response = ser.read_all()
            logging.info("收到数据:" )
            logging.info(response)
        except Exception as e:
            logging.error("通信出错:" + str(e))
        # 不关闭 ser，让下一个用例复用

    def test_execution(self, case_config):
        if not ser.is_open:
            ser.open()
        logging.info("串口已打开")

        self.esp32_reset_by_dtr(ser)
        time.sleep(1)
        self.find_esp32()
