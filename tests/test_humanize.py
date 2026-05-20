"""
CronForge - Cron人类可读翻译测试

测试Cron表达式到人类可读描述的翻译功能。
"""

import unittest

from cronforge.humanize import humanize_cron


class TestHumanizeCN(unittest.TestCase):
    """测试中文翻译"""

    def test_every_minute(self):
        """测试每分钟"""
        result = humanize_cron("* * * * *", "cn")
        self.assertIn("每分钟", result)

    def test_specific_time_daily(self):
        """测试每天特定时间"""
        result = humanize_cron("0 9 * * *", "cn")
        self.assertIn("9", result)
        self.assertIn("每天", result)

    def test_weekday_range(self):
        """测试工作日"""
        result = humanize_cron("0 9 * * 1-5", "cn")
        self.assertIn("周一", result)
        self.assertIn("周五", result)

    def test_specific_weekday(self):
        """测试特定星期"""
        result = humanize_cron("0 9 * * 1", "cn")
        self.assertIn("周一", result)

    def test_step_minutes(self):
        """测试步长分钟"""
        result = humanize_cron("*/5 * * * *", "cn")
        self.assertIsNotNone(result)

    def test_monthly(self):
        """测试每月"""
        result = humanize_cron("0 0 1 * *", "cn")
        self.assertIn("1日", result)

    def test_yearly(self):
        """测试每年"""
        result = humanize_cron("0 0 1 1 *", "cn")
        self.assertIsNotNone(result)

    def test_alias_daily(self):
        """测试 @daily 别名"""
        result = humanize_cron("@daily", "cn")
        self.assertIn("每天", result)

    def test_alias_hourly(self):
        """测试 @hourly 别名"""
        result = humanize_cron("@hourly", "cn")
        self.assertIn("每小时", result)

    def test_alias_monthly(self):
        """测试 @monthly 别名"""
        result = humanize_cron("@monthly", "cn")
        self.assertIn("每月", result)

    def test_alias_weekly(self):
        """测试 @weekly 别名"""
        result = humanize_cron("@weekly", "cn")
        self.assertIn("每周", result)

    def test_alias_yearly(self):
        """测试 @yearly 别名"""
        result = humanize_cron("@yearly", "cn")
        self.assertIn("每年", result)

    def test_interval_seconds(self):
        """测试秒间隔"""
        result = humanize_cron("@every_30s", "cn")
        self.assertIn("30", result)
        self.assertIn("秒", result)

    def test_interval_minutes(self):
        """测试分钟间隔"""
        result = humanize_cron("@every_5m", "cn")
        self.assertIn("5", result)
        self.assertIn("分钟", result)

    def test_interval_hours(self):
        """测试小时间隔"""
        result = humanize_cron("@every_2h", "cn")
        self.assertIn("2", result)
        self.assertIn("小时", result)

    def test_afternoon_time(self):
        """测试下午时间"""
        result = humanize_cron("0 14 * * *", "cn")
        self.assertIn("下午", result)

    def test_midnight(self):
        """测试午夜"""
        result = humanize_cron("0 0 * * *", "cn")
        self.assertIn("午夜", result)

    def test_noon(self):
        """测试中午"""
        result = humanize_cron("0 12 * * *", "cn")
        self.assertIn("中午", result)

    def test_multiple_weekdays(self):
        """测试多个星期"""
        result = humanize_cron("0 9 * * 1,3,5", "cn")
        self.assertIn("周一", result)
        self.assertIn("周三", result)
        self.assertIn("周五", result)


class TestHumanizeEN(unittest.TestCase):
    """测试英文翻译"""

    def test_every_minute(self):
        """测试每分钟"""
        result = humanize_cron("* * * * *", "en")
        self.assertIn("Every minute", result)

    def test_specific_time(self):
        """测试特定时间"""
        result = humanize_cron("0 9 * * *", "en")
        self.assertIn("9:00", result)
        self.assertIn("AM", result)

    def test_afternoon_time(self):
        """测试下午时间"""
        result = humanize_cron("0 14 * * *", "en")
        self.assertIn("2:00", result)
        self.assertIn("PM", result)

    def test_weekday(self):
        """测试星期"""
        result = humanize_cron("0 9 * * 1", "en")
        self.assertIn("Monday", result)

    def test_alias_daily(self):
        """测试 @daily 别名"""
        result = humanize_cron("@daily", "en")
        self.assertIn("midnight", result.lower())

    def test_alias_hourly(self):
        """测试 @hourly 别名"""
        result = humanize_cron("@hourly", "en")
        self.assertIn("hour", result)

    def test_interval(self):
        """测试间隔"""
        result = humanize_cron("@every_30s", "en")
        self.assertIn("30", result)

    def test_invalid_expression(self):
        """测试无效表达式"""
        result = humanize_cron("invalid expr", "cn")
        self.assertIn("无法解析", result)


class TestHumanizeEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def test_multiple_hours(self):
        """测试多个小时"""
        result = humanize_cron("0 9,17 * * *", "cn")
        self.assertIsNotNone(result)

    def test_step_hours(self):
        """测试步长小时"""
        result = humanize_cron("0 */2 * * *", "cn")
        self.assertIsNotNone(result)

    def test_specific_day_and_month(self):
        """测试特定日期和月份"""
        result = humanize_cron("0 0 15 6 *", "cn")
        self.assertIsNotNone(result)

    def test_all_weekdays(self):
        """测试所有星期"""
        result = humanize_cron("0 9 * * 0-6", "cn")
        # 0-6 是所有星期，应该不显示星期描述
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
