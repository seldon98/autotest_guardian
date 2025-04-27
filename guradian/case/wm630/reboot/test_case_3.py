import time

import allure
import pytest
from common.CmdShell import CommandExecutor
import logging

class TestCase3:
    @pytest.mark.usefixtures("allure_metadata")
    def test_execution(self, case_config):
        self.cmd = CommandExecutor()

        if self.prepare():
            self.run_test()
        else:
            logging.error('test faile')
            assert False


    def prepare(self):
        output = str(self.cmd.cmd_shell('adb devices'))

        if '123456789ABCDEF' not in output:
            logging.error('not obtain devices')
            return False
        else:
            logging.info('obtain devices')
            return True


    @allure.step("执行搜索测试")
    def run_test(self):

        self.cmd.cmd_shell('adb devices')

        time.sleep(5)

        result = str(self.cmd.cmd_shell('adb devices'))

        if '123456789ABCDEF' not in result:
            logging.error('not obtain devices')
            assert False
