import smtplib
from utils.config_reader import get_config_section

class EmailClient:
    def __init__(self):
        self.config = get_config_section("email")
        required_keys = ["email", "password"]
        
    
    def send_notification(self, message: str):
        email: str = self.config.get("email")
        password: str = self.config.get("password")
        to_email: str = self.config.get("notify_email")
        email_text = self.__construct_email_text(email, to_email, message)

        smtp_server = smtplib.SMTP("smtp.gmail.com", 587) #465
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.login(email, password)
        smtp_server.sendmail(email, to_email, email_text)
        smtp_server.quit()
    
    def __construct_email_text(self, email: str, to_email: str, message: str) -> str:
        return f"From: {email}\nTo: {to_email}\nSubject: TCDD Tren Bos Koltuk\n\n{message}"