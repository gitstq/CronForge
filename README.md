[简体中文](#简体中文) | [繁體中文](#繁體中文) | [English](#english)

---

<h1 align="center">
  ⚒️ CronForge
</h1>

<p align="center">
  <strong>轻量级跨平台定时任务调度与管理引擎 CLI</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/零依赖-纯标准库-green.svg" alt="零依赖">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/tests-97%20passed-brightgreen.svg" alt="97 Tests">
</p>

---

## 简体中文

### 🎉 项目介绍

**CronForge** 是一款轻量级、跨平台的定时任务调度与管理引擎，以命令行工具（CLI）的形式交付。它面向需要在本地或服务器环境中管理周期性任务的开发者和运维人员，提供从任务定义、调度执行到日志审计的一站式解决方案。

**我们解决的核心痛点：**

- 传统 `crontab` 仅限 Unix/Linux 平台，Windows 用户难以使用
- 原生 cron 缺乏可视化界面，任务状态难以直观掌握
- 日志分散、缺乏结构化管理，排查问题费时费力
- 任务配置与系统强耦合，难以在不同环境间迁移

**差异化亮点：**

- **纯 Python 零依赖** —— 仅使用标准库，`pip install` 即装即用，无需解决任何依赖冲突
- **内置 TUI Dashboard** —— 基于 curses 的终端面板，实时查看任务状态，不支持 curses 时自动降级为纯文本模式
- **人类可读 Cron 翻译** —— 将晦涩的 Cron 表达式翻译为自然语言（中文/英文），降低阅读门槛
- **SQLite 结构化日志** —— 轻量级本地存储，支持查询、统计和自动清理

**灵感来源：** 本项目的设计参考了 [Cronboard](https://github.com/cronboard/cronboard)、[CronTUI](https://github.com/nickthecook/crontui)、[Pycroner](https://github.com/fabiocaccamo/python-croner) 等优秀开源项目的理念，在此基础上追求零依赖、跨平台和开发者友好的极致体验。

---

### ✨ 核心特性

| 特性 | 说明 |
|:-----|:-----|
| ⏰ **完整 Cron 表达式解析** | 标准 5 字段（分 时 日 月 周）+ `@yearly`/`@daily` 等别名 + `@every_30m` 固定间隔语法 |
| 📋 **YAML 驱动配置** | 声明式定义任务，支持超时、重试、标签、描述等丰富字段 |
| 🖥️ **curses TUI Dashboard** | 交互式终端面板，实时展示任务状态与下次执行时间，不支持 curses 时自动降级为纯文本 |
| 🔄 **任务执行器** | subprocess 执行 + 超时控制 + 指数退避重试机制 |
| 📊 **SQLite 执行日志** | 结构化存储执行记录，支持查询、统计和按时间清理 |
| 🔔 **Webhook 通知** | HTTP POST 通知，可按任务成功/失败事件触发 |
| 🌍 **人类可读 Cron 翻译** | 将 Cron 表达式翻译为中文或英文自然语言描述 |
| 🚀 **零外部依赖** | 仅使用 Python 标准库，无任何第三方依赖 |
| 💻 **跨平台支持** | Windows / macOS / Linux 全平台兼容 |
| 🧪 **97 个单元测试** | 完善的测试覆盖，保障代码质量 |

---

### 🚀 快速开始

#### 环境要求

- Python 3.8 或更高版本

#### 安装

```bash
# 通过 pip 直接从 GitHub 安装
pip install git+https://github.com/gitstq/CronForge.git

# 或克隆仓库后本地安装
git clone https://github.com/gitstq/CronForge.git
cd CronForge
pip install .
```

#### 初始化配置

```bash
cronforge init
```

该命令会在当前目录生成 `cronforge.yaml` 配置文件模板。

#### 启动调度器

```bash
cronforge start          # 后台运行
cronforge start --tui    # TUI 面板模式（交互式终端界面）
```

---

### 📖 详细使用指南

#### 配置文件示例

编辑 `cronforge.yaml` 定义你的定时任务：

```yaml
tasks:
  - name: backup
    command: python backup.py
    cron: "0 2 * * *"
    timeout: 300
    retries: 3
    retry_delay: 60
    enabled: true
    tags: [backup, daily]
    description: "每日凌晨2点执行数据库备份"

  - name: cleanup
    command: rm -rf /tmp/old_*
    cron: "@daily"
    timeout: 60
    retries: 1
    enabled: true

notifications:
  webhook:
    url: "https://hooks.example.com/cronforge"
    on_success: false
    on_failure: true

logging:
  max_entries: 10000
  cleanup_days: 30
```

#### CLI 子命令一览

| 命令 | 说明 |
|:-----|:-----|
| `cronforge start [--tui]` | 启动调度器（可选 TUI 面板模式） |
| `cronforge list` | 列出所有已配置的任务 |
| `cronforge add` | 交互式添加新任务 |
| `cronforge run <name>` | 立即执行指定任务 |
| `cronforge pause <name>` | 暂停指定任务 |
| `cronforge resume <name>` | 恢复指定任务 |
| `cronforge logs [name]` | 查看执行日志（可按任务名过滤） |
| `cronforge validate <expr>` | 验证 Cron 表达式是否合法 |
| `cronforge humanize <expr>` | 将 Cron 表达式翻译为人类可读描述 |
| `cronforge init` | 初始化配置文件 |
| `cronforge status` | 查看调度器运行状态与统计信息 |

#### Cron 表达式示例

```
*/5 * * * *     → 每5分钟
0 9 * * 1-5     → 每周一至周五上午9:00
30 */2 * * *    → 每2小时的第30分钟
@daily          → 每天0:00
@hourly         → 每小时
@every_30m      → 每30分钟
```

使用 `humanize` 命令查看翻译结果：

```bash
$ cronforge humanize "0 9 * * 1-5"
表达式: 0 9 * * 1-5
描述: 每周一至周五上午9:00

$ cronforge humanize "0 9 * * 1-5" --lang en
表达式: 0 9 * * 1-5
描述: At 9:00 AM, every Monday through Friday
```

---

### 💡 设计思路与迭代规划

#### 设计理念

- **零依赖优先** —— 仅使用 Python 标准库，避免依赖冲突，降低安装门槛
- **跨平台兼容** —— 统一的 YAML 配置 + 纯 Python 实现，一处配置到处运行
- **开发者友好** —— 清晰的 CLI 接口、结构化日志、人类可读的 Cron 翻译

#### 技术选型

| 选型 | 原因 |
|:-----|:-----|
| 纯标准库 | 避免第三方依赖冲突，确保在任何 Python 环境下均可运行 |
| SQLite | 轻量级嵌入式数据库，无需额外部署，适合本地日志存储 |
| curses | Python 标准库原生支持的终端 UI 框架，自动降级保障兼容性 |
| YAML 配置 | 声明式配置，可读性强，便于版本管理和团队协作 |

#### 后续迭代计划

| 版本 | 规划内容 |
|:-----|:---------|
| v1.1 | 多机远程调度支持 |
| v1.2 | Web Dashboard（浏览器端管理面板） |
| v1.3 | 邮件 / Slack 通知集成 |
| v1.4 | 任务依赖链（上游任务完成后触发下游任务） |
| v1.5 | 分布式锁（防止多实例重复执行） |

---

### 📦 打包与部署

#### pip 安装

```bash
pip install git+https://github.com/gitstq/CronForge.git
```

#### systemd 服务（Linux）

创建 `/etc/systemd/system/cronforge.service`：

```ini
[Unit]
Description=CronForge Scheduler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/your/project
ExecStart=/usr/local/bin/cronforge start
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动并设置开机自启：

```bash
sudo systemctl enable cronforge
sudo systemctl start cronforge
sudo systemctl status cronforge
```

#### launchd 服务（macOS）

创建 `~/Library/LaunchAgents/com.cronforge.scheduler.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cronforge.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/cronforge</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/your/project</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

加载服务：

```bash
launchctl load ~/Library/LaunchAgents/com.cronforge.scheduler.plist
```

---

### 🤝 贡献指南

欢迎参与 CronForge 的开发！请遵循以下规范：

#### 提交 Pull Request

1. Fork 本仓库并创建特性分支：`git checkout -b feature/your-feature`
2. 确保代码符合规范：Python 3.8+ 语法、类型注解、中文 docstring
3. 确保所有测试通过：`python -m pytest tests/`
4. 一个 PR 只解决一个问题，提交信息清晰明确
5. 提交 PR 并描述变更内容与动机

#### 报告 Issue

请通过 [GitHub Issues](https://github.com/gitstq/CronForge/issues) 提交问题，包含以下信息：

- 操作系统与 Python 版本
- 问题的详细描述与复现步骤
- 期望行为与实际行为的差异

#### 代码规范

- 零外部依赖，仅使用 Python 标准库
- 添加类型注解（Type Hints）
- 编写详细的中文 docstring
- 每个模块顶部添加模块说明注释

---

### 📄 开源协议

本项目基于 [MIT License](https://github.com/gitstq/CronForge/blob/main/LICENSE) 开源。

```
MIT License

Copyright (c) 2026 琦琦

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---
---

## 繁體中文

### 🎉 專案介紹

**CronForge** 是一款輕量級、跨平台的定時任務排程與管理引擎，以命令列工具（CLI）的形式交付。它面向需要在本地或伺服器環境中管理週期性任務的開發者和維運人員，提供從任務定義、排程執行到日誌審計的一站式解決方案。

**我們解決的核心痛點：**

- 傳統 `crontab` 僅限 Unix/Linux 平台，Windows 使用者難以使用
- 原生 cron 缺乏視覺化介面，任務狀態難以直觀掌握
- 日誌分散、缺乏結構化管理，排查問題費時費力
- 任務設定與系統強耦合，難以在不同環境間遷移

**差異化亮點：**

- **純 Python 零依賴** —— 僅使用標準庫，`pip install` 即裝即用，無需解決任何依賴衝突
- **內建 TUI Dashboard** —— 基於 curses 的終端面板，即時查看任務狀態，不支援 curses 時自動降級為純文字模式
- **人類可讀 Cron 翻譯** —— 將晦澀的 Cron 表達式翻譯為自然語言（中文/英文），降低閱讀門檻
- **SQLite 結構化日誌** —— 輕量級本地儲存，支援查詢、統計和自動清理

**靈感來源：** 本專案的設計參考了 [Cronboard](https://github.com/cronboard/cronboard)、[CronTUI](https://github.com/nickthecook/crontui)、[Pycroner](https://github.com/fabiocaccamo/python-croner) 等優秀開源專案的理念，在此基礎上追求零依賴、跨平台和開發者友好的極致體驗。

---

### ✨ 核心特性

| 特性 | 說明 |
|:-----|:-----|
| ⏰ **完整 Cron 表達式解析** | 標準 5 欄位（分 時 日 月 週）+ `@yearly`/`@daily` 等別名 + `@every_30m` 固定間隔語法 |
| 📋 **YAML 驅動設定** | 宣告式定義任務，支援逾時、重試、標籤、描述等豐富欄位 |
| 🖥️ **curses TUI Dashboard** | 互動式終端面板，即時展示任務狀態與下次執行時間，不支援 curses 時自動降級為純文字 |
| 🔄 **任務執行器** | subprocess 執行 + 逾時控制 + 指數退避重試機制 |
| 📊 **SQLite 執行日誌** | 結構化儲存執行記錄，支援查詢、統計和按時間清理 |
| 🔔 **Webhook 通知** | HTTP POST 通知，可按任務成功/失敗事件觸發 |
| 🌍 **人類可讀 Cron 翻譯** | 將 Cron 表達式翻譯為中文或英文自然語言描述 |
| 🚀 **零外部依賴** | 僅使用 Python 標準庫，無任何第三方依賴 |
| 💻 **跨平台支援** | Windows / macOS / Linux 全平台相容 |
| 🧪 **97 個單元測試** | 完善的測試覆蓋，保障程式碼品質 |

---

### 🚀 快速開始

#### 環境需求

- Python 3.8 或更高版本

#### 安裝

```bash
# 透過 pip 直接從 GitHub 安裝
pip install git+https://github.com/gitstq/CronForge.git

# 或複製儲存庫後本地安裝
git clone https://github.com/gitstq/CronForge.git
cd CronForge
pip install .
```

#### 初始化設定

```bash
cronforge init
```

此命令會在當前目錄產生 `cronforge.yaml` 設定檔範本。

#### 啟動排程器

```bash
cronforge start          # 背景執行
cronforge start --tui    # TUI 面板模式（互動式終端介面）
```

---

### 📖 詳細使用指南

#### 設定檔範例

編輯 `cronforge.yaml` 定義你的定時任務：

```yaml
tasks:
  - name: backup
    command: python backup.py
    cron: "0 2 * * *"
    timeout: 300
    retries: 3
    retry_delay: 60
    enabled: true
    tags: [backup, daily]
    description: "每日凌晨2點執行資料庫備份"

  - name: cleanup
    command: rm -rf /tmp/old_*
    cron: "@daily"
    timeout: 60
    retries: 1
    enabled: true

notifications:
  webhook:
    url: "https://hooks.example.com/cronforge"
    on_success: false
    on_failure: true

logging:
  max_entries: 10000
  cleanup_days: 30
```

#### CLI 子命令一覽

| 命令 | 說明 |
|:-----|:-----|
| `cronforge start [--tui]` | 啟動排程器（可選 TUI 面板模式） |
| `cronforge list` | 列出所有已設定的任務 |
| `cronforge add` | 互動式新增任務 |
| `cronforge run <name>` | 立即執行指定任務 |
| `cronforge pause <name>` | 暫停指定任務 |
| `cronforge resume <name>` | 恢復指定任務 |
| `cronforge logs [name]` | 檢視執行日誌（可按任務名稱篩選） |
| `cronforge validate <expr>` | 驗證 Cron 表達式是否合法 |
| `cronforge humanize <expr>` | 將 Cron 表達式翻譯為人類可讀描述 |
| `cronforge init` | 初始化設定檔 |
| `cronforge status` | 檢視排程器運作狀態與統計資訊 |

#### Cron 表達式範例

```
*/5 * * * *     → 每5分鐘
0 9 * * 1-5     → 每週一至週五上午9:00
30 */2 * * *    → 每2小時的第30分鐘
@daily          → 每天0:00
@hourly         → 每小時
@every_30m      → 每30分鐘
```

使用 `humanize` 命令檢視翻譯結果：

```bash
$ cronforge humanize "0 9 * * 1-5"
表達式: 0 9 * * 1-5
描述: 每週一至週五上午9:00

$ cronforge humanize "0 9 * * 1-5" --lang en
表達式: 0 9 * * 1-5
描述: At 9:00 AM, every Monday through Friday
```

---

### 💡 設計思路與迭代規劃

#### 設計理念

- **零依賴優先** —— 僅使用 Python 標準庫，避免依賴衝突，降低安裝門檻
- **跨平台相容** —— 統一的 YAML 設定 + 純 Python 實作，一處設定到處執行
- **開發者友善** —— 清晰的 CLI 介面、結構化日誌、人類可讀的 Cron 翻譯

#### 技術選型

| 選型 | 原因 |
|:-----|:-----|
| 純標準庫 | 避免第三方依賴衝突，確保在任何 Python 環境下均可執行 |
| SQLite | 輕量級嵌入式資料庫，無需額外部署，適合本地日誌儲存 |
| curses | Python 標準庫原生支援的終端 UI 框架，自動降級保障相容性 |
| YAML 設定 | 宣告式設定，可讀性強，便於版本管理與團隊協作 |

#### 後續迭代計畫

| 版本 | 規劃內容 |
|:-----|:---------|
| v1.1 | 多機遠端排程支援 |
| v1.2 | Web Dashboard（瀏覽器端管理面板） |
| v1.3 | 電子郵件 / Slack 通知整合 |
| v1.4 | 任務依賴鏈（上游任務完成後觸發下游任務） |
| v1.5 | 分散式鎖（防止多實例重複執行） |

---

### 📦 打包與部署

#### pip 安裝

```bash
pip install git+https://github.com/gitstq/CronForge.git
```

#### systemd 服務（Linux）

建立 `/etc/systemd/system/cronforge.service`：

```ini
[Unit]
Description=CronForge Scheduler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/your/project
ExecStart=/usr/local/bin/cronforge start
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

啟動並設定開機自啟：

```bash
sudo systemctl enable cronforge
sudo systemctl start cronforge
sudo systemctl status cronforge
```

#### launchd 服務（macOS）

建立 `~/Library/LaunchAgents/com.cronforge.scheduler.plist`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cronforge.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/cronforge</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/your/project</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

載入服務：

```bash
launchctl load ~/Library/LaunchAgents/com.cronforge.scheduler.plist
```

---

### 🤝 貢獻指南

歡迎參與 CronForge 的開發！請遵循以下規範：

#### 提交 Pull Request

1. Fork 本儲存庫並建立特性分支：`git checkout -b feature/your-feature`
2. 確保程式碼符合規範：Python 3.8+ 語法、型別註解、中文 docstring
3. 確保所有測試通過：`python -m pytest tests/`
4. 一個 PR 只解決一個問題，提交資訊清晰明確
5. 提交 PR 並描述變更內容與動機

#### 回報 Issue

請透過 [GitHub Issues](https://github.com/gitstq/CronForge/issues) 提交問題，包含以下資訊：

- 作業系統與 Python 版本
- 問題的詳細描述與重現步驟
- 預期行為與實際行為的差異

#### 程式碼規範

- 零外部依賴，僅使用 Python 標準庫
- 加入型別註解（Type Hints）
- 編寫詳細的中文 docstring
- 每個模組頂部加入模組說明註解

---

### 📄 開源協議

本專案基於 [MIT License](https://github.com/gitstq/CronForge/blob/main/LICENSE) 開源。

```
MIT License

Copyright (c) 2026 琦琦

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---
---

## English

### 🎉 Introduction

**CronForge** is a lightweight, cross-platform cron job scheduling and management engine delivered as a command-line tool (CLI). It is designed for developers and DevOps engineers who need to manage recurring tasks in local or server environments, providing an all-in-one solution from task definition and scheduled execution to log auditing.

**Core problems we solve:**

- The traditional `crontab` is limited to Unix/Linux, leaving Windows users without a viable alternative
- Native cron lacks a visual interface, making it hard to monitor task status at a glance
- Logs are scattered and unstructured, making troubleshooting time-consuming
- Task configurations are tightly coupled to the system, making cross-environment migration difficult

**What makes CronForge different:**

- **Pure Python, zero dependencies** — Uses only the standard library. Install with `pip install` and you're ready to go — no dependency conflicts to resolve
- **Built-in TUI Dashboard** — A curses-based terminal panel for real-time task monitoring, with automatic fallback to plain text mode when curses is unavailable
- **Human-readable Cron translation** — Translates cryptic Cron expressions into natural language (Chinese/English), lowering the barrier to understanding
- **SQLite structured logging** — Lightweight local storage with built-in query, statistics, and automatic cleanup

**Inspired by:** The design of this project draws on ideas from [Cronboard](https://github.com/cronboard/cronboard), [CronTUI](https://github.com/nickthecook/crontui), [Pycroner](https://github.com/fabiocaccamo/python-croner), and other excellent open-source projects, while pursuing the ultimate experience in zero-dependency, cross-platform, and developer-friendly design.

---

### ✨ Key Features

| Feature | Description |
|:--------|:------------|
| ⏰ **Full Cron Expression Parser** | Standard 5-field format (min hour day month weekday) + `@yearly`/`@daily` aliases + `@every_30m` interval syntax |
| 📋 **YAML-Driven Configuration** | Declarative task definition with rich fields: timeout, retries, tags, descriptions |
| 🖥️ **curses TUI Dashboard** | Interactive terminal panel showing real-time task status and next run times; auto-falls back to plain text when curses is unavailable |
| 🔄 **Task Executor** | subprocess-based execution with timeout control and exponential backoff retry |
| 📊 **SQLite Execution Logs** | Structured execution records with query, statistics, and time-based cleanup |
| 🔔 **Webhook Notifications** | HTTP POST notifications triggered by task success/failure events |
| 🌍 **Human-Readable Cron Translation** | Translates Cron expressions into Chinese or English natural language descriptions |
| 🚀 **Zero External Dependencies** | Uses only the Python standard library — no third-party packages required |
| 💻 **Cross-Platform Support** | Fully compatible with Windows / macOS / Linux |
| 🧪 **97 Unit Tests** | Comprehensive test coverage ensuring code quality |

---

### 🚀 Quick Start

#### Requirements

- Python 3.8 or higher

#### Installation

```bash
# Install directly from GitHub via pip
pip install git+https://github.com/gitstq/CronForge.git

# Or clone the repository and install locally
git clone https://github.com/gitstq/CronForge.git
cd CronForge
pip install .
```

#### Initialize Configuration

```bash
cronforge init
```

This command generates a `cronforge.yaml` configuration template in the current directory.

#### Start the Scheduler

```bash
cronforge start          # Run in the background
cronforge start --tui    # TUI dashboard mode (interactive terminal interface)
```

---

### 📖 Detailed Usage Guide

#### Configuration Example

Edit `cronforge.yaml` to define your scheduled tasks:

```yaml
tasks:
  - name: backup
    command: python backup.py
    cron: "0 2 * * *"
    timeout: 300
    retries: 3
    retry_delay: 60
    enabled: true
    tags: [backup, daily]
    description: "Run database backup daily at 2 AM"

  - name: cleanup
    command: rm -rf /tmp/old_*
    cron: "@daily"
    timeout: 60
    retries: 1
    enabled: true

notifications:
  webhook:
    url: "https://hooks.example.com/cronforge"
    on_success: false
    on_failure: true

logging:
  max_entries: 10000
  cleanup_days: 30
```

#### CLI Command Reference

| Command | Description |
|:--------|:------------|
| `cronforge start [--tui]` | Start the scheduler (optional TUI dashboard mode) |
| `cronforge list` | List all configured tasks |
| `cronforge add` | Interactively add a new task |
| `cronforge run <name>` | Immediately execute a specified task |
| `cronforge pause <name>` | Pause a specified task |
| `cronforge resume <name>` | Resume a specified task |
| `cronforge logs [name]` | View execution logs (optionally filter by task name) |
| `cronforge validate <expr>` | Validate a Cron expression |
| `cronforge humanize <expr>` | Translate a Cron expression to a human-readable description |
| `cronforge init` | Initialize the configuration file |
| `cronforge status` | Show scheduler status and statistics |

#### Cron Expression Examples

```
*/5 * * * *     → Every 5 minutes
0 9 * * 1-5     → At 9:00 AM, Monday through Friday
30 */2 * * *    → At minute 30 of every 2nd hour
@daily          → At 00:00 every day
@hourly         → At the start of every hour
@every_30m      → Every 30 minutes
```

Use the `humanize` command to see translations:

```bash
$ cronforge humanize "0 9 * * 1-5"
Expression: 0 9 * * 1-5
Description: At 9:00 AM, every Monday through Friday

$ cronforge humanize "0 9 * * 1-5" --lang cn
Expression: 0 9 * * 1-5
Description: 每周一至周五上午9:00
```

---

### 💡 Design Philosophy & Roadmap

#### Design Principles

- **Zero-dependency first** — Uses only the Python standard library to avoid dependency conflicts and minimize installation friction
- **Cross-platform compatibility** — Unified YAML configuration + pure Python implementation — configure once, run anywhere
- **Developer-friendly** — Clean CLI interface, structured logging, and human-readable Cron translations

#### Technology Choices

| Choice | Rationale |
|:-------|:----------|
| Pure standard library | Avoids third-party dependency conflicts; runs in any Python environment |
| SQLite | Lightweight embedded database requiring no additional deployment; ideal for local log storage |
| curses | Terminal UI framework natively supported by Python's standard library; automatic fallback ensures compatibility |
| YAML configuration | Declarative, highly readable, and easy to version-control and collaborate on |

#### Roadmap

| Version | Planned Features |
|:--------|:-----------------|
| v1.1 | Multi-machine remote scheduling support |
| v1.2 | Web Dashboard (browser-based management panel) |
| v1.3 | Email / Slack notification integration |
| v1.4 | Task dependency chains (trigger downstream tasks after upstream completion) |
| v1.5 | Distributed locks (prevent duplicate execution across multiple instances) |

---

### 📦 Packaging & Deployment

#### pip Installation

```bash
pip install git+https://github.com/gitstq/CronForge.git
```

#### systemd Service (Linux)

Create `/etc/systemd/system/cronforge.service`:

```ini
[Unit]
Description=CronForge Scheduler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/your/project
ExecStart=/usr/local/bin/cronforge start
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable cronforge
sudo systemctl start cronforge
sudo systemctl status cronforge
```

#### launchd Service (macOS)

Create `~/Library/LaunchAgents/com.cronforge.scheduler.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cronforge.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/cronforge</string>
        <string>start</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/your/project</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load the service:

```bash
launchctl load ~/Library/LaunchAgents/com.cronforge.scheduler.plist
```

---

### 🤝 Contributing

Contributions to CronForge are welcome! Please follow these guidelines:

#### Submitting a Pull Request

1. Fork this repository and create a feature branch: `git checkout -b feature/your-feature`
2. Ensure your code follows the conventions: Python 3.8+ syntax, type hints, Chinese docstrings
3. Make sure all tests pass: `python -m pytest tests/`
4. One PR per issue — keep commit messages clear and descriptive
5. Submit your PR with a description of the changes and motivation

#### Reporting Issues

Please use [GitHub Issues](https://github.com/gitstq/CronForge/issues) to report problems, including:

- Operating system and Python version
- Detailed description and steps to reproduce
- Expected vs. actual behavior

#### Code Conventions

- Zero external dependencies — use only the Python standard library
- Add type hints
- Write detailed Chinese docstrings
- Include a module-level docstring at the top of each module

---

### 📄 License

This project is licensed under the [MIT License](https://github.com/gitstq/CronForge/blob/main/LICENSE).

```
MIT License

Copyright (c) 2026 琦琦

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
