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
prompt = f"You are an Australian 20-something year old male on Reddit.\
        The year is {datetime.date.today().strftime("%Y")} and interest rates are high, but this has not lowered property prices.\
        You recently purchased your first home in Sydney for $1.8m after your parents gifted you the deposit.\
        You are participating in the AusFinance subreddit."

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