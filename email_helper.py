from flask_mail import Message
from email_templates.password_reset import get_password_reset_email
from email_templates.match_notification import get_match_notification_email
from email_templates.email_verification import get_email_verification_email
from email_templates.email_change_notification import get_email_change_notification_email
from email_templates.email_change_verification import get_email_change_verification_email


def sanitize_email_content(text):
    """
    Aggressively sanitize email content to remove ALL non-ASCII characters for SMTP compatibility.
    This includes Unicode punctuation, emojis, and any other characters that could cause encoding issues.

    Strategy:
    1. First replace common Unicode characters with ASCII equivalents
    2. Then strip any remaining non-ASCII characters (including emojis)
    """
    if not text:
        return text

    # First pass: Replace common Unicode punctuation with ASCII equivalents
    replacements = {
        '\u2014': '--',          # Em dash
        '\u2013': '-',           # En dash
        '\u2018': "'",           # Left single quote
        '\u2019': "'",           # Right single quote
        '\u201c': '"',           # Left double quote
        '\u201d': '"',           # Right double quote
        '\u2026': '...',         # Ellipsis
        '\u2022': '*',           # Bullet point
        '\U0001f31f': '',        # Star emoji 🌟
        '\U0001f4ab': '',        # Dizzy emoji 💫
        '\U0001f493': '',        # Beating heart emoji 💓
        '\U0001f49c': '',        # Purple heart emoji 💜
        '\u2764\ufe0f': '',      # Red heart emoji ❤️
        '\u2764': '',            # Red heart (without variation selector)
    }

    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)

    # Second pass: Aggressively remove any remaining non-ASCII characters
    # This catches any emojis or Unicode characters we didn't explicitly map
    try:
        # Encode to ASCII, replacing any characters that can't be encoded
        text = text.encode('ascii', 'ignore').decode('ascii')
    except Exception as e:
        print(f"Warning: Error during ASCII sanitization: {e}")

    return text


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
        # Sanitize content to remove all non-ASCII characters
        msg.body = sanitize_email_content(body_text)
        msg.html = sanitize_email_content(body_html)
        msg.charset = 'utf-8'

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False


def send_match_notification_email(mail, sender, user, match_name, dashboard_url):
    """
    Send a match notification email to a user.

    Args:
        mail: Flask-Mail instance
        sender: Email sender address
        user: User object with first_name and email attributes
        match_name: The first name of the matched user
        dashboard_url: The URL to the user's dashboard

    Returns:
        tuple: (success: bool, html_content: str or None) - True/HTML if email sent successfully, False/None otherwise
    """
    try:
        subject, body_text, body_html = get_match_notification_email(user.first_name, dashboard_url)

        # Replace placeholders with actual values
        subject = subject.replace('{first_name}', user.first_name).replace('{match_name}', match_name).replace('{dashboard_url}', dashboard_url)
        body_text = body_text.replace('{first_name}', user.first_name).replace('{match_name}', match_name).replace('{dashboard_url}', dashboard_url)
        body_html = body_html.replace('{first_name}', user.first_name).replace('{match_name}', match_name).replace('{dashboard_url}', dashboard_url)

        # Aggressively sanitize all content to remove non-ASCII characters (including emojis)
        subject = sanitize_email_content(subject)
        body_text = sanitize_email_content(body_text)
        body_html = sanitize_email_content(body_html)

        msg = Message(
            subject,
            sender=sender,
            recipients=[user.email]
        )
        msg.body = body_text
        msg.html = body_html
        # Set UTF-8 charset for proper Unicode handling
        msg.charset = 'utf-8'

        mail.send(msg)
        return True, body_text
    except Exception as e:
        print(f"Error sending match notification email: {e}")
        return False, None


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
        # Sanitize content to remove all non-ASCII characters
        msg.body = sanitize_email_content(body_text)
        msg.html = sanitize_email_content(body_html)
        msg.charset = 'utf-8'

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
        # Sanitize content to remove all non-ASCII characters
        msg.body = sanitize_email_content(body_text)
        msg.html = sanitize_email_content(body_html)
        msg.charset = 'utf-8'

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
        # Sanitize content to remove all non-ASCII characters
        msg.body = sanitize_email_content(body_text)
        msg.html = sanitize_email_content(body_html)
        msg.charset = 'utf-8'

        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email change verification: {e}")
        return False
