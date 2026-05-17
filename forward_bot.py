"""
mail.com 自动转发机器人
循环检测收件箱中的新邮件,自动转发到指定邮箱

运行前提:
  1. 已经运行过 login_once.py 完成首次登录
  2. config.json 已经配置好转发目标邮箱
"""

import json
import time
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ============ 文件路径 ============
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"
AUTH_FILE = SCRIPT_DIR / "auth_state.json"
FORWARDED_FILE = SCRIPT_DIR / "forwarded.json"
LOG_FILE = SCRIPT_DIR / "forwarder.log"


# ============ 工具函数 ============
def log(msg: str):
    """同时输出到控制台和日志文件"""
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        log("❌ 找不到 config.json,请先创建并填写")
        sys.exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    # 校验
    required = ["mailcom_email", "forward_to"]
    for k in required:
        if not cfg.get(k) or "你的" in str(cfg.get(k, "")):
            log(f"❌ config.json 中的 {k} 没有填写")
            sys.exit(1)
    return cfg


def load_forwarded() -> set:
    if not FORWARDED_FILE.exists():
        return set()
    try:
        with open(FORWARDED_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("ids", []))
    except Exception:
        return set()


def save_forwarded(ids: set):
    # 只保留最近 1000 条,避免文件无限增长
    ids_list = list(ids)[-1000:]
    with open(FORWARDED_FILE, "w", encoding="utf-8") as f:
        json.dump({"ids": ids_list, "updated": datetime.now().isoformat()},
                  f, ensure_ascii=False, indent=2)


# ============ 核心转发逻辑 ============
def get_inbox_emails(page) -> list:
    """
    扫描收件箱,返回邮件列表
    每个元素:{"id": 唯一标识, "subject": 主题, "sender": 发件人, "element": 邮件行的 locator}
    """
    # 进入收件箱
    try:
        # mail.com 的收件箱通常自动加载,等列表出现即可
        page.wait_for_selector("text=Inbox", timeout=15000)
    except PWTimeout:
        log("⚠️ 没找到 Inbox,可能登录失效")
        raise

    # 等邮件列表渲染
    time.sleep(2)

    emails = []
    # 邮件行的常见选择器(mail.com 用 div 列表展示邮件)
    # 主要靠 data-* 属性或文本特征定位
    rows = page.locator('[data-mailid], [data-id], .mail-list-row, .ui-grid-row').all()

    if not rows:
        # 兼容备用选择器
        rows = page.locator('div[role="row"]').all()

    for row in rows:
        try:
            # 提取主题、发件人作为唯一标识(因为没有稳定的邮件ID DOM 暴露)
            text = row.inner_text(timeout=2000).strip()
            if not text:
                continue
            # 用文本的 hash 作为去重 key
            uid = str(hash(text))
            emails.append({
                "id": uid,
                "preview": text[:80].replace("\n", " | "),
                "element": row
            })
        except Exception:
            continue

    return emails


def forward_email(page, email_row, forward_to: str, subject_prefix: str) -> bool:
    """
    打开一封邮件并转发
    返回 True 表示转发成功
    """
    try:
        # 点击邮件打开
        email_row.click()
        time.sleep(1.5)

        # 找到 Forward 按钮(顶部工具栏)
        forward_btn = page.locator("text=Forward").first
        forward_btn.wait_for(state="visible", timeout=8000)
        forward_btn.click()
        time.sleep(2)

        # 找到收件人输入框(转发界面的 To 字段)
        to_input = page.locator('input[placeholder*="recipient" i], '
                                'input[placeholder*="to" i], '
                                'input[name="to"]').first
        to_input.wait_for(state="visible", timeout=8000)
        to_input.fill(forward_to)
        time.sleep(0.5)
        # 按 Enter 或 Tab 确认收件人
        to_input.press("Tab")
        time.sleep(0.5)

        # 点击 Send 按钮
        send_btn = page.locator('button:has-text("Send"), '
                                'a:has-text("Send")').first
        send_btn.wait_for(state="visible", timeout=8000)
        send_btn.click()

        # 等发送完成
        time.sleep(3)
        return True

    except Exception as e:
        log(f"   ⚠️ 转发失败: {e}")
        # 截图保存现场,方便排查
        try:
            screenshot_path = SCRIPT_DIR / f"error_{int(time.time())}.png"
            page.screenshot(path=str(screenshot_path))
            log(f"   📸 错误截图: {screenshot_path.name}")
        except Exception:
            pass
        # 尝试关闭弹窗回到收件箱
        try:
            page.keyboard.press("Escape")
            time.sleep(1)
        except Exception:
            pass
        return False


