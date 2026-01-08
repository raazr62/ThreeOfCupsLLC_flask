def get_walk_in_welcome_email(user_first_name, event_title, profile_completion_url):
    """
    Welcome email for walk-in attendees.

    Args:
        user_first_name: First name of the user
        event_title: Name of event they attended
        profile_completion_url: Link to complete their profile

    Returns:
        Tuple of (subject, body_text, body_html)
    """
    subject = f'welcome to three of cups, {user_first_name}!'

    body_text = f'''hi {user_first_name},

it was wonderful to meet you at {event_title}!

three of cups is a friendship-matching community that helps people find meaningful, lasting friendships. since you attended our event, we'd love for you to complete your profile and discover the connections waiting for you.

complete your profile here:
{profile_completion_url}

once you complete your profile, you'll be able to:
- take our friendship assessment
- get matched with compatible friends in your area
- access exclusive community events
- join a supportive network of people seeking authentic connections

⏰ this link will expire in 7 days, so don't wait too long!

we're excited to help you find your people.

with warmth,
the three of cups team

p.s. questions? just reply to this email - we're here to help!
'''

    body_html = f'''
<div style="font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #FFD1DC 0%, #FFB88C 40%, #FFD97D 100%); padding: 20px; border-radius: 16px;">
    <div style="background: linear-gradient(145deg, rgba(250, 247, 245, 0.98), rgba(255, 155, 155, 0.15)); backdrop-filter: blur(12px); border: 1px solid rgba(255, 155, 155, 0.3); padding: 40px; border-radius: 16px; box-shadow: 0 8px 32px rgba(255, 155, 155, 0.2);">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #2C2420; margin: 0 0 10px 0; font-size: 32px; font-family: 'Playfair Display', Georgia, serif;">three of cups</h1>
            <div style="width: 60px; height: 3px; background: linear-gradient(90deg, #FF9B9B, #FFB88C, #FFD97D); margin: 0 auto;"></div>
        </div>

        <h2 style="color: #2C2420; font-size: 24px; margin: 0 0 20px 0;">welcome, {user_first_name}!</h2>

        <p style="color: #2C2420; line-height: 1.7; font-size: 16px;">It was wonderful to meet you at <strong style="color: #D84315;">{event_title}</strong>!</p>

        <p style="color: #2C2420; line-height: 1.7; font-size: 16px;">Three of Cups is a friendship-matching community that helps people find meaningful, lasting friendships. Since you attended our event, we'd love for you to complete your profile and discover the connections waiting for you.</p>

        <div style="text-align: center; margin: 35px 0;">
            <a href="{profile_completion_url}"
               style="background: linear-gradient(135deg, #FF9B9B, #FFB88C, #FFD97D);
                      color: #2C2420;
                      padding: 16px 40px;
                      text-decoration: none;
                      border-radius: 12px;
                      font-weight: bold;
                      font-size: 16px;
                      display: inline-block;
                      box-shadow: 0 4px 16px rgba(255, 155, 155, 0.4);
                      transition: all 0.3s ease;">
                Complete Your Profile
            </a>
        </div>

        <div style="background: linear-gradient(145deg, rgba(255, 217, 125, 0.2), rgba(255, 184, 140, 0.2)); padding: 24px; border-left: 4px solid #FFB88C; border-radius: 8px; margin: 25px 0;">
            <h3 style="color: #D84315; margin-top: 0; font-size: 17px; font-weight: 600;">Once you complete your profile, you'll be able to:</h3>
            <ul style="color: #2C2420; line-height: 1.8; margin: 10px 0; padding-left: 20px;">
                <li style="margin-bottom: 8px;">Take our friendship assessment</li>
                <li style="margin-bottom: 8px;">Get matched with compatible friends in your area</li>
                <li style="margin-bottom: 8px;">Access exclusive community events</li>
                <li style="margin-bottom: 8px;">Join a supportive network of people seeking authentic connections</li>
            </ul>
        </div>

        <div style="background: rgba(255, 155, 155, 0.1); padding: 16px; border-radius: 8px; margin: 25px 0; text-align: center;">
            <p style="color: #D84315; font-size: 14px; margin: 0; font-weight: 600;">⏰ This link will expire in 7 days, so don't wait too long!</p>
        </div>

        <p style="color: #2C2420; line-height: 1.7; font-size: 16px; margin-top: 30px;">We're excited to help you find your people.</p>

        <p style="color: #2C2420; font-style: italic; margin-top: 24px; font-size: 15px;">
            With warmth,<br>
            <strong style="color: #D84315;">The Three of Cups Team</strong>
        </p>

        <hr style="margin: 30px 0; border: none; border-top: 1px solid rgba(255, 155, 155, 0.2);">

        <p style="color: #2C2420; font-size: 13px; opacity: 0.7;">
            <strong>P.S.</strong> Questions? Just reply to this email - we're here to help!
        </p>
    </div>
</div>
'''

    return subject, body_text, body_html
