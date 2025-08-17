import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        await page.goto("http://127.0.0.1:5000")

        start_button = page.get_by_role("button", name="Commencer une nouvelle main")
        await expect(start_button).to_be_visible()
        await start_button.click()

        # Attendre que les sièges des joueurs soient rendus
        await expect(page.locator(".player-seat").first).to_be_visible(timeout=5000)

        # Attendre plus longtemps pour que le jeu progresse et que les logs apparaissent
        await page.wait_for_timeout(5000)

        await page.screenshot(path="jules-scratch/verification/poker_final_screenshot_v2.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
