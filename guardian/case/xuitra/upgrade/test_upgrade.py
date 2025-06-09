import uiautomator2 as u2
from uiautomator2 import exceptions
import time
from datetime import datetime, timedelta
import logging
import os

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 时间戳 & 截图路径
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
target_path = os.path.join("E:\\Jenkins\\SWS_Git\\autotest_guardian\\guardian\\logs\\screen", timestamp)
os.makedirs(target_path, exist_ok=True)


class TestUpgrade:

    def safe_click(self, d, timeout=10, **selector):



        """等待并点击指定元素，失败则抛异常和截图"""
        if not d(**selector).wait(timeout=timeout):
            screenshot = os.path.join(target_path, f"element_not_found_{selector}.jpg")
            d.screenshot(screenshot)
            raise RuntimeError(f"元素未找到: {selector}")
        d(**selector).click()

    def enter_upgrade(self, d):
        time.sleep(5)

        # 等待页面稳定，通过等待目标元素
        if not d(description="debug 1").wait(timeout=10.0):
            raise RuntimeError("主入口元素 [debug 1] 未加载完成")

        self.safe_click(d, description="debug 1")
        time.sleep(3)

        d.click(0.842, 0.183)
        time.sleep(5)

        self.safe_click(d, description="升级")
        time.sleep(3)

        if d(description="固件重刷确认").exists():
            self.safe_click(d, description="重刷")
            time.sleep(3)
            d.swipe_ext("up")
            time.sleep(3)
            self.safe_click(d, description="重刷")
            time.sleep(3)
            self.safe_click(d, description="继续")
            time.sleep(3)
            self.safe_click(d, description="升级")
        else:
            d.swipe_ext("up")
            time.sleep(2)
            self.safe_click(d, description="升级")
            time.sleep(3)

            if d(description="更新前请注意").exists():
                self.safe_click(d, description="继续")
                time.sleep(3)

            if d(description="固件重刷确认").exists():
                self.safe_click(d, description="重刷")
                time.sleep(3)
                d.swipe_ext("up")
                time.sleep(3)
                self.safe_click(d, description="继续")
                time.sleep(3)
                self.safe_click(d, description="升级")

            if d(description="确定现在更新吗？").exists():
                self.safe_click(d, description="升级")

        time.sleep(3)

        if d(description="请在手机上保持蓝牙开启,并在更新时保持应用在前台").exists():
            logging.info("进入升级流程")

    def safe_print_description(self, desc):
        try:
            print(f"[{time.strftime('%H:%M:%S')}] Description: {desc}")
        except Exception as e:
            print(f"打印异常: {str(e)}")

    def monitor_view_descriptions(self, d, duration_minutes=10):
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        logging.info(f"开始监控，持续到 {end_time.strftime('%H:%M:%S')}")

        while datetime.now() < end_time:
            try:
                elements = d(className="android.view.View", packageName="com.hypershell.hypershell")

                if not elements.exists:
                    logging.info("未找到目标元素")
                    time.sleep(5)
                    continue

                for elem in elements:
                    try:
                        desc = elem.info.get('contentDescription')
                        self.safe_print_description(desc)
                    except uiautomator2.exceptions.UiObjectNotFoundError as e:
                        logging.warning(f"元素在获取信息时消失: {e}")
                        continue  # 跳过当前元素，继续下一个

                # 检查升级失败或成功
                if d(description="固件更新失败").exists():
                    logging.error("检测到固件更新失败")
                    d.screenshot(os.path.join(target_path, "upgrade_error.jpg"))
                    return False

                if d(description="固件更新成功").exists():
                    logging.info("升级成功")
                    return True

                time.sleep(2)

            except Exception as e:
                # 如果是UiObjectNotFoundError，我们已经在内部处理了，所以这里捕获的是其他异常
                logging.exception(f"测试执行失败: {e}")
                # 检查是否为设备连接问题
                if isinstance(e, (uiautomator2.exceptions.GatewayError, uiautomator2.exceptions.JsonRpcError)):
                    logging.warning("设备连接丢失，尝试重连...")
                    try:
                        # 尝试重新连接
                        d = u2.connect('5200f7b052f035bb')
                    except Exception as e2:
                        logging.error(f"重连失败: {e2}")
                    return False
                else:
                    # 其他异常，我们记录并继续监控（除非是严重错误）
                    # 但为了安全，我们这里返回False，因为未知异常可能导致后续监控无效
                    logging.error("遇到未处理的异常，终止监控")
                    return False

        logging.error("升级过程超时")
        return False

    def test_execution(self, case_config):
        try:
            d = u2.connect('5200f7b052f035bb')

            d.app_stop('com.hypershell.hypershell')
            if not d.app_wait("com.hypershell.hypershell", timeout=10):
                logging.info("应用未启动，正在启动...")
                d.app_start('com.hypershell.hypershell')
                time.sleep(15)

            if d(description="取消").exists():
                d.screenshot(os.path.join(target_path, "DetectAnomalies.jpg"))
                d(description="取消").click()
                logging.info("已点击取消按钮")

            if d(description="充电/放电中").exists():
                d(description="确认").click()

            self.enter_upgrade(d)

            if self.monitor_view_descriptions(d, duration_minutes=10):
                logging.info('升级成功')
                d.screenshot(os.path.join(target_path, "upgradeSuccess.jpg"))
            else:
                logging.error('升级失败')
                d.screenshot(os.path.join(target_path, "upgradeFail.jpg"))
                assert False

        except Exception as e:
            logging.exception(f"测试执行失败: {e}")
            d.screenshot(os.path.join(target_path, "unexpected_error.jpg"))