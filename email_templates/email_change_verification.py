def get_email_change_verification_email(user_first_name, verification_url, old_email):
    """
    Generate email change verification email content (sent to new email).

    Args:
        user_first_name: The first name of the user
        verification_url: The email verification URL
        old_email: The old email address (for context)

    Returns:
        Tuple of (subject, body_text, body_html)
    """
    subject = 'Verify Your New Email Address - Three of Cups'

    body_text = f'''Hello {user_first_name},

You requested to change the email address for your Three of Cups account from {old_email} to this email address.

Please verify this new email address by clicking the link below:
{verification_url}

This link will expire in 24 hours.

Once verified, this will become your new login email address for Three of Cups.

If you did not request this change, please ignore this email. Your account email will not be changed unless you click the verification link.

Best regards,
The Three of Cups Team
'''

    body_html = f'''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #333;">Verify Your New Email Address</h2>
    <p>Hello {user_first_name},</p>
    <p>You requested to change the email address for your Three of Cups account from <strong>{old_email}</strong> to this email address.</p>
    <p>To complete this change, please verify your new email address by clicking the button below:</p>

    <div style="text-align: center; margin: 30px 0;">
        <a href="{verification_url}" style="background-color: #8B5CF6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; display: inline-block;">Verify New Email Address</a>
    </div>

    <p style="color: #666; font-size: 14px;">Or copy and paste this link into your browser:</p>
    <p style="color: #8B5CF6; word-break: break-all;">{verification_url}</p>
    <p style="color: #666; font-size: 14px;">This link will expire in 24 hours.</p>

    <div style="background-color: #f0f9ff; padding: 15px; border-left: 4px solid #8B5CF6; margin: 20px 0;">
        <strong>What Happens Next?</strong>
        <p style="margin: 10px 0 0 0;">Once verified, this will become your new login email address for Three of Cups. You'll use this email for all future logins and communications.</p>
    </div>

    <p style="color: #666; font-size: 14px;">If you did not request this change, please ignore this email. Your account email will not be changed unless you click the verification link.</p>

    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
    <p style="color: #999; font-size: 12px;">Best regards,<br>The Three of Cups Team</p>
</div>
'''

    return subject, body_text, body_html
