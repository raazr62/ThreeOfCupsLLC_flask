def get_email_change_notification_email(user_first_name, old_email, new_email):
    """
    Generate email change notification email content (sent to old email).

    Args:
        user_first_name: The first name of the user
        old_email: The current (old) email address
        new_email: The new email address being requested

    Returns:
        Tuple of (subject, body_text, body_html)
    """
    subject = 'Email Address Change Request - Three of Cups'

    body_text = f'''Hello {user_first_name},

We're writing to inform you that a request has been made to change the email address associated with your Three of Cups account.

Current email: {old_email}
New email: {new_email}

A verification email has been sent to the new email address. Your account email will only be updated after the new email address is verified.

If you did not make this request, please log in to your account immediately and secure your account by changing your password.

Best regards,
The Three of Cups Team
'''

    body_html = f'''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #333;">Email Address Change Request</h2>
    <p>Hello {user_first_name},</p>
    <p>We're writing to inform you that a request has been made to change the email address associated with your Three of Cups account.</p>

    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <p style="margin: 5px 0;"><strong>Current email:</strong> {old_email}</p>
        <p style="margin: 5px 0;"><strong>New email:</strong> {new_email}</p>
    </div>

    <p>A verification email has been sent to the new email address. Your account email will only be updated after the new email address is verified.</p>

    <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
        <strong style="color: #856404;">Security Notice</strong>
        <p style="color: #856404; margin: 10px 0 0 0;">If you did not make this request, please log in to your account immediately and secure your account by changing your password.</p>
    </div>

    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
    <p style="color: #999; font-size: 12px;">Best regards,<br>The Three of Cups Team</p>
</div>
'''

    return subject, body_text, body_html