def run_one_cycle(cfg: dict, forwarded: set):
    """跑一轮检测+转发"""
    if not AUTH_FILE.exists():
        log("❌ 找不到 auth_state.json,请先运行 login_once.py")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=cfg.get("headless", True))
        context = browser.new_context(
            storage_state=str(AUTH_FILE),
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            log("🌐 打开 mail.com...")
            page.goto("https://www.mail.com/int/mail/", wait_until="domcontentloaded")
            time.sleep(3)

            # 检查是否登录成功(没跳转到登录页)
            if "login" in page.url.lower() or page.locator('input[type="password"]').count() > 0:
                log("❌ 登录状态失效,请重新运行 login_once.py")
                return

            log("📥 扫描收件箱...")
            emails = get_inbox_emails(page)
            log(f"   找到 {len(emails)} 封邮件")

            new_emails = [e for e in emails if e["id"] not in forwarded]
            log(f"   其中 {len(new_emails)} 封是新邮件")

            if not new_emails:
                log("✅ 没有新邮件需要转发")
                return

            max_forwards = cfg.get("max_forwards_per_run", 10)
            new_emails = new_emails[:max_forwards]

            forward_to = cfg["forward_to"]
            subject_prefix = cfg.get("forward_subject_prefix", "[转发] ")

            success_count = 0
            for i, em in enumerate(new_emails, 1):
                log(f"📤 [{i}/{len(new_emails)}] 转发: {em['preview']}")
                if forward_email(page, em["element"], forward_to, subject_prefix):
                    forwarded.add(em["id"])
                    success_count += 1
                    save_forwarded(forwarded)
                    log(f"   ✅ 成功")
                else:
                    log(f"   ❌ 失败,跳过")

                # 返回收件箱准备下一封
                try:
                    page.goto("https://www.mail.com/int/mail/", wait_until="domcontentloaded")
                    time.sleep(2)
                except Exception:
                    pass

            log(f"🎉 本轮完成:成功转发 {success_count}/{len(new_emails)} 封")

        except Exception as e:
            log(f"❌ 本轮异常: {e}")
            log(traceback.format_exc())
        finally:
            browser.close()


# ============ 主循环 ============
def main():
    log("=" * 60)
    log("🚀 mail.com 自动转发机器人启动")
    log("=" * 60)

    cfg = load_config()
    forwarded = load_forwarded()

    log(f"📧 源邮箱: {cfg['mailcom_email']}")
    log(f"📬 转发到: {cfg['forward_to']}")
    log(f"⏱️ 检查间隔: {cfg['check_interval_seconds']} 秒")
    log(f"🪟 无头模式: {cfg.get('headless', True)}")
    log(f"📝 已转发记录: {len(forwarded)} 条")
    log("-" * 60)

    while True:
        try:
            run_one_cycle(cfg, forwarded)
        except KeyboardInterrupt:
            log("👋 收到退出信号,停止运行")
            break
        except Exception as e:
            log(f"❌ 主循环异常: {e}")
            log(traceback.format_exc())

        interval = cfg.get("check_interval_seconds", 120)
        log(f"💤 休眠 {interval} 秒后再次检查...\n")
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            log("👋 收到退出信号,停止运行")
            break


if __name__ == "__main__":
    main()
