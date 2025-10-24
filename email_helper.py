from flask_mail import Message
from email_templates.password_reset import get_password_reset_email
from email_templates.match_notification import get_match_notification_email
from email_templates.email_verification import get_email_verification_email
from email_templates.email_change_notification import get_email_change_notification_email
from email_templates.email_change_verification import get_email_change_verification_email


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


def send_verification_email(mail, sender, user, verification_url):
    """
    Send an email verification email to a user.

    Args:
        mail: Flask-Mail instance
        sender: Email sender address
        user: User object with first_name and email attributes
        verification_url: The email verification URL

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject, body_text, body_html = get_email_verification_email(user.first_name, verification_url)

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
        print(f"Error sending verification email: {e}")
        return False


def send_email_change_notification(mail, sender, old_email, user_first_name, new_email):
    """
    Send an email change notification to the old email address.

    Args:
        mail: Flask-Mail instance
        sender: Email sender address
        old_email: The old (current) email address
        user_first_name: User's first name
        new_email: The new email address being requested

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject, body_text, body_html = get_email_change_notification_email(
            user_first_name, old_email, new_email
        )

        msg = Message(
            subject,
            sender=sender,
            recipients=[old_email]
        )
        msg.body = body_text
        msg.html = body_html

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email change notification: {e}")
        return False


def send_email_change_verification(mail, sender, new_email, user_first_name, verification_url, old_email):
    """
    Send an email change verification email to the new email address.

    Args:
        mail: Flask-Mail instance
        sender: Email sender address
        new_email: The new email address to verify
        user_first_name: User's first name
        verification_url: The verification URL
        old_email: The old email address (for context)

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject, body_text, body_html = get_email_change_verification_email(
            user_first_name, verification_url, old_email
        )

        msg = Message(
            subject,
            sender=sender,
            recipients=[new_email]
        )
        msg.body = body_text
        msg.html = body_html

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email change verification: {e}")
        return False
