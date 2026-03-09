from flask_mail import Message
from email_templates.password_reset import get_password_reset_email
from email_templates.match_notification import get_match_notification_email
from email_templates.email_verification import get_email_verification_email
from email_templates.email_change_notification import get_email_change_notification_email
from email_templates.email_change_verification import get_email_change_verification_email
from email_templates.walk_in_welcome import get_walk_in_welcome_email


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


def send_match_notification_email(mail, sender, user, match_name, dashboard_url, user1_name=None, user2_name=None):
    """
    Send a match notification email to a user.

    Args:
        mail: Flask-Mail instance
        sender: Email sender address
        user: User object with first_name and email attributes
        match_name: The first name of the matched user
        dashboard_url: The URL to the user's dashboard
        user1_name: First name of user1 (for fixed placeholder)
        user2_name: First name of user2 (for fixed placeholder)

    Returns:
        tuple: (success: bool, html_content: str or None) - True/HTML if email sent successfully, False/None otherwise
    """
    try:
        subject, body_text, body_html = get_match_notification_email(user.first_name, dashboard_url)

        # Replace placeholders with actual values
        subject = subject.replace('{first_name}', user.first_name).replace('{match_name}', match_name).replace('{dashboard_url}', dashboard_url)
        body_text = body_text.replace('{first_name}', user.first_name).replace('{match_name}', match_name).replace('{dashboard_url}', dashboard_url)
        body_html = body_html.replace('{first_name}', user.first_name).replace('{match_name}', match_name).replace('{dashboard_url}', dashboard_url)

        if user1_name:
            subject = subject.replace('{user1_name}', user1_name)
            body_text = body_text.replace('{user1_name}', user1_name)
            body_html = body_html.replace('{user1_name}', user1_name)
        if user2_name:
            subject = subject.replace('{user2_name}', user2_name)
            body_text = body_text.replace('{user2_name}', user2_name)
            body_html = body_html.replace('{user2_name}', user2_name)

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


def send_rsvp_admin_notification(mail, sender, admin_email, user, event, energy_exchange_amount=None):
    """
    Notify admin when a user finalizes an RSVP (with energy exchange confirmation).

    Args:
        mail: Flask-Mail instance
        sender: Email sender address
        admin_email: Admin recipient email
        user: User who RSVPd
        event: Event object
        energy_exchange_amount: String describing the energy exchange amount (e.g. "$25" or "$20-$35")

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f"New RSVP: {user.first_name} {user.last_name} for {event.title}"

        body_text = (
            f"A new RSVP has been submitted!\n\n"
            f"Event: {event.title}\n"
            f"Date: {event.date_time.strftime('%A, %B %d, %Y at %I:%M %p')}\n\n"
            f"Attendee: {user.first_name} {user.last_name}\n"
            f"Email: {user.email}\n\n"
        )

        if energy_exchange_amount:
            body_text += (
                f"Energy Exchange: {energy_exchange_amount}\n"
                f"The attendee has indicated they sent their energy exchange via Venmo @threeofcupsllc.\n\n"
                f"Please check Venmo, verify the transaction, and update their payment status in the admin events page.\n"
            )

        body_html = (
            f"<h2>New RSVP!</h2>"
            f"<p><strong>Event:</strong> {event.title}</p>"
            f"<p><strong>Date:</strong> {event.date_time.strftime('%A, %B %d, %Y at %I:%M %p')}</p>"
            f"<hr>"
            f"<p><strong>Attendee:</strong> {user.first_name} {user.last_name}</p>"
            f"<p><strong>Email:</strong> {user.email}</p>"
        )

        if energy_exchange_amount:
            body_html += (
                f"<p><strong>Energy Exchange:</strong> {energy_exchange_amount}</p>"
                f"<p>The attendee has indicated they sent their energy exchange via Venmo @threeofcupsllc.</p>"
                f"<p><strong>Please check Venmo, verify the transaction, and update their payment status "
                f"in the admin events page (View Energy Exchanges).</strong></p>"
            )

        msg = Message(subject, sender=sender, recipients=[admin_email])
        msg.body = sanitize_email_content(body_text)
        msg.html = sanitize_email_content(body_html)
        msg.charset = 'utf-8'
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending RSVP admin notification: {e}")
        return False


def send_rsvp_cancellation_admin_notification(mail, sender, admin_email, user, event):
    """
    Notify admin when a user cancels their RSVP.

    Args:
        mail: Flask-Mail instance
        sender: Email sender address
        admin_email: Admin recipient email
        user: User who cancelled
        event: Event object

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        subject = f"RSVP Cancelled: {user.first_name} {user.last_name} for {event.title}"

        body_text = (
            f"An RSVP has been cancelled.\n\n"
            f"Event: {event.title}\n"
            f"Date: {event.date_time.strftime('%A, %B %d, %Y at %I:%M %p')}\n\n"
            f"Attendee: {user.first_name} {user.last_name}\n"
            f"Email: {user.email}\n"
        )

        body_html = (
            f"<h2>RSVP Cancelled</h2>"
            f"<p><strong>Event:</strong> {event.title}</p>"
            f"<p><strong>Date:</strong> {event.date_time.strftime('%A, %B %d, %Y at %I:%M %p')}</p>"
            f"<hr>"
            f"<p><strong>Attendee:</strong> {user.first_name} {user.last_name}</p>"
            f"<p><strong>Email:</strong> {user.email}</p>"
        )

        msg = Message(subject, sender=sender, recipients=[admin_email])
        msg.body = sanitize_email_content(body_text)
        msg.html = sanitize_email_content(body_html)
        msg.charset = 'utf-8'
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending RSVP cancellation admin notification: {e}")
        return False


def send_walk_in_welcome_email(mail, sender, user, event_title, profile_completion_url):
    """
    Send welcome email to walk-in attendee with profile completion link.

    Args:
        mail: Flask-Mail instance
        sender: Sender email address
        user: User object
        event_title: Name of event they attended
        profile_completion_url: URL to complete profile

    Returns:
        Tuple (success: bool, error_message: str or None)
    """
    try:
        subject, body_text, body_html = get_walk_in_welcome_email(
            user.first_name,
            event_title,
            profile_completion_url
        )

        msg = Message(
            subject=subject,
            sender=sender,
            recipients=[user.email]
        )
        msg.body = sanitize_email_content(body_text)
        msg.html = sanitize_email_content(body_html)
        msg.charset = 'utf-8'

        mail.send(msg)
        return True, None
    except Exception as e:
        print(f"Error sending walk-in welcome email: {e}")
        return False, str(e)
