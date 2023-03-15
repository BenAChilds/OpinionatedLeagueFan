from dotenv import load_dotenv

import os
import random
import time
import datetime
import pickle
import openai
import praw

load_dotenv()

# set up OpenAI API
openai.api_key = os.getenv('OPENAI_API_KEY')
prompt = "You are an opinionated Rugby League fan on Reddit.\
        The " + datetime.date.today().strftime("%Y") + " season has started and you don't follow any one particular team - you love all footy. Most others are die hard fans of one particular team, however.\
        You have poor grammar and spelling, and you like to use shorthand often.\
        You like to argue with other users and are not willing to accept that you might be wrong.\
        Some posts that you respond to may not be specifically about Rugby League.\
        Do not respond to comments as if they were directed at you personally.\
        If there is not enough context to the post, simply agree."

# set up Reddit API credentials
reddit = praw.Reddit(client_id=os.getenv('REDDIT_CLIENT_ID'),
                     client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
                     user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
                     username=os.getenv('REDDIT_USERNAME'),
                     password=os.getenv('REDDIT_PASSWORD'))
# set the subreddit to monitor
subreddit = reddit.subreddit('nrl')
self = reddit.redditor(os.getenv('REDDIT_USERNAME'))

# keep track of the last post ID processed
picklefile = 'post-tracking.pk'

with open(picklefile) as f:
    try:
        last_post_id, last_comment_id = pickle.load(f)
    except Exception:
        # touch the picklefile if it doesn't exist
        open(picklefile, 'a').close()
        # now load empty values to work with
        last_post_id = None
        last_comment_id = None

# monitor for new posts
while True:
    # Only run during common hours
    if datetime.datetime.now().hour < 6 | datetime.datetime.now().hour > 23:
        print('Outside of operating hours')
        break

    # randomly select what we're going to reply to
    # 0: comments
    # 1: threads
    select = random.randint(0,1)

    try:
        match select:
            case 0:
                # get the latest comment
                new_comments = subreddit.comments(limit=1)

                for comment in new_comments:
                    if comment.author.id == self.id:
                        # Skip our own comments
                        raise Exception('Comment is my own, skipping.')
                    if len(comment.body.split()) < 5:
                        # too little words to be a useful comment
                        raise Exception('Comment is not long enough, skipping.')

                    last_comment_id = comment.id
                    print('New comment: ' + comment.body)

                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                                {"role": "system", "content": prompt},
                                {"role": "user", "content": "Respond to the following comment: " + comment.body},
                            ]
                        )

                    # wait a random interval of at least 2 minutes to a maximum of 7 before posting
                    print('Replying with: \n' + response['choices'][0]['message']['content'] + '\n')
                    print('Waiting to post...')
                    time.sleep(int(2) + random.randint(0,300))
                    comment.reply(response['choices'][0]['message']['content'])
                    print('Posted\n')

            case 1:
                # get the latest post
                new_posts = subreddit.new(limit=1)

                # process each new post
                for post in new_posts:
                    # ensure the post doesn't match any of the cases where we'd not want to reply
                    if last_post_id and post.id == last_post_id:
                        # skip posts that have already been processed
                        raise Exception('Post is not new, skipping.')
                    if post.author.id == "AutoModerator":
                        # Skip AutoMod posts
                        raise Exception('Post is by AutoMod, skipping.')
                    if post.author.id == self.id:
                        # Skip our own posts
                        raise Exception('Post is my own, skipping.')
                    if post.title == 'Fantasy Football and SuperCoach Thread':
                        # Skip the Supercoach thread
                        raise Exception('Post is the Supercoach thread, skipping.')
                    if post.selftext == '':
                        # Skip if this isn't a selftext post, update the last post id so we don't repeat ourselves
                        last_post_id = post.id
                        raise Exception('Post is not selftext, skipping.')
                    if len(post.selftext.split()) < 5:
                        # too little words to be a useful post
                        raise Exception('Post is not long enough, skipping.')
                    
                    # process the new post
                    print(f'New post: {post.title}')
                    print(f'Body: {post.selftext}')

                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                                {"role": "system", "content": prompt},
                                {"role": "user", "content": "Respond to the following new post: " + post.selftext},
                            ]
                        )
                    
                    # wait a random interval of at least 2 minutes to a maximum of 7 before posting
                    print('Repling with: \n' + response['choices'][0]['message']['content'] + '\n')
                    print('Waiting to post...')
                    time.sleep(int(2) + random.randint(0,300))
                    post.reply(response['choices'][0]['message']['content'])
                    print('Posted\n')

                    # update last post id so we don't reply again
                    last_post_id = post.id
        
        # save the current state
        with open(picklefile, 'wb') as f:
            pickle.dump([last_post_id, last_comment_id], f)

        # wait 60 seconds before checking for new posts again
        print('Waiting 10 minutes before going again...\n')
        time.sleep(600)
        
    except Exception as e:
        print(f'Error: {e}\nRetrying in 60s...')
        # If there was an error, we'll wait 60 seconds before trying again
        time.sleep(60)
