import uiautomator2 as u2
import time
from datetime import datetime, timedelta
import logging
import os

# 配置统一时间戳和路径
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
target_path = os.path.join("E:", "Jenkins", "SWS_Git", "autotest_guardian",
                           "guardian", "logs", "screen", timestamp)
os.makedirs(target_path, exist_ok=True)

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(target_path, "execution.log")),
        logging.StreamHandler()
    ]
)


class TestBluetoothConnect:

    def disconnect(self, d):
        try:
            time.sleep(5)
            d(description="number 2").click()
            time.sleep(3)
        except Exception as e:
            d.screenshot(os.path.join(target_path, "Main_entrance_exception.jpg"))
            logging.info(f"Error clicking Hypershell entrance: {e}")

        try:
            d.click(0.842, 0.183)
            time.sleep(2)
        except Exception as e:
            d.screenshot(os.path.join(target_path, "enter_devices_failed.jpg"))
            print(f"Error clicking coordinates: {e}")

        try:
            elements = d(className="android.view.View", index="8")
            if elements.exists():
                elements.click()
                time.sleep(2)
        except Exception as e:
            d.screenshot(os.path.join(target_path, "unbinding1.jpg"))
            print(f"Error handling dynamic elements: {e}")

        try:
            if d(description="解绑").exists():
                d(description="解绑").click()
                time.sleep(5)
                logging.info('设备解绑完成')
        except Exception as e:
            d.screenshot(os.path.join(target_path, "unbinding2.jpg"))
            print(f"Error during unbinding: {e}")

    def connet(self, d):
        try:
            if not d(description="搜寻设备").exists(timeout=5):
                logging.warning("未找到'搜寻设备'入口")
                d.screenshot(os.path.join(target_path, "Search_devices_failed.jpg"))
                return False

            d(description="搜寻设备").click()
            time.sleep(5)

            start_time = datetime.now()
            timeout = 30

            while (datetime.now() - start_time).total_seconds() < timeout:
                parent = d(description="number 2")  # 动态获取父节点
                if not parent.exists(): continue  # 增加存在性检查

                icon = parent.child(
                    className="android.widget.ImageView",
                    instance=2
                )
                try:
                    for _ in range(3):
                        try:
                            icon.click()
                            break
                        except Exception as e:
                            logging.warning(f"点击失败，重试 {_ + 1}/3")
                            d.screenshot(os.path.join(target_path, "Click_Connect_failed.jpg"))
                            time.sleep(1)

                    if d(description="重新检测").wait(timeout=10):
                        d(description="取消").click()
                        logging.info("connect success!")
                        return True

                    if d(description="充电中").wait(timeout=10):
                        d(description="确认").click()
                        logging.info("connect success!")
                        return True

                    if d(description="number 2").exists():
                        return True

                except Exception as e:
                    logging.error(f"连接过程异常: {str(e)}")
                    d.screenshot(os.path.join(target_path, "connection_error.jpg"))

                time.sleep(1)
            return False
        except Exception as e:
            d.screenshot(os.path.join(target_path, "connet_exception.jpg"))
            logging.error(f"连接主流程异常: {str(e)}")
            return False

    def init_prepare(self,d):

        logging.info("重新启动app")
        d.app_stop('com.hypershell.hypershell')
        time.sleep(3)
        d.app_start('com.hypershell.hypershell')
        time.sleep(5)

        logging.info("关闭毛刺提示")

        if d(description="取消").exists():
            d.screenshot(
                fr"E:\Jenkins\SWS_Git\autotest_guardian\guardian\logs\screen\{timestamp}\DetectAnomalies.jpg")  # 修正路径
            d(description="取消").click()
            print("已点击取消按钮")

        if d(description="充电中"):
            d(description="确认").click()


    def test_execution(self):
        d = u2.connect("NAB0220730025203")

        self.init_prepare(d)

        logging.info("开始执行解绑流程")
        time.sleep(5)

        self.disconnect(d)

        self.init_prepare(d)

        logging.info("开始执行连接流程")
        time.sleep(5)
        result = self.connet(d)

        logging.info(f"测试执行结果: {'成功' if result else '失败'}")
        return result


