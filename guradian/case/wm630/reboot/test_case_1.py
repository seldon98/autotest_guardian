import allure
import pytest


class TestCase1:
    @pytest.mark.usefixtures("allure_metadata")
    def test_execution(self, case_config):
        self.run_test(case_config['loop'])

    @allure.step("执行测试逻辑")
    def run_test(self, iteration):
        with allure.step(f"第{iteration}次迭代"):
            print(f"执行test_case_1的第{iteration}次迭代")
            allure.attach("测试数据", "用户名: test1\n密码: 123456")
            assert True
