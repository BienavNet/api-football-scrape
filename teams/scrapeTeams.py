import sys, asyncio, json, uuid
sys.path.append('\\Users\\User\\Desktop\\api futbol scrapping')

from playwright.async_api import async_playwright, Browser
from exceptions.main import NoTeamsFoundException
from bs4 import BeautifulSoup
from termcolor import colored
from config.config import TIMEOUT, SCRAPE_TEAMS_LINKS_DIR_INPUT, SCRAPE_TEAMS_LINKS_DIR_OUTPUT, CONCURRENCY_WORKERS
from asyncio import Semaphore

async def main(browser: Browser, url: str):
    try:

        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()
        page.set_default_timeout(TIMEOUT)
        await page.goto(url, wait_until="networkidle")
        content = await page.content()

        soup = BeautifulSoup(content, 'html.parser')

        anchorList = soup.find_all('a', {"class": "tableCellParticipant__name"})
        leagueName = soup.find('div', {"class": "heading__name"}).get_text(strip=True)

        if not anchorList:
            raise NoTeamsFoundException(f"No se encontraron equipos de futbol para esta liga: {url}")
        
        data = []
        for element in anchorList:
            data.append({
                "id": uuid.uuid4().hex,
                "name": element.get_text(),
                "link": f"https://www.flashscoreusa.com{element.get('href')}",
                "league": leagueName
            })

        return data

    except Exception as e:
        print(colored(f"Error on scrapeTeams.py: line {e.__traceback__.tb_lineno}\tDetails: {e}", "red"))

    finally:
        if 'context' in locals():
            await context.close()
    

async def run():
    try:

        with open(SCRAPE_TEAMS_LINKS_DIR_INPUT, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"ERROR: No se encontró el archivo de enlaces: {SCRAPE_TEAMS_LINKS_DIR_INPUT}")
        return

    try:

        semaphore = Semaphore(CONCURRENCY_WORKERS)

        async with async_playwright() as p:
            browser = await p.chromium.launch(channel="msedge", headless=True)
            tasks = [run_limited(browser, url, semaphore) for url in urls]

            all_results_lists = await asyncio.gather(*tasks)

            await browser.close()

            all_teams = []
            for result_list in all_results_lists:
                if result_list:
                    all_teams.extend(result_list)

            final_json_object = {
                "teams": all_teams
            }

            with open(SCRAPE_TEAMS_LINKS_DIR_OUTPUT, 'w', encoding='utf-8') as outfile:
                json.dump(final_json_object, outfile, indent=4, ensure_ascii=False)

            print(colored("Task Done, results was saved on data.json.", 'green'))

        
    except NoTeamsFoundException as e:
        print(colored(f"Error on scrapeTeams.py: line {e.__traceback__.tb_lineno}\tDetails: {e}", "red"))

async def run_limited(browser: Browser, url: str, semaphore: Semaphore):
    async with semaphore:
        result = await main(browser, url)
        return result


