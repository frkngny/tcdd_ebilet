
class UnsupportedNotificationChannelError(Exception):
    """Raised when an unsupported notification channel is provided."""

def get_notification_client(channel: str):
    if channel == "email":
        from .email_client import EmailClient
        return EmailClient()
    else:
        raise UnsupportedNotificationChannelError(
            f"Notification channel '{channel}' is not supported"
        )