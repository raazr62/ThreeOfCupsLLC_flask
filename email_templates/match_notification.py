def get_match_notification_email(user_first_name=None, dashboard_url=None):
    """
    Generate match notification email content with dynamic and bracketed placeholders.

    Dynamic placeholders (replaced at send time):
        {user1_name} - Always refers to User 1
        {user2_name} - Always refers to User 2
        {dashboard_url} - Link to the user dashboard

    Bracketed placeholders (customized by admin):
        [values], [shared hobby], [friendship desire], etc. - Match details from assessments

    Args:
        user_first_name: Not used in template (placeholders used instead)
        dashboard_url: Not used in template (placeholders used instead)

    Returns:
        Tuple of (subject, body_text, body_html) with placeholders
    """
    subject = 'Your Three of Cups Match: {user1_name} and {user2_name}!'

    body_text = '''Hi {user1_name} and {user2_name},

I'm so excited to introduce you both to each other! {user2_name}, meet {user1_name} ({user1_pronouns})! {user1_name}, meet {user2_name} ({user2_pronouns})! After carefully reviewing both of your assessments, I have a really good feeling about this match.

Here's why I think you two will connect:
You both ranked [values] in your top values. I noticed that {user1_name}, you mentioned desiring a friend that [user1 friendship desire], and {user2_name}, you mentioned desiring a friendship that [user2 friendship desire]! This feels like a great match.

Some fun overlaps:
• You both enjoy [shared hobby/interest]
• You both are seeking [shared friendship goal]
• You both receive connection best through [shared connection style]

A gentle awareness: {user1_name}, you [user1 preference], while {user2_name}, you [user2 preference]. This could actually work well together with intentionality and communication!

Next steps: I've sent this same message to both of you with each other's contact info. I encourage you to reach out within the next few days to set up a casual first meeting—coffee, a walk, whatever feels right.

Here are a few more ideas from the Three of Cups team:
• Share a new hobby together
• Attend a social event or market together
• [Additional idea]

Contact info:
You both are CC'd on this email, so feel free to reach out individually!

I'm rooting for you both! Remember, not every match will become a lifelong friendship, and that's okay. Stay open, be yourselves, and see what unfolds.

With so much hope for beautiful connection,
The Three of Cups Team
'''

    body_html = '''
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
    <div style="background-color: #FF9B9B; width: 100%; padding: 24px 0; text-align: center; margin-bottom: 24px;">
        <img src="{logo_url}" alt="Three of Cups" style="max-height: 80px; display: inline-block;">
    </div>
    <p>Hi <strong>{user1_name}</strong> and <strong>{user2_name}</strong>,</p>
    <p>I'm so excited to introduce you both to each other! <strong>{user2_name}</strong>, meet <strong>{user1_name}</strong> (<strong>{user1_pronouns}</strong>)! <strong>{user1_name}</strong>, meet <strong>{user2_name}</strong> (<strong>{user2_pronouns}</strong>)! After carefully reviewing both of your assessments, I have a really good feeling about this match.</p>

    <p><strong>Here's why I think you two will connect:</strong><br>
    You both ranked [values] in your top values. I noticed that {user1_name}, you mentioned desiring a friend that [user1 friendship desire], and {user2_name}, you mentioned desiring a friendship that [user2 friendship desire]! This feels like a great match.</p>

    <p><strong>Some fun overlaps:</strong><br>
    • You both enjoy [shared hobby/interest]<br>
    • You both are seeking [shared friendship goal]<br>
    • You both receive connection best through [shared connection style]</p>

    <p><strong>A gentle awareness:</strong> {user1_name}, you [user1 preference], while {user2_name}, you [user2 preference]. This could actually work well together with intentionality and communication!</p>

    <p><strong>Next steps:</strong> I've sent this same message to both of you with each other's contact info. I encourage you to reach out within the next few days to set up a casual first meeting—coffee, a walk, whatever feels right.</p>

    <p>Here are a few more ideas from the Three of Cups team:<br>
    • Share a new hobby together<br>
    • Attend a social event or market together<br>
    • [Additional idea]</p>

    <p><strong>Contact info:</strong><br>
    You both are CC'd on this email, so feel free to reach out individually!</p>

    <p>I'm rooting for you both! Remember, not every match will become a lifelong friendship, and that's okay. Stay open, be yourselves, and see what unfolds.</p>

    <p>With so much hope for beautiful connection,<br>The Three of Cups Team</p>

    <hr style="border: none; border-top: 2px solid #FF9B9B; margin: 24px 0;">
    <p><a href="https://linktr.ee/threeofcupsllc" style="color: #FF9B9B;">follow us for more opportunities to connect!</a></p>
</div>
'''

    return subject, body_text, body_html
