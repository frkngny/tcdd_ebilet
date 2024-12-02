from bot import tcdd_bot
from utils.timer import countdown
from utils.config_reader import get_config_value, initialize_config


initialize_config()

while True:
    appointment_found = tcdd_bot.start()
    if appointment_found:
        break
    countdown(
        int(get_config_value("default", "interval")),
        "Next appointment check in",
    )