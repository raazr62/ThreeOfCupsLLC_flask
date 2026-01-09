def get_match_notification_email(user_first_name=None, dashboard_url=None):
    """
    Generate match notification email content with dynamic and bracketed placeholders.

    Dynamic placeholders (replaced at send time):
        {first_name} - Recipient's first name (swaps based on who receives the email)
        {match_name} - Match's first name (swaps based on who receives the email)
        {user1_name} - Always refers to User 1 (does NOT swap)
        {user2_name} - Always refers to User 2 (does NOT swap)
        {dashboard_url} - Link to recipient's dashboard

    Bracketed placeholders (customized by admin):
        [values], [shared hobby], [friendship desire], etc. - Match details from assessments

    Args:
        user_first_name: Not used in template (placeholders used instead)
        dashboard_url: Not used in template (placeholders used instead)

    Returns:
        Tuple of (subject, body_text, body_html) with placeholders
    """
    subject = 'Your Three of Cups Match: Meet {match_name}!'

    body_text = '''Hi {first_name},

I'm so excited to introduce you to {match_name}! After carefully reviewing both of your assessments, I have a really good feeling about this match.

Here's why I think you two will connect:

You both ranked [values] in your top values, and you each expressed a desire for friendships where you can [friendship desire]. I noticed that {user1_name}, you mentioned wanting a friend who "[X]" and {user2_name}, you described yourself as someone who "[X]." That feels like a beautiful alignment.

You also have complementary [x such as communication styles]—{user1_name}, you're a thoughtful processor who likes time before difficult conversations, and {user2_name}, you're patient and prefer to understand someone's perspective before responding. I think you'll navigate conflict together with a lot of grace.

Some fun overlaps:
• You both love [shared hobby]
• You're both exploring [shared interest]
• You both value [shared value]

A gentle awareness: {user1_name}, you mentioned needing advance notice for plans, and {user2_name}, you tend to be more spontaneous. This could actually be a beautiful balance if you both communicate openly about your needs!

Next steps: I've sent this same message to both of you with each other's contact info. I encourage you to reach out within the next few days to set up a casual first meeting—coffee, a walk, whatever feels right.

Here are a few ideas from the Three of Cups team:

Contact info:
[Contact method and details]

I'm rooting for you both! Remember, not every match will become a lifelong friendship, and that's okay. Stay open, be yourselves, and see what unfolds.

With so much hope for beautiful connection,
Iris
'''

    body_html = '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
    <h2 style="color: #8B5CF6;">Your Three of Cups Match: Meet {match_name}!</h2>
    <p>Hi {first_name},</p>
    <p>I'm so excited to introduce you to <strong>{match_name}</strong>! After carefully reviewing both of your assessments, I have a really good feeling about this match.</p>

    <h3 style="color: #06B6D4; margin-top: 25px;">Here's why I think you two will connect:</h3>
    <p>You both ranked <strong>[values]</strong> in your top values, and you each expressed a desire for friendships where you can <strong>[friendship desire]</strong>. I noticed that {user1_name}, you mentioned wanting a friend who "[X]" and {user2_name}, you described yourself as someone who "[X]." That feels like a beautiful alignment.</p>

    <p>You also have complementary <strong>[x such as communication styles]</strong>—{user1_name}, you're a thoughtful processor who likes time before difficult conversations, and {user2_name}, you're patient and prefer to understand someone's perspective before responding. I think you'll navigate conflict together with a lot of grace.</p>

    <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h4 style="color: #8B5CF6; margin-top: 0;">Some fun overlaps:</h4>
        <ul style="margin: 10px 0;">
            <li>You both love <strong>[shared hobby]</strong></li>
            <li>You're both exploring <strong>[shared interest]</strong></li>
            <li>You both value <strong>[shared value]</strong></li>
        </ul>
    </div>

    <p style="background-color: #fff7ed; padding: 12px; border-left: 4px solid #f59e0b; border-radius: 4px;"><strong>A gentle awareness:</strong> {user1_name}, you mentioned needing advance notice for plans, and {user2_name}, you tend to be more spontaneous. This could actually be a beautiful balance if you both communicate openly about your needs!</p>

    <h3 style="color: #06B6D4; margin-top: 25px;">Next steps:</h3>
    <p>I've sent this same message to both of you with each other's contact info. I encourage you to reach out within the next few days to set up a casual first meeting—coffee, a walk, whatever feels right.</p>

    <p><strong>Here are a few ideas from the Three of Cups team:</strong></p>

    <div style="background-color: #f0f9ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h4 style="color: #06B6D4; margin-top: 0;">Contact info:</h4>
        <p>[Contact method and details]</p>
    </div>

    <p>I'm rooting for you both! Remember, not every match will become a lifelong friendship, and that's okay. Stay open, be yourselves, and see what unfolds.</p>

    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
    <p style="font-style: italic;">With so much hope for beautiful connection,<br>Iris</p>
</div>
'''

    return subject, body_text, body_html
