# 📧 mail.com 自动转发机器人

通过浏览器自动化,把 mail.com 收到的新邮件自动转发到指定邮箱(如 163、QQ、Gmail)。
**适用场景**:mail.com 免费版不支持 POP3/IMAP 和官方转发,只能通过模拟浏览器操作。

---

## 🚀 快速开始(5 步搞定)

### 第 1 步:安装 Python

如果你电脑没装 Python,先去 https://www.python.org/downloads/ 下载 **Python 3.10+**。

> ⚠️ **安装时一定要勾选**:`Add Python to PATH`

装完后,按 `Win + R` 输入 `cmd`,在黑窗口里输入 `python --version`,能显示版本号就成功。

### 第 2 步:把整个文件夹放到合适位置

建议放在 `D:\mailcom_forwarder\` 或 `C:\Users\你的名字\mailcom_forwarder\`,
**路径不要有中文或空格**(否则 pip 可能出问题)。

### 第 3 步:安装依赖

**双击运行 `安装依赖.bat`**

它会自动:
- 安装 Playwright 库
- 下载 Chromium 浏览器(约 150MB,稍等几分钟)

看到 `✅ 安装完成!` 就成功了。

### 第 4 步:配置转发邮箱

用记事本打开 **`config.json`**,把以下信息填上:

```json
{
  "mailcom_email": "你的账号@mail.com",
  "mailcom_password": "你的密码(可留空,登录用)",
  "forward_to": "你的163邮箱@163.com",
  "check_interval_seconds": 120,
  "headless": true,
  "max_forwards_per_run": 10,
  "forward_subject_prefix": "[转发] "
}
```

**字段说明**:

| 字段 | 含义 |
|------|------|
| `mailcom_email` | 你的 mail.com 邮箱(目前只是显示用,登录靠 cookie) |
| `mailcom_password` | 密码,可以留空(实际登录靠保存的 cookie) |
| `forward_to` | **要转发到的目标邮箱**(填这个最重要) |
| `check_interval_seconds` | 多少秒检查一次,默认 120(2 分钟) |
| `headless` | 是否隐藏浏览器窗口。**首次测试建议改成 false**,稳定后改 true |
| `max_forwards_per_run` | 单次最多转发几封,防止短时间内转发太多被风控 |
| `forward_subject_prefix` | 转发邮件主题前缀(目前用 mail.com 的默认 "Fwd:") |

### 第 5 步:首次登录

**双击运行 `首次登录.bat`**

按提示操作:
1. 脚本会打开 Chromium 浏览器,自动打开 mail.com
2. 你在浏览器里**手动登录**(输账号、密码,过验证码)
3. 看到收件箱后,**回到命令行黑窗口**,按 Enter
4. 脚本会保存登录状态到 `auth_state.json`

✅ 这一步只用做一次,以后机器人就用这个保存的状态自动登录,不会再有验证码。

> 💡 如果几周后登录失效,重新跑一次 `首次登录.bat` 即可。

---

## ▶️ 正式启动

**双击运行 `启动.bat`**

机器人会:
- 每 2 分钟检查一次收件箱
- 把没转发过的邮件转发到你配置的邮箱
- 已转发的记录保存在 `forwarded.json`,不会重复转发

**保持这个窗口开着不关**,关了机器人就停了。

要停止:在窗口里按 `Ctrl + C`。

---

## 🔧 进阶:开机自启 + 后台运行

### 方法 1:任务计划程序(推荐)

1. 按 `Win + R` 输入 `taskschd.msc` 打开任务计划程序
2. 右侧「创建基本任务」
3. 名称:`mail.com 转发机器人`
4. 触发器:**当用户登录时**
5. 操作:**启动程序**,路径选你的 `启动.bat`
6. 完成后右键这个任务 → 属性 → 勾选「使用最高权限运行」

之后开机自动启动,后台默默运行。

### 方法 2:放到启动文件夹

1. 按 `Win + R` 输入 `shell:startup`
2. 把 `启动.bat` 的**快捷方式**拖进去

---

## 🛠️ 故障排查

### ❌ 启动后立刻报"找不到 auth_state.json"
→ 你还没运行过 `首次登录.bat`,先做这一步。

### ❌ 报"登录状态失效"
→ cookie 过期了,重新跑一次 `首次登录.bat`。

### ❌ 转发失败,生成了 error_xxxxx.png
→ 打开这个截图看是卡在哪一步,通常是 mail.com 界面改版导致选择器失效。
   把截图发给开发者,改一下 `forward_bot.py` 里的选择器即可。

### ❌ 转发太慢
→ 在 `config.json` 里把 `headless` 改成 `true`,无头模式速度快一点。

### ⚠️ 想看机器人在做什么
→ 把 `config.json` 的 `headless` 改成 `false`,会显示浏览器窗口。

### 📋 日志在哪
→ 同目录下的 `forwarder.log`,记录了所有运行历史。

---

## ⚠️ 重要提醒

1. **不要短时间转发太多邮件**:mail.com 可能会风控,默认每轮最多 10 封,够用了。
2. **首次登录的浏览器和正式运行的浏览器是同一个**(都是 Playwright 控制的 Chromium),所以 cookie 通用。
3. **接收方邮箱可能把转发邮件归到垃圾箱**:第一次收到后,记得在 163/QQ 邮箱里把 mail.com 加白名单。
4. **mail.com 界面如果改版**,脚本可能失效,需要更新选择器。

---

## 📂 文件清单

```
mailcom_forwarder/
├── config.json          ← 配置文件(你需要修改)
├── login_once.py        ← 首次登录脚本
├── forward_bot.py       ← 主转发脚本
├── requirements.txt     ← Python 依赖列表
├── 安装依赖.bat          ← 双击安装依赖
├── 首次登录.bat          ← 双击进行首次登录
├── 启动.bat             ← 双击启动机器人
├── README.md            ← 本说明文档
├── auth_state.json      ← 登录状态(自动生成)
├── forwarded.json       ← 已转发记录(自动生成)
└── forwarder.log        ← 运行日志(自动生成)
```

祝使用愉快 🎉
