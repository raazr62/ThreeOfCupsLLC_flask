def get_match_notification_email(user_first_name, dashboard_url):
    """
    Generate match notification email content.

    Args:
        user_first_name: The first name of the user who received a match
        dashboard_url: The URL to the user's dashboard

    Returns:
        Tuple of (subject, body_text, body_html)
    """
    subject = 'You have a new match! - Three of Cups'

    body_text = f'''Hello {user_first_name},

Great news! You have received a new friendship match on Three of Cups.

Visit your dashboard to view your new match and start connecting:
{dashboard_url}

We're excited for you to begin this new friendship journey!

Best regards,
the three of cups team
'''

    body_html = f'''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #333;">You Have a New Match!</h2>
    <p>Hello {user_first_name},</p>
    <p>Great news! You have received a new friendship match on Three of Cups.</p>
    <p>Visit your dashboard to view your new match and start connecting:</p>
    <div style="text-align: center; margin: 30px 0;">
        <a href="{dashboard_url}" style="background-color: #8B5CF6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 8px; display: inline-block;">View Your Match</a>
    </div>
    <p style="color: #666; font-size: 14px;">Or copy and paste this link into your browser:</p>
    <p style="color: #8B5CF6; word-break: break-all;">{dashboard_url}</p>
    <p>We're excited for you to begin this new friendship journey!</p>
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
    <p style="color: #999; font-size: 12px;">Best regards,<br>The Three of Cups Team</p>
</div>
'''

    return subject, body_text, body_html
