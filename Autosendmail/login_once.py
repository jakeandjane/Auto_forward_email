"""
首次登录脚本 - 只需要运行一次
作用:打开浏览器让你手动登录 mail.com,然后保存登录状态(cookies)到 auth_state.json
之后 forward_bot.py 就能用这个状态自动登录,不需要每次输密码也不会触发验证码
"""

from playwright.sync_api import sync_playwright
import os

AUTH_FILE = "auth_state.json"


def main():
    print("=" * 60)
    print("📧 mail.com 首次登录设置")
    print("=" * 60)
    print()
    print("即将打开浏览器,请你:")
    print("  1. 手动登录你的 mail.com 邮箱")
    print("  2. 如果有验证码、安全提示,都正常通过")
    print("  3. 看到收件箱后,回到这个窗口按 Enter")
    print()
    input("准备好了按 Enter 继续...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("\n🌐 正在打开 mail.com 登录页...")
        page.goto("https://www.mail.com/", wait_until="domcontentloaded")

        print("\n⏳ 请在浏览器中手动登录,登录成功并看到收件箱后,")
        print("   回到这个窗口按 Enter 保存登录状态。\n")
        input("登录完成后按 Enter 保存 >>> ")

        # 保存登录状态
        context.storage_state(path=AUTH_FILE)
        print(f"\n✅ 登录状态已保存到 {AUTH_FILE}")
        print("现在可以关闭浏览器,运行 forward_bot.py 开始自动转发")

        browser.close()


if __name__ == "__main__":
    main()
