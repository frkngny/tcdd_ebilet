import re
import time

from playwright.sync_api import Playwright, sync_playwright
import schedule

from utils.config_reader import get_config_value
from notification.notification_factory import get_notification_client


FROM = "Ankara Gar"
TO = "İzmit YHT"

MONTH = 12
DAY = 8

# "" -> all hours
# "X" -> after X o'clock
# "XX:YY"
SAAT = "9"
UNTIL = "22"

def set_parameters():
    FROM = get_config_value("train", "FROM")
    TO = get_config_value("train", "TO")
    MONTH = get_config_value("train", "MONTH")
    DAY = get_config_value("train", "DAY")
    SAAT = get_config_value("train", "SAAT")
    UNTIL = get_config_value("train", "UNTIL")
    
    print(f"{FROM} -> {TO} @ {DAY}/{MONTH} at/after {SAAT} until {UNTIL}")


def notify(appointment_params: dict[str, str], dates: list[str]):
    message = f"Found appointment(s) for {', '.join(appointment_params.values())} on {', '.join(dates)}"
    channels = get_config_value("notification", "channels")

    for channel in channels.split(","):
        client = get_notification_client(channel)
        try:
            client.send_notification(message)
        except Exception:
            pass
            #logging.error(f"Failed to send {channel} notification")


def get_numbers(str):
    array = re.findall(r'[1-9]+', str)
    return array


def run(playwright: Playwright) -> None:
    while True:
        try:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Chrome/126.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            page.goto("https://ebilet.tcddtasimacilik.gov.tr", wait_until="commit")
            time.sleep(2)
            page.goto("https://ebilet.tcddtasimacilik.gov.tr")


            # gidis - gelis
            page.locator("#nereden").click()
            page.locator("#nereden").fill(FROM)
            # page.get_by_text(FROM).click()

            page.locator("#nereye").click()
            page.locator("#nereye").fill(TO)
            # page.get_by_text(TO).click()

            page.locator("#trCalGid_input").click()
            page.get_by_role("combobox").first.select_option(str(MONTH-1))
            page.get_by_role("link", name=str(DAY), exact=True).click()

            # playwright.selectors.set_test_id_attribute("data-handler")
            # page.get_by_test_id("selectMonth").select_option(MONTH)

            page.get_by_role("button", name="Ara").click()

            waiting = page.locator("#mainTabView")
            waiting.wait_for()
            break
        except:
            context.close()
            browser.close()
            print("Retrying...")
            time.sleep(2)
            continue

    ###
    appointment_found = False
    playwright.selectors.set_test_id_attribute("data-ri")
    rows_count = page.locator("[id='mainTabView:gidisSeferTablosu_data']").locator("tr").count()
    try:
        dates = []
        seats = {}
        for n in range(0, rows_count):
            tr = page.get_by_test_id(f"{n}")

            board_time = tr.get_by_role("gridcell").first.locator(".seferSorguTableBuyuk").inner_text()
            if SAAT != "":
                if ":" in SAAT:
                    if board_time != SAAT:
                        continue
                else:
                    m_saat = board_time.split(":")[0]
                    if int(m_saat) < int(SAAT) or int(m_saat) > int(UNTIL):
                        continue
            # check if row has ekonomi seat
            has_seat = False
            av_seats = 0
            texts = tr.locator(f"[id='mainTabView:gidisSeferTablosu:{n}:j_idt109:0:somVagonTipiGidis1_label']").all_inner_texts()
            if len(texts) > 0:
                mtxt = texts[0]
                if "Ekonomi" in mtxt and "Engelli" not in mtxt:
                    otxt = mtxt.split("(Ekonomi)")[1]
                    numbers = get_numbers(otxt)
                    if len(numbers) > 0:
                        if int(numbers[0]) > 0:
                            av_seats = numbers[0]
                            has_seat = True

            if not has_seat:
                continue
            
            dates.append(board_time)
            seats[board_time] = av_seats
            print(f"Saat: {board_time}, koltuk sayisi: {av_seats}")
            appointment_found = True
            
        if(appointment_found):
            notify(appointment_params=seats, dates=dates)
    except Exception as e:
        print(e)
        
    context.close()
    browser.close()
    
    return appointment_found
    


def start():
    found = False
    try:
        set_parameters()
        with sync_playwright() as playwright:
            found = run(playwright)
    except Exception as e:
        print(e)
    return found

if __name__ == "__main__":
    start()

