import uiautomator2 as u2
import time
from datetime import datetime, timedelta
import logging
import os

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# 指定目标路径（可以是绝对路径或相对路径）
target_path = rf"D:\Jenkins\SWS_Git\autotest_guardian\guardian\logs\screen\{timestamp}"  # 替换为你的路径

# 创建文件夹（如果路径中的父目录不存在，会自动创建）
os.makedirs(target_path, exist_ok=True)  # exist_ok=True 表示文件夹存在时不报错


class TestUpgrade:

    def enter_upgrade(self, d):
        # 点击 Hypershell 主入口
        time.sleep(5)
        d(description="Hypershell").click()
        time.sleep(3)

        # 点击坐标位置（建议改用百分比或元素定位）
        d.click(0.842, 0.183)  # 使用百分比更安全
        time.sleep(5)

        # 进入升级页面
        d(description="升级").click()
        time.sleep(3)


        if d(description="固件重刷确认").exists():
            d(description="重刷").click()
            time.sleep(3)
            d.swipe_ext("up")
            time.sleep(3)
            d(description="重刷").click()
            time.sleep(3)
            d(description="继续").click()
            time.sleep(3)
            d(description="升级").click()
        else:
            # 滑动操作
            d.swipe_ext("up")  # 确保设备支持此方法
            time.sleep(2)

            # 再次点击升级按钮
            d(description="升级").click()
            time.sleep(3)

            # 检查更新提示
            update_note = d(description="更新前请注意")
            if update_note.exists():  # 修正拼写错误
                d(description="继续").click()
                time.sleep(3)

            if d(description="固件重刷确认").exists():
                d(description="重刷").click()
                time.sleep(3)
                d.swipe_ext("up")
                time.sleep(3)
                d(description="继续").click()
                time.sleep(3)
                d(description="升级").click()

            if d(description="确定现在更新吗？").exists:
                d(description="升级").click()

        time.sleep(3)

        if d(description="请在手机上保持蓝牙开启,并在更新时保持应用在前台").exists():
            logging.info("Enter the upgrade")


    def safe_print_description(self,desc):
        """安全打印包含特殊字符的描述信息"""

        try:
            # 使用f-string避免格式化问题
            print(f"[{time.strftime('%H:%M:%S')}] Description: {desc}")
        except Exception as e:
            print(f"打印异常: {str(e)}")

    def monitor_view_descriptions(self, d, duration_minutes=10):
        """
        持续监控指定类名的元素描述
        :param d: uiautomator2设备实例
        :param duration_minutes: 监控持续时间（分钟）
        """
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        logging.info(f"开始监控，将持续到 {end_time.strftime('%H:%M:%S')}")

        while datetime.now() < end_time:
            try:
                # 获取所有目标元素（改用更精确的选择器）
                elements = d(className="android.view.View", packageName="com.hypershell.hypershell")

                if not elements.exists:
                    logging.info("未找到目标元素")
                    time.sleep(5)
                    continue

                # 遍历所有匹配元素
                for elem in elements:
                    desc = elem.info.get('contentDescription')

                    self.safe_print_description(desc)

                # 添加滚动检测（防止元素被遮挡）
                if not elements.exists:
                    print("检测到界面变化，尝试滚动...")
                    d.swipe(0.5, 0.8, 0.5, 0.2, 0.5)  # 从下往上滑动

                # 间隔时间可配置化
                time.sleep(2)  # 适当间隔避免高频请求

                if d(description="固件更新失败").exists():
                    return False

                if d(description="固件更新成功").exists():
                    logging.info("升级成功")
                    return True

            except u2.exceptions.UiAutomationNotConnectedError:
                print("设备连接丢失，尝试重连...")
                d = u2.connect('NAB0220730025203')  # 自动重连设备
                return False

        logging.error("upgrade timeout !")

        return False



    def test_execution(self, case_config):

        # 初始化设备连接
        d = u2.connect('NAB0220730025203')

        d.app_stop('com.hypershell.hypershell')

        # 确保应用运行状态
        if not d.app_wait("com.hypershell.hypershell", timeout=10):
            print("应用未启动，正在启动...")
            d.app_start('com.hypershell.hypershell')
            time.sleep(10)

        if d(description="取消").exists():
            d.screenshot(fr"D:\Jenkins\SWS_Git\autotest_guardian\guardian\logs\screen\{timestamp}\DetectAnomalies.jpg")  # 修正路径
            d(description="取消").click()
            print("已点击取消按钮")

        if d(description="充电中"):
            d(description="确认").click()

        self.enter_upgrade(d)


        if self.monitor_view_descriptions(d,duration_minutes=5):
            logging.info('upgrade success')
            d.screenshot(fr"D:\Jenkins\SWS_Git\autotest_guardian\guardian\logs\screen\{timestamp}\upgradeSuccesss.jpg")
        else:
            logging.error('upgrade faile')
            d.screenshot(fr"D:\Jenkins\SWS_Git\autotest_guardian\guardian\logs\screen\{timestamp}\pgradeFaile.jpg")
            assert  False