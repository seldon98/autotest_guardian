import pytest
import allure
import time


@allure.feature("串口通信测试")
class TestSerialCommunication:
    @allure.story("AT指令基础测试")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_at_command_basic(self, case_config, serial_connection):
        """
        测试发送AT指令并验证响应
        """
        # 从case_config获取测试信息
        test_name = case_config['name']
        loop_num = case_config['loop']

        # Allure动态标题
        allure.dynamic.title(f"{test_name} - Loop {loop_num}")

        # 测试步骤
        with allure.step("准备测试数据"):
            test_command = b"AT\r\n"  # 要发送的指令
            expected_response = b"OK"  # 预期响应

        with allure.step("清空串口缓冲区"):
            serial_connection.reset_input_buffer()
            serial_connection.reset_output_buffer()

        with allure.step(f"发送指令: {test_command.decode().strip()}"):
            serial_connection.write(test_command)
            allure.attach(
                test_command.decode(),
                name="Sent Command",
                attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("等待并读取响应"):
            time.sleep(0.5)  # 等待响应
            response = serial_connection.read_all()
            decoded_response = response.decode(errors='replace').strip()

            allure.attach(
                decoded_response,
                name="Received Response",
                attachment_type=allure.attachment_type.TEXT
            )

        with allure.step("验证响应"):
            assert expected_response in response, \
                f"预期包含 {expected_response!r}，实际收到 {response!r}"

    @allure.story("自定义指令测试")
    def test_custom_command(self, serial_connection):
        """
        测试设备特定指令（示例）
        """
        with allure.step("发送设备重启指令"):
            cmd = b"AT+REBOOT\r\n"
            serial_connection.write(cmd)

        with allure.step("验证设备响应"):
            time.sleep(1)  # 等待设备响应
            response = serial_connection.read_all()

            assert b"Rebooting" in response, \
                "未收到重启确认响应"
