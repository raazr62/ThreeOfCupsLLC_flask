"""
Security utilities for XSS prevention and input sanitization.
"""
import re
import bleach
from html import escape
from markupsafe import Markup


# Allowed HTML tags and attributes for rich text (if needed in the future)
ALLOWED_TAGS = []  # Currently no HTML allowed
ALLOWED_ATTRIBUTES = {}
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html(text, allow_tags=False):
    """
    Sanitize HTML content to prevent XSS attacks.

    Args:
        text: The text to sanitize
        allow_tags: If True, allows safe HTML tags. Default is False (strips all HTML)

    Returns:
        Sanitized text safe for display
    """
    if text is None:
        return ''

    if not isinstance(text, str):
        text = str(text)

    if allow_tags:
        # Use bleach to sanitize while allowing specific tags
        cleaned = bleach.clean(
            text,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True
        )
    else:
        # Strip all HTML tags
        cleaned = bleach.clean(text, tags=[], strip=True)

    # Remove dangerous protocols (javascript:, data:, vbscript:, etc.)
    dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:', 'about:']
    for protocol in dangerous_protocols:
        if protocol in cleaned.lower():
            # Remove the dangerous protocol
            cleaned = re.sub(re.escape(protocol), '', cleaned, flags=re.IGNORECASE)

    return cleaned


def sanitize_input(text, max_length=None, allow_newlines=True):
    """
    Sanitize user input by removing potentially dangerous content.

    Args:
        text: The text to sanitize
        max_length: Maximum allowed length (optional)
        allow_newlines: Whether to allow newline characters

    Returns:
        Sanitized text
    """
    if text is None:
        return ''

    if not isinstance(text, str):
        text = str(text)

    # Strip leading/trailing whitespace
    text = text.strip()

    # Remove null bytes
    text = text.replace('\x00', '')

    # Sanitize HTML
    text = sanitize_html(text, allow_tags=False)

    # Remove dangerous protocols (javascript:, data:, vbscript:)
    dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:', 'about:']
    text_lower = text.lower()
    for protocol in dangerous_protocols:
        if protocol in text_lower:
            # Remove the dangerous protocol
            text = re.sub(re.escape(protocol), '', text, flags=re.IGNORECASE)

    # Remove newlines if not allowed
    if not allow_newlines:
        text = text.replace('\n', ' ').replace('\r', ' ')
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)

    # Enforce max length
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def sanitize_email(email):
    """
    Sanitize and validate email address.

    Args:
        email: Email address to sanitize

    Returns:
        Sanitized email in lowercase
    """
    if not email:
        return ''

    email = str(email).strip().lower()

    # Remove null bytes and HTML
    email = email.replace('\x00', '')
    email = sanitize_html(email, allow_tags=False)

    # Basic email validation pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return ''

    return email


def sanitize_username(username):
    """
    Sanitize username to allow only safe characters.

    Args:
        username: Username to sanitize

    Returns:
        Sanitized username
    """
    if not username:
        return ''

    username = str(username).strip()

    # Remove HTML and dangerous characters
    username = sanitize_html(username, allow_tags=False)

    # Only allow alphanumeric, underscore, hyphen, and period
    username = re.sub(r'[^a-zA-Z0-9._-]', '', username)

    return username


def sanitize_location(location):
    """
    Sanitize location string.

    Args:
        location: Location string to sanitize

    Returns:
        Sanitized location
    """
    if not location:
        return ''

    location = sanitize_input(location, max_length=200, allow_newlines=False)

    return location


def sanitize_json_data(data):
    """
    Recursively sanitize JSON data structure.

    Args:
        data: Dictionary or list to sanitize

    Returns:
        Sanitized data structure
    """
    if isinstance(data, dict):
        return {key: sanitize_json_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_json_data(item) for item in data]
    elif isinstance(data, str):
        return sanitize_input(data)
    else:
        return data


def escape_for_html(text):
    """
    Escape text for safe display in HTML context.
    This is a wrapper around html.escape for consistency.

    Args:
        text: Text to escape

    Returns:
        HTML-escaped text
    """
    if text is None:
        return ''

    return escape(str(text))


def validate_file_upload(filename):
    """
    Validate uploaded filename for security.

    Args:
        filename: The filename to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not filename:
        return False, "No filename provided"

    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]

    # Check for null bytes
    if '\x00' in filename:
        return False, "Invalid filename"

    # Check for dangerous extensions
    dangerous_extensions = [
        '.exe', '.bat', '.cmd', '.sh', '.ps1', '.php', '.jsp',
        '.asp', '.aspx', '.js', '.vbs', '.scr', '.pif', '.application'
    ]

    filename_lower = filename.lower()
    for ext in dangerous_extensions:
        if filename_lower.endswith(ext):
            return False, f"File type {ext} not allowed"

    # Check for allowed image extensions
    allowed_extensions = ['.png', '.jpg', '.jpeg', '.gif']
    if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
        return False, "Only PNG, JPG, JPEG, and GIF files are allowed"

    return True, ""


# Context processor for templates to ensure auto-escaping is enabled
def setup_template_filters(app):
    """
    Set up custom template filters for additional security.

    Args:
        app: Flask application instance
    """

    @app.template_filter('sanitize')
    def sanitize_filter(text):
        """Custom template filter for sanitizing text."""
        return sanitize_html(text, allow_tags=False)

    @app.context_processor
    def security_context():
        """Inject security utilities into template context."""
        return {
            'escape': escape_for_html,
        }
