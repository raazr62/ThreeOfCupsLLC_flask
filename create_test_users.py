#!/usr/bin/env python3
"""
Script to create test users with completed assessments
"""

from app import app, db
from models import User, Assessment
import json

def create_test_users():
    with app.app_context():
        # Test user data
        test_users = [
            {
                'username': 'alice_smith',
                'first_name': 'Alice',
                'last_name': 'Smith',
                'email': 'alice@test.com',
                'password': 'Test123!',
                'bio': 'Love hiking and reading books. Looking for meaningful friendships.',
                'assessment': {
                    'tell_us_more_what_brings_you': 'I recently moved to a new city and want to make genuine connections',
                    'tell_us_more_friendship_meaning': 'Friendship means having someone who truly understands and supports you',
                    'friendship_readiness_emotional_availability': '8',
                    'friendship_readiness_time_energy_capacity': 'I have time for regular hangouts and maintaining friendships',
                    'friendship_readiness_friendship_intention': 'Building close, lasting friendships',
                    'friendship_readiness_personal_work': 'Yes, I\'ve done therapy and self-reflection',
                    'friendship_readiness_showing_up': 'Being present, listening actively, and checking in regularly',
                    'personality_social_style_recharge_style': '3',
                    'personality_social_style_social_settings': 'I observe first, then engage when comfortable',
                    'personality_social_style_ideal_hangout_0': '1',
                    'personality_social_style_ideal_hangout_1': '2',
                    'personality_social_style_ideal_hangout_2': '4',
                    'personality_social_style_ideal_hangout_3': '3',
                    'personality_social_style_making_plans': 'I like to plan ahead',
                    'personality_social_style_communication_preference': ['Text/messaging', 'Phone/video calls'],
                    'personality_social_style_texting_style': 'I respond thoughtfully when I have time',
                    'conflict_repair_conflict_response': 'I address it directly but calmly',
                    'conflict_repair_repair_looks_like': ['A sincere apology', 'Taking accountability'],
                    'conflict_repair_flaky_friend_scenario': 'I\'d bring it up gently and ask what\'s going on',
                    'conflict_repair_feedback_comfort': '4',
                    'conflict_repair_hurt_feelings_needs_0': '2',
                    'conflict_repair_hurt_feelings_needs_1': '3',
                    'conflict_repair_hurt_feelings_needs_2': '1',
                    'conflict_repair_hurt_feelings_needs_3': '4',
                    'conflict_repair_hurt_feelings_needs_4': '5',
                    'conflict_repair_boundary_setting': 'I can set boundaries but it takes effort',
                    'conflict_repair_friendship_lessons': 'Communication is everything - don\'t let things fester',
                    'hobbies_interests_activities_interests': ['Reading', 'Hiking/outdoors', 'Cooking/baking'],
                    'hobbies_interests_want_to_try': 'Rock climbing and pottery classes',
                    'hobbies_interests_free_time': 'I love exploring nature trails and trying new recipes',
                    'hobbies_interests_doing_vs_being': 'A balance of both',
                    'values_top_values_0': '1',
                    'values_top_values_1': '2',
                    'values_top_values_2': '3',
                    'values_top_values_3': '4',
                    'values_top_values_4': '5',
                    'values_top_values_5': '6',
                    'values_top_values_6': '7',
                    'values_top_values_7': '8',
                    'values_top_values_8': '9',
                    'values_top_values_9': '10',
                    'friendship_values_statements_resonate': ['I value depth over quantity', 'I need consistency and reliability', 'I appreciate vulnerability and realness'],
                    'friendship_values_friendship_needs': ['Emotional support', 'Quality time', 'Deep conversations'],
                    'friendship_values_non_negotiables': 'Honesty, loyalty, and mutual respect',
                    'friendship_values_dealbreakers': 'Gossip, flakiness, and dishonesty',
                    'friendship_values_connection_language_0': '1',
                    'friendship_values_connection_language_1': '4',
                    'friendship_values_connection_language_2': '3',
                    'friendship_values_connection_language_3': '2',
                    'friendship_values_connection_language_4': '5',
                    'friendship_values_connection_language_5': '6',
                    'logistics_connection_frequency': 'Weekly or a few times a month',
                    'logistics_connection_type': 'In-person primarily, with texting in between',
                    'wrapping_up_ideal_friend_words_word1': 'Authentic',
                    'wrapping_up_ideal_friend_words_word2': 'Supportive',
                    'wrapping_up_ideal_friend_words_word3': 'Adventurous',
                    'wrapping_up_what_can_offer': 'A listening ear, loyalty, and genuine care',
                    'wrapping_up_what_want_receive': 'The same - someone who truly cares and shows up',
                    'wrapping_up_gender_preference': ['Women', 'Non-binary'],
                    'wrapping_up_age_preference': ['25-34', '35-44']
                }
            },
            {
                'username': 'bob_jones',
                'first_name': 'Bob',
                'last_name': 'Jones',
                'email': 'bob@test.com',
                'password': 'Test123!',
                'bio': 'Tech enthusiast and coffee lover. Always up for deep conversations.',
                'assessment': {
                    'tell_us_more_what_brings_you': 'Want to expand my social circle and find people with similar interests',
                    'tell_us_more_friendship_meaning': 'Having people you can be yourself with and share life\'s journey',
                    'friendship_readiness_emotional_availability': '7',
                    'friendship_readiness_time_energy_capacity': 'I can make time but my schedule varies',
                    'friendship_readiness_friendship_intention': 'Making a few close friends',
                    'friendship_readiness_personal_work': 'Some - I\'m working on being more vulnerable',
                    'friendship_readiness_showing_up': 'Being reliable, following through on commitments',
                    'personality_social_style_recharge_style': '2',
                    'personality_social_style_social_settings': 'I\'m usually the one starting conversations',
                    'personality_social_style_ideal_hangout_0': '2',
                    'personality_social_style_ideal_hangout_1': '1',
                    'personality_social_style_ideal_hangout_2': '3',
                    'personality_social_style_ideal_hangout_3': '4',
                    'personality_social_style_making_plans': 'I\'m flexible and spontaneous',
                    'personality_social_style_communication_preference': ['Text/messaging', 'In-person hangouts'],
                    'personality_social_style_texting_style': 'I respond pretty quickly',
                    'conflict_repair_conflict_response': 'I need time to process before discussing',
                    'conflict_repair_repair_looks_like': ['Having a conversation about it', 'Understanding each other\'s perspective'],
                    'conflict_repair_flaky_friend_scenario': 'I\'d probably let it slide a few times before saying something',
                    'conflict_repair_feedback_comfort': '3',
                    'conflict_repair_hurt_feelings_needs_0': '3',
                    'conflict_repair_hurt_feelings_needs_1': '1',
                    'conflict_repair_hurt_feelings_needs_2': '2',
                    'conflict_repair_hurt_feelings_needs_3': '4',
                    'conflict_repair_hurt_feelings_needs_4': '5',
                    'conflict_repair_boundary_setting': 'I can set boundaries but it takes effort',
                    'conflict_repair_friendship_lessons': 'It\'s important to speak up when something bothers you',
                    'hobbies_interests_activities_interests': ['Gaming', 'Coffee shops', 'Tech/gadgets'],
                    'hobbies_interests_want_to_try': 'Board game cafes and escape rooms',
                    'hobbies_interests_free_time': 'Playing video games, checking out new coffee spots',
                    'hobbies_interests_doing_vs_being': 'More of a doing friend',
                    'values_top_values_0': '2',
                    'values_top_values_1': '1',
                    'values_top_values_2': '4',
                    'values_top_values_3': '3',
                    'values_top_values_4': '6',
                    'values_top_values_5': '5',
                    'values_top_values_6': '8',
                    'values_top_values_7': '7',
                    'values_top_values_8': '10',
                    'values_top_values_9': '9',
                    'friendship_values_statements_resonate': ['I appreciate humor and lightheartedness', 'I value shared activities and experiences', 'I need friends who respect my independence'],
                    'friendship_values_friendship_needs': ['Shared hobbies', 'Fun and laughter', 'Respect for boundaries'],
                    'friendship_values_non_negotiables': 'Respect and reliability',
                    'friendship_values_dealbreakers': 'Being judgmental or overly negative',
                    'friendship_values_connection_language_0': '2',
                    'friendship_values_connection_language_1': '1',
                    'friendship_values_connection_language_2': '3',
                    'friendship_values_connection_language_3': '4',
                    'friendship_values_connection_language_4': '5',
                    'friendship_values_connection_language_5': '6',
                    'logistics_connection_frequency': 'A few times a month',
                    'logistics_connection_type': 'Mix of in-person and virtual',
                    'wrapping_up_ideal_friend_words_word1': 'Chill',
                    'wrapping_up_ideal_friend_words_word2': 'Interesting',
                    'wrapping_up_ideal_friend_words_word3': 'Reliable',
                    'wrapping_up_what_can_offer': 'Good conversation, shared activities, and loyalty',
                    'wrapping_up_what_want_receive': 'Someone who\'s genuine and fun to hang out with',
                    'wrapping_up_gender_preference': ['Any gender'],
                    'wrapping_up_age_preference': ['25-34', '35-44']
                }
            },
            {
                'username': 'carol_white',
                'first_name': 'Carol',
                'last_name': 'White',
                'email': 'carol@test.com',
                'password': 'Test123!',
                'bio': 'Yoga instructor and mindfulness practitioner. Seeking conscious connections.',
                'assessment': {
                    'tell_us_more_what_brings_you': 'I\'m looking for spiritually-minded friends who value growth',
                    'tell_us_more_friendship_meaning': 'A sacred space where we can be vulnerable and support each other\'s evolution',
                    'friendship_readiness_emotional_availability': '9',
                    'friendship_readiness_time_energy_capacity': 'I prioritize my friendships and make time for them',
                    'friendship_readiness_friendship_intention': 'Building soul-nourishing friendships',
                    'friendship_readiness_personal_work': 'Yes, continuously - therapy, meditation, and self-inquiry',
                    'friendship_readiness_showing_up': 'Holding space, being present without judgment, deep listening',
                    'personality_social_style_recharge_style': '4',
                    'personality_social_style_social_settings': 'I observe first, then engage when comfortable',
                    'personality_social_style_ideal_hangout_0': '1',
                    'personality_social_style_ideal_hangout_1': '2',
                    'personality_social_style_ideal_hangout_2': '4',
                    'personality_social_style_ideal_hangout_3': '3',
                    'personality_social_style_making_plans': 'I like to plan ahead',
                    'personality_social_style_communication_preference': ['Phone/video calls', 'In-person hangouts'],
                    'personality_social_style_texting_style': 'I respond thoughtfully when I have time',
                    'conflict_repair_conflict_response': 'I address it directly but calmly',
                    'conflict_repair_repair_looks_like': ['Having a conversation about it', 'Understanding each other\'s perspective'],
                    'conflict_repair_flaky_friend_scenario': 'I\'d bring it up gently and ask what\'s going on',
                    'conflict_repair_feedback_comfort': '5',
                    'conflict_repair_hurt_feelings_needs_0': '3',
                    'conflict_repair_hurt_feelings_needs_1': '2',
                    'conflict_repair_hurt_feelings_needs_2': '1',
                    'conflict_repair_hurt_feelings_needs_3': '4',
                    'conflict_repair_hurt_feelings_needs_4': '5',
                    'conflict_repair_boundary_setting': 'I\'m comfortable setting clear boundaries',
                    'conflict_repair_friendship_lessons': 'Boundaries are an act of love, and honest communication builds trust',
                    'hobbies_interests_activities_interests': ['Yoga/meditation', 'Reading', 'Nature/outdoors'],
                    'hobbies_interests_want_to_try': 'Sound healing and ecstatic dance',
                    'hobbies_interests_free_time': 'Practicing yoga, reading spiritual texts, walking in nature',
                    'hobbies_interests_doing_vs_being': 'More of a being friend',
                    'values_top_values_0': '1',
                    'values_top_values_1': '3',
                    'values_top_values_2': '2',
                    'values_top_values_3': '5',
                    'values_top_values_4': '4',
                    'values_top_values_5': '7',
                    'values_top_values_6': '6',
                    'values_top_values_7': '9',
                    'values_top_values_8': '8',
                    'values_top_values_9': '10',
                    'friendship_values_statements_resonate': ['I value depth over quantity', 'I appreciate vulnerability and realness', 'I\'m drawn to emotional intimacy'],
                    'friendship_values_friendship_needs': ['Deep conversations', 'Emotional support', 'Mutual growth'],
                    'friendship_values_non_negotiables': 'Authenticity, emotional intelligence, and commitment to growth',
                    'friendship_values_dealbreakers': 'Superficiality, closed-mindedness, lack of self-awareness',
                    'friendship_values_connection_language_0': '4',
                    'friendship_values_connection_language_1': '1',
                    'friendship_values_connection_language_2': '3',
                    'friendship_values_connection_language_3': '2',
                    'friendship_values_connection_language_4': '5',
                    'friendship_values_connection_language_5': '6',
                    'logistics_connection_frequency': 'Weekly or a few times a month',
                    'logistics_connection_type': 'In-person primarily, with texting in between',
                    'wrapping_up_ideal_friend_words_word1': 'Conscious',
                    'wrapping_up_ideal_friend_words_word2': 'Compassionate',
                    'wrapping_up_ideal_friend_words_word3': 'Authentic',
                    'wrapping_up_what_can_offer': 'Deep presence, emotional support, and spiritual companionship',
                    'wrapping_up_what_want_receive': 'Someone who values depth and is committed to their own growth',
                    'wrapping_up_gender_preference': ['Women', 'Non-binary'],
                    'wrapping_up_age_preference': ['35-44', '45-54']
                }
            },
            {
                'username': 'david_kim',
                'first_name': 'David',
                'last_name': 'Kim',
                'email': 'david@test.com',
                'password': 'Test123!',
                'bio': 'Artist and musician. Always looking for creative collaborators and deep thinkers.',
                'assessment': {
                    'tell_us_more_what_brings_you': 'Looking for friends who appreciate art and creativity',
                    'tell_us_more_friendship_meaning': 'Finding people who inspire you and make you feel alive',
                    'friendship_readiness_emotional_availability': '8',
                    'friendship_readiness_time_energy_capacity': 'My schedule is flexible as a freelancer',
                    'friendship_readiness_friendship_intention': 'Building creative community and close bonds',
                    'friendship_readiness_personal_work': 'Yes - art is my therapy',
                    'friendship_readiness_showing_up': 'Creating together, sharing inspiration, being authentic',
                    'personality_social_style_recharge_style': '3',
                    'personality_social_style_social_settings': 'I\'m warm and engaging with everyone',
                    'personality_social_style_ideal_hangout_0': '4',
                    'personality_social_style_ideal_hangout_1': '1',
                    'personality_social_style_ideal_hangout_2': '2',
                    'personality_social_style_ideal_hangout_3': '3',
                    'personality_social_style_making_plans': 'I\'m flexible and spontaneous',
                    'personality_social_style_communication_preference': ['Text/messaging', 'In-person hangouts'],
                    'personality_social_style_texting_style': 'I text in bursts then disappear for a while',
                    'conflict_repair_conflict_response': 'I address it directly but calmly',
                    'conflict_repair_repair_looks_like': ['Having a conversation about it', 'A sincere apology'],
                    'conflict_repair_flaky_friend_scenario': 'I\'d bring it up gently and ask what\'s going on',
                    'conflict_repair_feedback_comfort': '4',
                    'conflict_repair_hurt_feelings_needs_0': '2',
                    'conflict_repair_hurt_feelings_needs_1': '3',
                    'conflict_repair_hurt_feelings_needs_2': '4',
                    'conflict_repair_hurt_feelings_needs_3': '1',
                    'conflict_repair_hurt_feelings_needs_4': '5',
                    'conflict_repair_boundary_setting': 'I can set boundaries but it takes effort',
                    'conflict_repair_friendship_lessons': 'People show love differently - learn their language',
                    'hobbies_interests_activities_interests': ['Art/crafts', 'Music/concerts', 'Museums/galleries'],
                    'hobbies_interests_want_to_try': 'Collaborative art projects and jam sessions',
                    'hobbies_interests_free_time': 'Creating art, playing music, visiting galleries',
                    'hobbies_interests_doing_vs_being': 'A balance of both',
                    'values_top_values_0': '3',
                    'values_top_values_1': '1',
                    'values_top_values_2': '2',
                    'values_top_values_3': '6',
                    'values_top_values_4': '4',
                    'values_top_values_5': '5',
                    'values_top_values_6': '8',
                    'values_top_values_7': '7',
                    'values_top_values_8': '9',
                    'values_top_values_9': '10',
                    'friendship_values_statements_resonate': ['I appreciate humor and lightheartedness', 'I value shared activities and experiences', 'I appreciate vulnerability and realness'],
                    'friendship_values_friendship_needs': ['Shared hobbies', 'Intellectual stimulation', 'Fun and laughter'],
                    'friendship_values_non_negotiables': 'Creativity, open-mindedness, authenticity',
                    'friendship_values_dealbreakers': 'Close-mindedness and lack of curiosity',
                    'friendship_values_connection_language_0': '1',
                    'friendship_values_connection_language_1': '3',
                    'friendship_values_connection_language_2': '4',
                    'friendship_values_connection_language_3': '2',
                    'friendship_values_connection_language_4': '6',
                    'friendship_values_connection_language_5': '5',
                    'logistics_connection_frequency': 'Weekly or a few times a month',
                    'logistics_connection_type': 'Mix of in-person and virtual',
                    'wrapping_up_ideal_friend_words_word1': 'Creative',
                    'wrapping_up_ideal_friend_words_word2': 'Open-minded',
                    'wrapping_up_ideal_friend_words_word3': 'Inspiring',
                    'wrapping_up_what_can_offer': 'Creative energy, inspiration, and authentic connection',
                    'wrapping_up_what_want_receive': 'Someone who appreciates art and has interesting perspectives',
                    'wrapping_up_gender_preference': ['Any gender'],
                    'wrapping_up_age_preference': ['25-34', '35-44']
                }
            }
        ]

        created_users = []
        for user_data in test_users:
            # Check if user already exists
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if existing_user:
                print(f"User '{user_data['username']}' already exists, skipping...")
                continue

            # Create user
            user = User(
                username=user_data['username'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=user_data['email'],
                is_admin=False,
                bio=user_data['bio']
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            db.session.flush()  # Get the user ID

            # Create assessment
            assessment_json = json.dumps(user_data['assessment'], indent=2)
            assessment = Assessment(
                user_id=user.id,
                answers=assessment_json,
                reviewed=False
            )
            db.session.add(assessment)

            created_users.append(user_data)
            print(f"Created user: {user_data['username']} ({user_data['email']})")

        db.session.commit()

        print("\n" + "="*50)
        print("Test users created successfully!")
        print("="*50)
        print("\nAll test users have password: Test123!")
        print("\nCreated users:")
        for user_data in created_users:
            print(f"  - {user_data['username']} ({user_data['first_name']} {user_data['last_name']})")

if __name__ == '__main__':
    create_test_users()
