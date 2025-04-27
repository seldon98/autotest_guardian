import logging

import allure
import pytest


class TestCase2:
    @pytest.mark.usefixtures("allure_metadata")
    def test_execution(self, case_config):
        self.run_test(case_config['loop'])

    @allure.step("执行支付测试")
    def run_test(self, iteration):
        with allure.step(f"第{iteration}次支付操作"):
            print(f"执行test_case_2的第{iteration}次迭代")
            allure.attach("交易数据", "金额: 100\n货币: CNY")
            if iteration % 2 ==0 :
                logging.error('case 2 test failed')
            assert iteration % 2 != 0  # 故意让偶数次迭代失败
