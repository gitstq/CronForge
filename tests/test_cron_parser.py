"""
CronForge - Cron表达式解析器测试

测试Cron表达式解析、验证和下次执行时间计算。
"""

import unittest
from datetime import datetime

from cronforge.cron_parser import (
    CronExpression,
    CronParseError,
    validate_cron,
    parse_cron,
    get_next_times,
)


class TestCronExpressionParsing(unittest.TestCase):
    """测试Cron表达式解析"""

    def test_standard_five_fields(self):
        """测试标准5字段表达式解析"""
        cron = CronExpression("0 9 * * *")
        self.assertIn(0, cron.fields["minute"])
        self.assertIn(9, cron.fields["hour"])
        self.assertEqual(len(cron.fields["day"]), 31)  # 1-31
        self.assertEqual(len(cron.fields["month"]), 12)  # 1-12
        self.assertEqual(len(cron.fields["weekday"]), 7)  # 0-6

    def test_wildcard(self):
        """测试通配符 * """
        cron = CronExpression("* * * * *")
        self.assertEqual(len(cron.fields["minute"]), 60)
        self.assertEqual(len(cron.fields["hour"]), 24)
        self.assertEqual(len(cron.fields["day"]), 31)
        self.assertEqual(len(cron.fields["month"]), 12)
        self.assertEqual(len(cron.fields["weekday"]), 7)

    def test_comma_separated(self):
        """测试逗号分隔值"""
        cron = CronExpression("0,15,30,45 * * * *")
        self.assertEqual(cron.fields["minute"], {0, 15, 30, 45})

    def test_range(self):
        """测试范围值"""
        cron = CronExpression("0 9 * * 1-5")
        self.assertEqual(cron.fields["weekday"], {1, 2, 3, 4, 5})

    def test_step(self):
        """测试步长值"""
        cron = CronExpression("*/5 * * * *")
        self.assertEqual(cron.fields["minute"], {0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55})

    def test_range_with_step(self):
        """测试范围加步长"""
        cron = CronExpression("10-30/5 * * * *")
        self.assertEqual(cron.fields["minute"], {10, 15, 20, 25, 30})

    def test_special_alias_yearly(self):
        """测试 @yearly 别名"""
        cron = CronExpression("@yearly")
        self.assertEqual(cron.fields["minute"], {0})
        self.assertEqual(cron.fields["hour"], {0})
        self.assertEqual(cron.fields["day"], {1})
        self.assertEqual(cron.fields["month"], {1})

    def test_special_alias_monthly(self):
        """测试 @monthly 别名"""
        cron = CronExpression("@monthly")
        self.assertEqual(cron.fields["minute"], {0})
        self.assertEqual(cron.fields["hour"], {0})
        self.assertEqual(cron.fields["day"], {1})

    def test_special_alias_weekly(self):
        """测试 @weekly 别名"""
        cron = CronExpression("@weekly")
        self.assertEqual(cron.fields["minute"], {0})
        self.assertEqual(cron.fields["hour"], {0})
        self.assertEqual(cron.fields["weekday"], {0})

    def test_special_alias_daily(self):
        """测试 @daily 别名"""
        cron = CronExpression("@daily")
        self.assertEqual(cron.fields["minute"], {0})
        self.assertEqual(cron.fields["hour"], {0})

    def test_special_alias_hourly(self):
        """测试 @hourly 别名"""
        cron = CronExpression("@hourly")
        self.assertEqual(cron.fields["minute"], {0})

    def test_interval_seconds(self):
        """测试 @every_Ns 间隔"""
        cron = CronExpression("@every_30s")
        self.assertTrue(cron.is_interval)
        self.assertEqual(cron.interval_seconds, 30)

    def test_interval_minutes(self):
        """测试 @every_Nm 间隔"""
        cron = CronExpression("@every_5m")
        self.assertTrue(cron.is_interval)
        self.assertEqual(cron.interval_seconds, 300)

    def test_interval_hours(self):
        """测试 @every_Nh 间隔"""
        cron = CronExpression("@every_2h")
        self.assertTrue(cron.is_interval)
        self.assertEqual(cron.interval_seconds, 7200)

    def test_case_insensitive(self):
        """测试大小写不敏感"""
        cron1 = CronExpression("@Daily")
        cron2 = CronExpression("@daily")
        self.assertEqual(cron1.fields, cron2.fields)


