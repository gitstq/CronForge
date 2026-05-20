"""
CronForge - 配置管理测试

测试YAML配置加载、保存和模板创建。
"""

import unittest
import os
import tempfile
import shutil

from cronforge.config import Config, SimpleYAMLParser
from cronforge.task import Task


class TestSimpleYAMLParser(unittest.TestCase):
    """测试简易YAML解析器"""

    def setUp(self):
        """测试初始化"""
        self.parser = SimpleYAMLParser()

    def test_parse_simple_key_value(self):
        """测试简单键值对解析"""
        yaml_text = """
name: test
value: 123
enabled: true
"""
        result = self.parser.parse(yaml_text)
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["value"], 123)
        self.assertTrue(result["enabled"])

    def test_parse_nested_dict(self):
        """测试嵌套字典解析"""
        yaml_text = """
global:
  timezone: local
  timeout: 3600
"""
        result = self.parser.parse(yaml_text)
        self.assertIn("global", result)
        self.assertEqual(result["global"]["timezone"], "local")
        self.assertEqual(result["global"]["timeout"], 3600)

    def test_parse_list(self):
        """测试列表解析"""
        yaml_text = """
items:
  - one
  - two
  - three
"""
        result = self.parser.parse(yaml_text)
        self.assertIn("items", result)
        self.assertEqual(result["items"], ["one", "two", "three"])

    def test_parse_list_of_dicts(self):
        """测试字典列表解析"""
        yaml_text = """
tasks:
  - name: task1
    command: echo 1
    cron_expr: "* * * * *"
  - name: task2
    command: echo 2
    cron_expr: "@hourly"
"""
        result = self.parser.parse(yaml_text)
        self.assertIn("tasks", result)
        self.assertEqual(len(result["tasks"]), 2)
        self.assertEqual(result["tasks"][0]["name"], "task1")
        self.assertEqual(result["tasks"][1]["name"], "task2")

    def test_parse_boolean_values(self):
        """测试布尔值解析"""
        yaml_text = """
true_val: true
false_val: false
yes_val: yes
no_val: no
"""
        result = self.parser.parse(yaml_text)
        self.assertTrue(result["true_val"])
        self.assertFalse(result["false_val"])
        self.assertTrue(result["yes_val"])
        self.assertFalse(result["no_val"])

    def test_parse_null_values(self):
        """测试空值解析"""
        yaml_text = """
null_val: null
tilde_val: ~
empty_val:
"""
        result = self.parser.parse(yaml_text)
        self.assertIsNone(result["null_val"])
        self.assertIsNone(result["tilde_val"])

    def test_parse_quoted_strings(self):
        """测试引号字符串"""
        yaml_text = """
single: 'hello world'
double: "hello world"
"""
        result = self.parser.parse(yaml_text)
        self.assertEqual(result["single"], "hello world")
        self.assertEqual(result["double"], "hello world")

    def test_parse_comments(self):
        """测试注释"""
        yaml_text = """
# 这是注释
name: test  # 行内注释
# 另一个注释
value: 42
"""
        result = self.parser.parse(yaml_text)
        self.assertEqual(result["name"], "test")
        self.assertEqual(result["value"], 42)

    def test_parse_float(self):
        """测试浮点数"""
        yaml_text = """
ratio: 3.14
"""
        result = self.parser.parse(yaml_text)
        self.assertAlmostEqual(result["ratio"], 3.14)

    def test_dump_dict(self):
        """测试字典序列化"""
        data = {
            "name": "test",
            "value": 42,
            "enabled": True,
        }
        result = self.parser.dump(data)
        self.assertIn("name: test", result)
        self.assertIn("value: 42", result)
        self.assertIn("enabled: true", result)


class TestConfigLoad(unittest.TestCase):
    """测试配置加载"""

    def setUp(self):
        """测试初始化"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "cronforge.yaml")

    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)

    def test_load_config_file(self):
        """测试加载配置文件"""
        config_content = """
global:
  timezone: local
  default_timeout: 1800

tasks:
  - name: test-task
    command: echo hello
    cron_expr: "0 9 * * *"
    enabled: true
    tags:
      - test
    description: 测试任务
"""
        with open(self.config_path, "w") as f:
            f.write(config_content)

        config = Config()
        config.load(self.config_path)

        self.assertEqual(len(config.tasks), 1)
        self.assertEqual(config.tasks[0].name, "test-task")
        self.assertEqual(config.tasks[0].command, "echo hello")
        self.assertEqual(config.tasks[0].cron_expr, "0 9 * * *")
        self.assertTrue(config.tasks[0].enabled)

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        config = Config()
        with self.assertRaises(FileNotFoundError):
            config.load("/nonexistent/path/config.yaml")

    def test_global_config_defaults(self):
        """测试全局配置默认值"""
        config = Config()
        self.assertEqual(config.global_config["timezone"], "local")
        self.assertEqual(config.global_config["default_timeout"], 3600)

    def test_get_task(self):
        """测试按名称获取任务"""
        config_content = """
tasks:
  - name: task1
    command: echo 1
    cron_expr: "* * * * *"
  - name: task2
    command: echo 2
    cron_expr: "@hourly"
"""
        with open(self.config_path, "w") as f:
            f.write(config_content)

        config = Config()
        config.load(self.config_path)

        task = config.get_task("task1")
        self.assertIsNotNone(task)
        self.assertEqual(task.name, "task1")

        self.assertIsNone(config.get_task("nonexistent"))

    def test_add_and_remove_task(self):
        """测试添加和移除任务"""
        config = Config()
        task = Task(
            name="new-task",
            command="echo new",
            cron_expr="@daily",
        )
        config.add_task(task)
        self.assertEqual(len(config.tasks), 1)
        self.assertEqual(config.tasks[0].name, "new-task")

        config.remove_task("new-task")
        self.assertEqual(len(config.tasks), 0)

    def test_remove_nonexistent_task(self):
        """测试移除不存在的任务"""
        config = Config()
        self.assertFalse(config.remove_task("nonexistent"))


class TestConfigSave(unittest.TestCase):
    """测试配置保存"""

    def setUp(self):
        """测试初始化"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "cronforge.yaml")

    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)

    def test_save_and_reload(self):
        """测试保存和重新加载"""
        config = Config()
        task = Task(
            name="save-test",
            command="echo saved",
            cron_expr="0 9 * * *",
            timeout=300,
            tags=["save"],
            description="保存测试",
        )
        config.add_task(task)
        config.save(self.config_path)

        # 重新加载
        config2 = Config()
        config2.load(self.config_path)

        self.assertEqual(len(config2.tasks), 1)
        self.assertEqual(config2.tasks[0].name, "save-test")
        self.assertEqual(config2.tasks[0].command, "echo saved")


class TestConfigTemplate(unittest.TestCase):
    """测试配置模板"""

    def setUp(self):
        """测试初始化"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)

    def test_create_template(self):
        """测试创建配置模板"""
        config = Config()
        path = os.path.join(self.temp_dir, "cronforge.yaml")
        created_path = config.create_template(path)

        self.assertTrue(os.path.exists(created_path))

        # 验证模板可以被加载
        config2 = Config()
        config2.load(created_path)
        self.assertGreater(len(config2.tasks), 0)

    def test_template_contains_example_tasks(self):
        """测试模板包含示例任务"""
        config = Config()
        path = os.path.join(self.temp_dir, "cronforge.yaml")
        config.create_template(path)

        config2 = Config()
        config2.load(path)

        task_names = [t.name for t in config2.tasks]
        self.assertIn("daily-report", task_names)
        self.assertIn("health-check", task_names)


if __name__ == "__main__":
    unittest.main()
