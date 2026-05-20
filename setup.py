"""
CronForge 安装配置

支持 pip install . 安装和 python -m cronforge 运行。
"""

from setuptools import setup, find_packages

setup(
    name="cronforge",
    version="1.0.0",
    description="轻量级跨平台定时任务调度与管理引擎",
    long_description=open("README.rst", encoding="utf-8").read() if __import__("os").path.exists("README.rst") else "",
    author="CronForge",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "cronforge=cronforge.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
        "Topic :: System :: Monitoring",
    ],
)