class TestCronExpressionValidation(unittest.TestCase):
    """测试Cron表达式验证"""

    def test_valid_expressions(self):
        """测试合法表达式"""
        valid_exprs = [
            "0 9 * * *",
            "*/5 * * * *",
            "0,30 * * * *",
            "0 9 * * 1-5",
            "@daily",
            "@hourly",
            "@every_10s",
            "0 0 1 1 *",
            "0 0 31 12 *",
        ]
        for expr in valid_exprs:
            valid, error = validate_cron(expr)
            self.assertTrue(valid, f"表达式 '{expr}' 应该合法，但报错: {error}")

    def test_invalid_expressions(self):
        """测试非法表达式"""
        invalid_exprs = [
            "",           # 空字符串
            "0 9 *",      # 字段不足
            "0 9 * * * *", # 字段过多
            "60 * * * *",  # 分钟超出范围
            "0 25 * * *",  # 小时超出范围
            "0 0 32 * *",  # 日期超出范围
            "0 0 * 13 *",  # 月份超出范围
            "0 0 * * 8",   # 星期超出范围
        ]
        for expr in invalid_exprs:
            valid, error = validate_cron(expr)
            self.assertFalse(valid, f"表达式 '{expr}' 应该非法")

    def test_parse_cron_function(self):
        """测试 parse_cron 函数"""
        cron = parse_cron("0 9 * * *")
        self.assertIsInstance(cron, CronExpression)

    def test_parse_invalid_raises(self):
        """测试解析非法表达式抛出异常"""
        with self.assertRaises(CronParseError):
            parse_cron("invalid")


class TestCronNextTime(unittest.TestCase):
    """测试下次执行时间计算"""

    def test_next_time_basic(self):
        """测试基本下次执行时间"""
        cron = CronExpression("0 9 * * *")
        after = datetime(2024, 1, 1, 8, 0, 0)
        next_time = cron.next_time(after)
        self.assertEqual(next_time.hour, 9)
        self.assertEqual(next_time.minute, 0)

    def test_next_time_same_hour(self):
        """测试同小时内的时间"""
        cron = CronExpression("30 9 * * *")
        after = datetime(2024, 1, 1, 9, 0, 0)
        next_time = cron.next_time(after)
        self.assertEqual(next_time.hour, 9)
        self.assertEqual(next_time.minute, 30)
        self.assertEqual(next_time.day, 1)

    def test_next_time_next_day(self):
        """测试跨天"""
        cron = CronExpression("0 9 * * *")
        after = datetime(2024, 1, 1, 10, 0, 0)
        next_time = cron.next_time(after)
        self.assertEqual(next_time.day, 2)
        self.assertEqual(next_time.hour, 9)

    def test_next_time_weekday(self):
        """测试星期匹配"""
        # 每周一执行 (weekday=1)
        cron = CronExpression("0 9 * * 1")
        # 2024-01-01 是周一
        after = datetime(2024, 1, 1, 10, 0, 0)
        next_time = cron.next_time(after)
        # 下一个周一应该是 2024-01-08
        self.assertEqual(next_time.day, 8)

    def test_next_time_interval(self):
        """测试间隔类型"""
        cron = CronExpression("@every_60s")
        after = datetime(2024, 1, 1, 0, 0, 0)
        next_time = cron.next_time(after)
        self.assertEqual(next_time, datetime(2024, 1, 1, 0, 1, 0))

    def test_get_next_times(self):
        """测试获取多次执行时间"""
        times = get_next_times("0 * * * *", count=3, after=datetime(2024, 1, 1, 0, 0, 0))
        self.assertEqual(len(times), 3)
        self.assertEqual(times[0].hour, 1)
        self.assertEqual(times[1].hour, 2)
        self.assertEqual(times[2].hour, 3)

    def test_next_time_month_boundary(self):
        """测试月份边界"""
        cron = CronExpression("0 0 1 * *")
        after = datetime(2024, 1, 2, 0, 0, 0)
        next_time = cron.next_time(after)
        self.assertEqual(next_time.month, 2)
        self.assertEqual(next_time.day, 1)


class TestCronMatches(unittest.TestCase):
    """测试时间匹配"""

    def test_matches_basic(self):
        """测试基本匹配"""
        cron = CronExpression("30 9 * * *")
        dt = datetime(2024, 1, 1, 9, 30, 0)
        self.assertTrue(cron.matches(dt))

    def test_not_matches(self):
        """测试不匹配"""
        cron = CronExpression("30 9 * * *")
        dt = datetime(2024, 1, 1, 9, 31, 0)
        self.assertFalse(cron.matches(dt))

    def test_matches_wildcard(self):
        """测试通配符匹配"""
        cron = CronExpression("* * * * *")
        dt = datetime(2024, 6, 15, 14, 30, 0)
        self.assertTrue(cron.matches(dt))

    def test_matches_weekday(self):
        """测试星期匹配"""
        # 每周一 (weekday=1)
        cron = CronExpression("0 9 * * 1")
        # 2024-01-01 是周一
        dt_monday = datetime(2024, 1, 1, 9, 0, 0)
        self.assertTrue(cron.matches(dt_monday))
        # 2024-01-02 是周二
        dt_tuesday = datetime(2024, 1, 2, 9, 0, 0)
        self.assertFalse(cron.matches(dt_tuesday))


if __name__ == "__main__":
    unittest.main()
