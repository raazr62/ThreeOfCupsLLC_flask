"""
Backfill the service table with the services that were previously hardcoded
in templates/services.html.

Run AFTER migrate_services.py:
    python3 migrate_services.py
    python3 backfill_services.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'friendship.db')

SERVICES = [
    {
        'name': 'basic reading via voice recording',
        'price_display': '$15',
        'description': (
            "A personalized tarot reading delivered through a voice recording! "
            "Whether it's career, love, personal growth, or friendships, I'll send you "
            "a voice recording where I mindfully draw cards and walk you through each "
            "card's meaning and how they relate to your situation.\n\n"
            "Delivered within 3-5 business days!"
        ),
        'sort_order': 0,
        'is_active': 1,
    },
    {
        'name': 'joint friendship reading via voice recording',
        'price_display': '$20',
        'description': (
            "Need a little bit more guidance in your friendship? This reading explores "
            "the current state of your friendship, underlying dynamics, and ways you both "
            "complement each other. I'll send you both a voice recording where I draw cards "
            "and walk both of you through each card's meaning and how they relate to your "
            "friendship.\n\n"
            "Delivered within 3-5 business days!"
        ),
        'sort_order': 1,
        'is_active': 1,
    },
    {
        'name': 'basic friendship reading + 3 questions',
        'price_display': '$30',
        'description': (
            "This offering is for those who want to dive deeper into their social wellness. "
            "With this comprehensive reading, you will receive a voice recording that explores "
            "your overall friendship dynamic. After pulling cards and explaining each meaning "
            "as it relates to your friendship life, I'll then answer three questions you submit "
            "ahead of time.\n\n"
            "Delivered within 3-5 business days!"
        ),
        'sort_order': 2,
        'is_active': 1,
    },
    {
        'name': 'basic reading via voice recording + 3 questions',
        'price_display': '$25',
        'description': (
            "A personalized tarot reading on your chosen topic, plus the opportunity to ask "
            "three specific follow-up questions. This offering allows you to explore your "
            "situation broadly first, and then zoom in on particular aspects that matter most "
            "to you. Whether it's career, love, personal growth, or life decisions, you'll "
            "receive a comprehensive voice recording that addresses both the big picture and "
            "your specific concerns.\n\n"
            "Delivered within 3-5 business days!"
        ),
        'sort_order': 3,
        'is_active': 1,
    },
    {
        'name': 'friendship guidance reading',
        'price_display': '$10',
        'description': (
            "This streamlined reading offers quick and meaningful insight into a friendship "
            "question or concern delivered through a voice recording. Ideal for check-ins, "
            "follow-up questions, or those wanting an introduction into tarot.\n\n"
            "Delivered within 3-5 business days!"
        ),
        'sort_order': 4,
        'is_active': 1,
    },
    {
        'name': 'reading via zoom + 3 questions (45 minutes)',
        'price_display': '$40',
        'description': (
            "A live, interactive tarot reading from the comfort of your home! During our "
            "45-minute Zoom session, we'll explore your primary concern through a tarot spread, "
            "then address three questions of your choice. This format allows for real-time "
            "discussion, clarification, and deeper exploration of the cards' messages. You'll "
            "leave with insights and a clearer perspective.\n\n"
            "Delivered within 3-5 business days!"
        ),
        'sort_order': 5,
        'is_active': 1,
    },
    {
        'name': 'joint friendship reading via zoom (1 hour)',
        'price_display': '$60 - 2 questions each',
        'description': (
            "A unique offering for friends who want to explore their friendship together. "
            "In this one-hour Zoom session, you, a pal, and I will read the cards to illuminate "
            "your friendship's strengths, challenges, and growth opportunities. Each person will "
            "get a chance to ask two questions, creating space for mutual understanding and deeper "
            "connection. This collaborative experience can strengthen bonds and provide insights "
            "for navigating your friendship with greater awareness and care.\n\n"
            "Delivered within 3-5 business days!"
        ),
        'sort_order': 6,
        'is_active': 1,
    },
    {
        'name': 'friendship coaching',
        'price_display': '(to be offered soon!)',
        'description': "Think couple's counseling but for friendship. Stay tuned for more!",
        'sort_order': 7,
        'is_active': 1,
    },
    {
        'name': 'life coaching',
        'price_display': '(to be offered soon!)',
        'description': 'Coming soon!',
        'sort_order': 8,
        'is_active': 1,
    },
]


def backfill():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute('SELECT COUNT(*) FROM service')
    count = cur.fetchone()[0]
    if count > 0:
        print(f'service table already has {count} rows — skipping backfill.')
        print('Delete existing rows first if you want to re-run the backfill.')
        conn.close()
        return

    cur.executemany(
        """
        INSERT INTO service (name, price_display, description, sort_order, is_active)
        VALUES (:name, :price_display, :description, :sort_order, :is_active)
        """,
        SERVICES,
    )
    conn.commit()
    print(f'Inserted {len(SERVICES)} services.')
    conn.close()


if __name__ == '__main__':
    backfill()
