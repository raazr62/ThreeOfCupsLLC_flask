from flask_mail import Message
from email_templates.password_reset import get_password_reset_email
from email_templates.match_notification import get_match_notification_email


def send_password_reset_email(mail, sender, user, reset_url):
    """
    Send a password reset email to a user.

    Args:
        mail: Flask-Mail instance
        sender: Email sender address
        user: User object with first_name and email attributes
        reset_url: The password reset URL

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject, body_text, body_html = get_password_reset_email(user.first_name, reset_url)

        msg = Message(
            subject,
            sender=sender,
            recipients=[user.email]
        )
        msg.body = body_text
        msg.html = body_html

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False


def send_match_notification_email(mail, sender, user, dashboard_url):
    """
    Send a match notification email to a user.

    Args:
        mail: Flask-Mail instance
        sender: Email sender address
        user: User object with first_name and email attributes
        dashboard_url: The URL to the user's dashboard

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject, body_text, body_html = get_match_notification_email(user.first_name, dashboard_url)

        msg = Message(
            subject,
            sender=sender,
            recipients=[user.email]
        )
        msg.body = body_text
        msg.html = body_html

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending match notification email: {e}")
        return False
