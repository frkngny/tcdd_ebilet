import re
import time

from playwright.sync_api import Playwright, sync_playwright, expect
import schedule

from utils.config_reader import get_config_value
from notification.notification_factory import get_notification_client

# "" -> all hours
# "X" -> after X o'clock
# "XX:YY"

class TCDDBot():
    def __init__(self):
        self.FROM = get_config_value("train", "FROM")
        self.TO = get_config_value("train", "TO")
        self.YEAR = get_config_value("train", "YEAR")
        self.MONTH = get_config_value("train", "MONTH")
        self.DAY = get_config_value("train", "DAY")
        self.HOUR = get_config_value("train", "HOUR")
        self.UNTIL = get_config_value("train", "UNTIL")
        print(f"{self.FROM} -> {self.TO} @ {self.DAY}/{self.MONTH} at/after {self.HOUR} until {self.UNTIL}")

    def run(self, playwright: Playwright) -> None:
        while True:
            try:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Chrome/126.0.0.0 Safari/537.36"
                )
                page = context.new_page()

                # gidis - gelis
                page.goto("https://bilet.tcdd.gov.tr/")
                page.locator("#fromTrainInput").click()
                page.locator("#fromTrainInput").fill(self.FROM)
                page.get_by_role("button", name=self.FROM).click()

                page.locator("input[name=\"Tren varış\"]").click()
                page.locator("input[name=\"Tren varış\"]").fill(self.TO)
                page.get_by_role("button", name=self.TO).click()

                page.locator(".datePickerInput").first.click()
                page.get_by_label("Bilet Al").locator(f"[id=\"\\30 {self.DAY}-{self.MONTH}-{self.YEAR}\"]").click()

                page.get_by_role("button", name="Sefer Ara").click()

                waiting = page.locator("#accordionSefer")
                waiting.wait_for()
                break
            except:
                context.close()
                browser.close()
                print("Retrying...")
                time.sleep(2)
                continue
            
        appointment_found = False
        seats = {}
        cards = page.locator("[id='accordionSefer']").locator(".card")
        try:
            for n, card in enumerate(cards.all()):
                # check departure time
                board_time = card.locator(".textDepartureArea").inner_text()
                if self.HOUR != "":
                    if ":" in self.HOUR:
                        if board_time != self.HOUR:
                            continue
                    else:
                        m_saat = board_time.split(":")[0].strip()
                        if int(m_saat) < int(self.HOUR) or int(m_saat) > int(self.UNTIL):
                            continue
                        
                # check if row has ekonomi seat
                has_seat = False
                av_seats = 0
                card.click()
                time.sleep(0.5)
                try:
                    empty_seats = card.get_by_role("button", name="Ekonomi 2+2 Pulman (Ekonomi)").locator(".emptySeat").inner_text()
                except:
                    continue
                numbers = get_numbers(empty_seats)
                if len(numbers) > 0:
                    if int(numbers[0]) > 0:
                        av_seats = numbers[0]
                        has_seat = True

                if not has_seat:
                    continue
                
                seats[board_time] = av_seats
                print(f"Saat: {board_time}, koltuk sayisi: {av_seats}")
                appointment_found = True
        except Exception as e:
            print(e)
        
        if(appointment_found):
            notify(appointment_params=seats)
            
        context.close()
        browser.close()
        
        return appointment_found
    
def notify(appointment_params: dict[str, str]):
    message = f"Found ticket: {[f"Saat: {key} - koltuk: {appointment_params[key]}" for key in appointment_params.keys()]}"
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

def start():
    found = False
    try:
        with sync_playwright() as playwright:
            tcddbot = TCDDBot()
            found = tcddbot.run(playwright)
    except Exception as e:
        print(e)
    return found

if __name__ == "__main__":
    start()

