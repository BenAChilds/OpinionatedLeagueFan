import os
import time
import datetime
import random
import pickle

import vardata
import InboxReply

# Set the prompt for public replies
prompt = "You are an opinionated Rugby League fan on Reddit. \
        The " + datetime.date.today().strftime("%Y") + " season has started and you don't follow any one particular team - you love all footy. Most others are die hard fans of one particular team. \
        Do not respond directly to comments as they're rarely directed at you. \
        You speak in Australian English."

if os.path.exists(vardata.picklefile):
    with open(vardata.picklefile, 'rb') as pickle_file:
        last_post_id, last_comment_id = pickle.load(pickle_file)
else:
    # touch the picklefile if it doesn't exist
    open(vardata.picklefile, 'w+').close()
    # now load empty values to work with
    last_post_id = None
    last_comment_id = None

# monitor for new posts
while True:
    # Only run during common hours
    if vardata.dev_mode == 0 & datetime.datetime.now().hour < 6 | datetime.datetime.now().hour > 23:
        print('Outside of operating hours')
        break

    # Handle any inbox replies before making new ones
    InboxReply.checkInboxReplies()

    # randomly select what we're going to reply to
    # 0: comments
    # 1: threads
    select = random.randint(0,1)

    try:
        match select:
            case 0:
                # get the latest comment
                new_comments = vardata.subreddit.comments(limit=1)

                for comment in new_comments:
                    if comment.author.id == vardata.self.id:
                        # Skip our own comments
                        raise Exception('Comment is my own, skipping.')
                    if len(comment.body.split()) < 5:
                        # too little words to be a useful comment
                        raise Exception('Comment is not long enough, skipping.')
                    if comment.author.id in vardata.blacklist:
                        # Skip Blacklisted user comments
                        raise Exception('Comment author is blacklisted, skipping.')

                    last_comment_id = comment.id
                    print('New comment: ' + comment.body)

                    response = vardata.openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        temperature=vardata.model_temperature,
                        # max_tokens=random.randint(5,100),
                        frequency_penalty=vardata.model_frequency_penalty,
                        messages=[
                                {"role": "system", "content": prompt},
                                {"role": "user", "content": "The thread title is: \"" + comment.submission.title + "\". Respond to the following comment: \"" + comment.body + "\""},
                            ]
                        )

                    # wait a random interval of at least 2 minutes to a maximum of 7 before posting
                    print('Replying with: \n' + response['choices'][0]['message']['content'] + '\n')
                    if vardata.dev_mode == 0:
                        waitBeforePost = int(120) + random.randint(0,300)
                        print('Waiting ' + str(waitBeforePost) + 's to post...')
                        time.sleep(waitBeforePost)
                        comment.reply(response['choices'][0]['message']['content'])
                        print('Posted\n')

            case 1:
                # get the latest post
                new_posts = vardata.subreddit.new(limit=1)

                # process each new post
                for post in new_posts:
                    # ensure the post doesn't match any of the cases where we'd not want to reply
                    if last_post_id and post.id == last_post_id:
                        # skip posts that have already been processed
                        raise Exception('Post is not new, skipping.')
                    if post.author.id in vardata.blacklist:
                        # Skip Blacklisted user posts
                        raise Exception('Post author is blacklisted, skipping.')
                    if post.author.id == vardata.self.id:
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

                    response = vardata.openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        temperature=vardata.model_temperature,
                        max_tokens=random.randint(5,100),
                        frequency_penalty=vardata.model_frequency_penalty,
                        messages=[
                                {"role": "system", "content": prompt},
                                {"role": "user", "content": "The thread title is: \"" + post.title + "\". Respond to the following new post: " + post.selftext + "\""},
                            ]
                        )
                    
                    # wait a random interval of at least 2 minutes to a maximum of 7 before posting
                    print('Repling with: \n' + response['choices'][0]['message']['content'] + '\n')
                    if vardata.dev_mode == 0:
                        waitBeforePost = int(120) + random.randint(0,300)
                        print('Waiting ' + str(waitBeforePost) + 's to post...')
                        time.sleep(waitBeforePost)
                        post.reply(response['choices'][0]['message']['content'])
                        print('Posted\n')

                    # update last post id so we don't reply again
                    last_post_id = post.id
        
        # save the current state
        with open(vardata.picklefile, 'wb') as f:
            pickle.dump([last_post_id, last_comment_id], f)

        # wait 60 seconds before checking for new posts again
        print('Waiting 10 minutes before going again...\n')
        time.sleep(600)
        
    except Exception as e:
        print(f'Error: {e}\nRetrying in 60s...')
        # If there was an error, we'll wait 60 seconds before trying again
        time.sleep(60)
