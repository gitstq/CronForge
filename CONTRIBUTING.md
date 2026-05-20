# 贡献指南

感谢你对 CronForge 项目的关注！欢迎提交 Issue 和 Pull Request。

## 开发环境

1. 克隆仓库
```bash
git clone https://github.com/cronforge/cronforge.git
cd cronforge
```

2. 安装（开发模式）
```bash
pip install -e .
```

3. 运行测试
```bash
python -m pytest tests/
```

## 代码规范

- Python 3.8+ 语法
- 零外部依赖，仅使用标准库
- 添加类型注解
- 编写详细的中文 docstring
- 每个模块顶部添加模块说明

## 提交规范

- 使用清晰的提交信息
- 一个 PR 解决一个问题
- 确保所有测试通过

## 报告问题

请使用 GitHub Issues 提交问题，包含以下信息：

- 操作系统和 Python 版本
- 问题描述和复现步骤
- 期望行为和实际行为
