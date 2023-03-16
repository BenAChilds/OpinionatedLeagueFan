from dotenv import load_dotenv

import os
import openai
import praw
import datetime

load_dotenv()

# dev mode will skip posting and only output to console
dev_mode = 1

# set up OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')

# Set the prompt for public replies
# Use this to set the bot's personality.
# Refer to the docs for techniques to use: https://platform.openai.com/docs/introduction/overview
prompt = "You are an opinionated AFL fan on Reddit. \
        The " + datetime.date.today().strftime("%Y") + " season is well underway and you don't follow any one particular team - you love all footy. Most others are die hard fans of one particular team. \
        DO NOT MENTION YOU ARE A BOT OR AN AI LANGUAGE MODEL. YOU ARE AN AFL FAN AND YOU LOVE YOUR FOOTY. YOU'RE NEW TO AFL AND HAVE NO KNOWLEDGE OF IT BEFORE 2018 \
        DO NOT REFER TO ANY SPECIFIC GAMES AFTER JANUARY 1 2021 \
        Do not respond directly to comments as they're rarely directed at you. \
        You speak in Australian English."

# Set values for the recommended adjustments. Again, refer to the docs
model_temperature=1.3
model_frequency_penalty=0.8

# set up Reddit API credentials
reddit = praw.Reddit(client_id=os.getenv('REDDIT_CLIENT_ID'),
                    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
                    username=os.getenv('REDDIT_USERNAME'),
                    password=os.getenv('REDDIT_PASSWORD'))

# set the subreddit to monitor
subreddit = reddit.subreddit(os.getenv('SUBREDDIT'))
# Make the bot self aware of its identity
self = reddit.redditor(os.getenv('REDDIT_USERNAME'))

# set banned users
blacklist = [
    'AutoModerator',
    'reddit',
    # user to ignore per line
]

# keep track of the last post ID processed
picklefile = 'post-tracking.pk'