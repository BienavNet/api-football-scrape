import sys, asyncio, json, uuid
sys.path.append('\\Users\\User\\Desktop\\api futbol scrapping')

from playwright.async_api import async_playwright, Browser, TimeoutError
from exceptions.main import NoMatchsFoundException
from bs4 import BeautifulSoup
from termcolor import colored
from config.config import TIMEOUT, SCRAPE_MATCHS_LINKS_DIR_INPUT, SCRAPE_MATCHS_LINKS_DIR_OUTPUT, CONCURRENCY_WORKERS
from asyncio import Semaphore





async def main(browser: Browser, url: str):
    try:

        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()
        page.set_default_timeout(TIMEOUT)
        await page.goto(f"{url}results/", wait_until="load")

        for _ in range(10):

            try:
                thereMoreResults = await page.is_visible('span:has-text("Show more games")', timeout=1500)

                if thereMoreResults:
                    await page.click('span:has-text("Show more games")')
                    await page.wait_for_timeout(1500)
            except:
                pass

        content = await page.content()

        await context.close()

        soup = BeautifulSoup(content, 'html.parser')

        matchs = soup.find_all('a', {'class': 'eventRowLink'})

        if not matchs:
            raise NoMatchsFoundException(f"No se encontraron partidos para este equipo: {url}")
        
        data = []

        for element in matchs:
            data.append({
                "id": uuid.uuid4().hex,
                "link": f"{element.get('href')}"
            })

        return data

    except Exception as e:
        print(colored(f"Error on scrapeTeams.py: line {e.__traceback__.tb_lineno}\tDetails: {e}", "red"))

    

async def run():
    try:

        with open(SCRAPE_MATCHS_LINKS_DIR_INPUT, 'r') as file:
            jsonTeamsData = json.load(file)

        teams = jsonTeamsData['teams']
        
    except FileNotFoundError:
        print(f"ERROR: No se encontró el archivo de enlaces: {SCRAPE_MATCHS_LINKS_DIR_INPUT}")
        return

    try:

        semaphore = Semaphore(CONCURRENCY_WORKERS)

        async with async_playwright() as p:
            browser = await p.chromium.launch(channel="msedge", headless=True)
            tasks = [run_limited(browser, team['link'], semaphore) for team in teams]

            all_matchs_lists = await asyncio.gather(*tasks)

            await browser.close()

            all_matchs = []
            for match_result in all_matchs_lists:
                if match_result:
                    all_matchs.extend(match_result)

            final_json_object = {
                "matchs": all_matchs
            }

            with open(SCRAPE_MATCHS_LINKS_DIR_OUTPUT, 'w', encoding='utf-8') as outfile:
                json.dump(final_json_object, outfile, indent=4, ensure_ascii=False)

            print(colored("Task Done, results was saved on data.json.", 'green'))

        
    except NoMatchsFoundException as e:
        print(colored(f"Error on scrapeTeams.py: line {e.__traceback__.tb_lineno}\tDetails: {e}", "red"))

async def run_limited(browser: Browser, url: str, semaphore: Semaphore):
    async with semaphore:
        result = await main(browser, url)
        return result

