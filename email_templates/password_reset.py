def get_password_reset_email(user_first_name, reset_url):
    """
    Generate password reset email content.

    Args:
        user_first_name: The first name of the user
        reset_url: The password reset URL

    Returns:
        Tuple of (subject, body_text, body_html)
    """
    subject = 'Password Reset Request - Three of Cups'

    body_text = f'''Hello {user_first_name},

You requested to reset your password for your Three of Cups account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email and your password will remain unchanged.

Best regards,
the three of cups team
'''

    body_html = f'''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #333;">Password Reset Request</h2>
    <p>Hello {user_first_name},</p>
    <p>You requested to reset your password for your Three of Cups account.</p>
    <p>Click the button below to reset your password:</p>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{reset_url}" style="background-color: #8B5CF6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; display: inline-block;">Reset Password</a>
    </div>
    <p style="color: #666; font-size: 14px;">Or copy and paste this link into your browser:</p>
    <p style="color: #8B5CF6; word-break: break-all;">{reset_url}</p>
    <p style="color: #666; font-size: 14px;">This link will expire in 1 hour.</p>
    <p style="color: #666; font-size: 14px;">If you did not request this password reset, please ignore this email and your password will remain unchanged.</p>
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
    <p style="color: #999; font-size: 12px;">Best regards,<br>The Three of Cups Team</p>
</div>
'''

    return subject, body_text, body_html
