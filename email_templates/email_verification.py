def get_email_verification_email(user_first_name, verification_url):
    """
    Generate email verification email content.

    Args:
        user_first_name: The first name of the user
        verification_url: The email verification URL

    Returns:
        Tuple of (subject, body_text, body_html)
    """
    subject = 'Verify Your Email - Three of Cups'

    body_text = f'''Hello {user_first_name},

Welcome to Three of Cups! We're excited to help you find meaningful friendships.

Please verify your email address by clicking the link below:
{verification_url}

This link will expire in 24 hours.

Once your email is verified, you'll unlock full access to view your matches and connect with potential friends!

If you did not create an account with Three of Cups, please ignore this email.

Best regards,
the three of cups team
'''

    body_html = f'''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #333;">Welcome to Three of Cups!</h2>
    <p>Hello {user_first_name},</p>
    <p>Thank you for joining Three of Cups! We're excited to help you find meaningful friendships.</p>
    <p>To get started, please verify your email address by clicking the button below:</p>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{verification_url}" style="background-color: #8B5CF6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; display: inline-block;">Verify Email Address</a>
    </div>
    <p style="color: #666; font-size: 14px;">Or copy and paste this link into your browser:</p>
    <p style="color: #8B5CF6; word-break: break-all;">{verification_url}</p>
    <p style="color: #666; font-size: 14px;">This link will expire in 24 hours.</p>
    <p style="background-color: #f0f9ff; padding: 15px; border-left: 4px solid #8B5CF6; margin: 20px 0;">
        <strong>What's Next?</strong><br>
        Once your email is verified, you'll unlock full access to view your matches and connect with potential friends!
    </p>
    <p style="color: #666; font-size: 14px;">If you did not create an account with Three of Cups, please ignore this email.</p>
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
    <p style="color: #999; font-size: 12px;">Best regards,<br>The Three of Cups Team</p>
</div>
'''

    return subject, body_text, body_html
