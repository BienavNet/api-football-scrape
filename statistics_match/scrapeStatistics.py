import sys, asyncio, json, uuid
sys.path.append('\\Users\\User\\Desktop\\api futbol scrapping')

from playwright.async_api import async_playwright, Browser
from bs4 import BeautifulSoup
from termcolor import colored
from config.config import TIMEOUT, SCRAPE_STATISTICS_LINKS_DIR_INPUT, SCRAPE_STATISTICS_LINKS_DIR_OUTPUT, CONCURRENCY_WORKERS, HEADLESS, MAX_RETRIES
from asyncio import Semaphore


async def main(browser: Browser, url: str):

    try:
        retries = 0
        # home_name = away_name = match_date = score = refereeName = competition = total_shots = shots_on_target = corners = cards = fouls = None
        while(retries < MAX_RETRIES):
            try:
                
                context = await browser.new_context(no_viewport=False)
                page = await context.new_page()
                page.set_default_timeout(TIMEOUT)
                await page.goto(url, wait_until="load")

                await page.wait_for_selector("button:has-text('Stats')", timeout=30000)
                await page.click("button:has-text('Stats')")
                await page.wait_for_selector('.sectionsWrapper')
                content = await page.content()

                soup = BeautifulSoup(content, 'html.parser')

                home_name = soup.find('div', {'class': "duelParticipant__home"}).find('a', {'class': 'participant__participantName participant__overflow'}).get_text(strip=True)

                away_name = soup.find('div', {'class': "duelParticipant__away"}).find('a', {'class': 'participant__participantName participant__overflow'}).get_text(strip=True)

                match_date = soup.find('div', {'class': 'duelParticipant__startTime'}).find('div').get_text(strip=True)

                scoreElement = soup.find('div', {'class': "detailScore__wrapper"}).find_all('span')

                score = {
                    "home": scoreElement[0].get_text(),
                    "away": scoreElement[2].get_text()
                }

                sectionStats = soup.find('div', {'class': 'sectionsWrapper'}).find_all('div')
                total_stats = {}

                for section in sectionStats:
                    try:

                        title = section.find('div', {'class': 'sectionHeader'}).get_text()
                        dataRows = section.find_all('div', {"class": "wcl-row_2oCpS"})

                        temp_stats = {}

                        for row in dataRows:
                            data = row.find('div', {'class': 'wcl-category_Ydwqh'})
                            stats = data.find_all('div')

                            home = stats[0].get_text()
                            away = stats[len(stats)-1].get_text()   
                            name = stats[1].get_text()
                            
                            temp_stats[name] = {
                                "home": home,
                                "away": away
                            }
                        
                        total_stats[title] = temp_stats
                    except:
                        pass

                mydata = {
                    "id": uuid.uuid4().hex,
                    "home": home_name,
                    "away": away_name,
                    "match_date": match_date,
                    "score": score,
                    "data": total_stats
                }

                return mydata

            except Exception as e:
                print(colored(f"Error on scrapeTeams.py {url}: line {e.__traceback__.tb_lineno}\tDetails: {e}", "red"))
                retries+=1

            finally:

                if page:
                    await page.close()
                if context:
                    await context.close()

    except:
        await context.close()

async def run(from_scrape: int = 1, to_scrape: int = 1):
    
    for i in range(from_scrape, to_scrape + 1):
        try:

            with open(f"{SCRAPE_STATISTICS_LINKS_DIR_INPUT}{str(i).zfill(3)}.json", 'r') as file:
                jsonMatchData = json.load(file)

            matchs = jsonMatchData['matchs']
        except FileNotFoundError:
            print(f"ERROR: No se encontró el archivo de enlaces: {SCRAPE_STATISTICS_LINKS_DIR_INPUT}")
            return

        try:

            semaphore = Semaphore(CONCURRENCY_WORKERS)

            async with async_playwright() as p:
                browser = await p.chromium.launch(channel="msedge", headless=HEADLESS)
                tasks = [run_limited(browser, match['link'], semaphore) for match in matchs]

                all_results_lists = await asyncio.gather(*tasks)

                await browser.close()

                all_statistics = []
                for result_list in all_results_lists:
                    if result_list:
                        all_statistics.append(result_list)

                final_json_object = {
                    "statistics": all_statistics
                }

                with open(f"{SCRAPE_STATISTICS_LINKS_DIR_OUTPUT}{str(i).zfill(3)}.json", 'w', encoding='utf-8') as outfile:
                    json.dump(final_json_object, outfile, indent=4, ensure_ascii=False)

                print(colored("Task Done, results was saved on data.json.", 'green'))

        
        except NoTeamsFoundException as e:
            print(colored(f"Error on scrapeTeams.py: line {e.__traceback__.tb_lineno}\tDetails: {e}", "red"))

async def run_limited(browser: Browser, url: str, semaphore: Semaphore):
    async with semaphore:
        result = await main(browser, url)
        return result

