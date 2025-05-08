import uiautomator2 as u2
import time
from datetime import datetime, timedelta
import logging

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

class TestUpgrade:

    def enter_upgrade(self, d):
        # 点击 Hypershell 主入口
        d(description="Hypershell").click()
        time.sleep(3)

        # 点击坐标位置（建议改用百分比或元素定位）
        d.click(0.842, 0.183)  # 使用百分比更安全
        time.sleep(3)

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



        if d(description="请在手机上保持蓝牙开启,并在更新时保持应用在前台").exists():
            print("Enter the upgrade")
        else:
            print("Upgrade exception")
            d.screenshot(f"upgradeFaile_{timestamp}.jpg")
            d.screenshot(fr"E:\Jenkins\SWS_Git\guardian\logs\screen\upgradeFaile1_{timestamp}.jpg")  # 修正路径

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
        print(f"开始监控，将持续到 {end_time.strftime('%H:%M:%S')}")

        while datetime.now() < end_time:
            try:
                # 获取所有目标元素（改用更精确的选择器）
                elements = d(className="android.view.View", packageName="com.hypershell.hypershell")

                if not elements.exists:
                    print("未找到目标元素")
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
                time.sleep(3)  # 适当间隔避免高频请求

                if d(description="固件更新失败").exists():
                    d.screenshot(f"upgradeFaile2_{timestamp}.png")
                    d.screenshot(fr"E:\Jenkins\SWS_Git\guardian\logs\screen\upgradeFaile2_{timestamp}.jpg")
                    return False

                if d(description="固件更新成功").exists():
                    logging.info("升级成功")
                    d.screenshot(f"upgradeSuccess_{timestamp}.png")
                    d.screenshot(fr"E:\Jenkins\SWS_Git\guardian\logs\screen\upgradeSuccesss_{timestamp}.jpg")
                    return False

            except u2.exceptions.UiAutomationNotConnectedError:
                print("设备连接丢失，尝试重连...")
                d = u2.connect('NAB0220730025203')  # 自动重连设备
            except Exception as e:
                print(f"监控异常: {str(e)}")
                time.sleep(5)

        print("监控周期结束")




    def test_execution(self, case_config):

        # 初始化设备连接
        d = u2.connect('NAB0220730025203')

        d.app_stop('com.hypershell.hypershell')

        # 确保应用运行状态
        if not d.app_wait("com.hypershell.hypershell", timeout=10):
            print("应用未启动，正在启动...")
            d.app_start('com.hypershell.hypershell')
            time.sleep(10)

        # 通过描述文本定位取消按钮
        cancel_button = d(description="取消")

        if cancel_button.exists():
            d.screenshot(f"DetectAnomalies_{timestamp}.png")
            d.screenshot(fr"E:\Jenkins\SWS_Git\guardian\logs\screen\DetectAnomalies_{timestamp}.jpg")  # 修正路径
            cancel_button.click()
            print("已点击取消按钮")
        else:
            print("未找到取消按钮")

        if d(description="充电中"):
            d(description="确认").click()

        self.enter_upgrade(d)


        if self.monitor_view_descriptions(d,duration_minutes=10):
            logging.info('upgrade success')
        else:
            logging.error('upgrade faile')
            assert  False