import os
import time
import datetime
import random
import pickle

import vardata
import InboxReply



if os.path.exists(vardata.picklefile):
    with open(vardata.picklefile, 'rb') as pickle_file:
        last_post_id, last_comment_id = pickle.load(pickle_file)
else:
    # touch the picklefile if it doesn't exist
    open(vardata.picklefile, 'w+').close()
    # now load empty values to work with
    last_post_id = None
    last_comment_id = None

print(f'Operating in r/ {str(vardata.subreddit)}')

# monitor for new posts
while True:
    try:
        # Only run during common hours
        # Useful for localised subreddits where posting at odd hours might raise suspicion
        # Time is per system clock. Comment out if not required
        if vardata.dev_mode == 0 & datetime.datetime.now().hour < 6 | datetime.datetime.now().hour > 18:
            raise Exception('Outside of operating hours')

        # Handle any inbox replies before making new ones
        InboxReply.checkInboxReplies()

        # randomly select what we're going to reply to
        # 0: comments
        # 1: threads
        select = random.randint(0,1)

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
                    print('--------------------\n')
                    print(f'New comment:\n{comment.body}\n')
                    print('--------------------\n')

                    response = vardata.openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        temperature=vardata.model_temperature,
                        frequency_penalty=vardata.model_frequency_penalty,
                        messages=[
                                {"role": "system", "content": vardata.prompt},
                                {"role": "user", "content": f"Read this Reddit thread: {comment.submission.permalink}. Now, respond to the following comment: {comment.body}"},
                            ]
                        )
                    
                    print('--------------------\n')

                    print(f'Replying with: \n{response['choices'][0]['message']['content']}\n')
                    print('--------------------\n')
                    if vardata.dev_mode == 0:
                        # wait a random interval of at least 2 minutes to a maximum of 7 before posting
                        waitBeforePost = int(120) + random.randint(0,300)
                        print(f'Waiting until {(datetime.datetime.now() + datetime.timedelta(seconds=int(waitBeforePost))).time().strftime("%H:%M:%S")} to post...')
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
                    if post.selftext == '':
                        # Skip if this isn't a selftext post, update the last post id so we don't repeat ourselves
                        last_post_id = post.id
                        raise Exception('Post is not selftext, skipping.')
                    if len(post.selftext.split()) < 5:
                        # too little words to be a useful post
                        raise Exception('Post is not long enough, skipping.')
                    
                    print('--------------------\n')
                    # process the new post
                    print(f'New post:\n{post.title}\n')
                    print(f'Body:\n{post.selftext}')
                    print('--------------------\n')

                    response = vardata.openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        temperature=vardata.model_temperature,
                        frequency_penalty=vardata.model_frequency_penalty,
                        messages=[
                                {"role": "system", "content": vardata.prompt},
                                {"role": "user", "content": f"The thread title is: \"{post.title}\".\nRespond to the following new post:\n\"{post.selftext}\""},
                            ]
                        )
                    
                    print('--------------------\n')
                    
                    print(f'Repling with: \n{response['choices'][0]['message']['content']}\n')
                    print('--------------------\n')
                    if vardata.dev_mode == 0:
                        # wait a random interval of at least 2 minutes to a maximum of 7 before posting
                        waitBeforePost = int(120) + random.randint(0,300)
                        print(f'Waiting until {(datetime.datetime.now() + datetime.timedelta(seconds=int(waitBeforePost))).time().strftime("%H:%M:%S")} to post...')
                        time.sleep(waitBeforePost)
                        post.reply(response['choices'][0]['message']['content'])
                        print('Posted\n')

                    # update last post id so we don't reply again
                    last_post_id = post.id
        
        # save the current state
        with open(vardata.picklefile, 'wb') as f:
            pickle.dump([last_post_id, last_comment_id], f)

        # wait 10mins before checking for new posts again
        wait = 600
        print(f'Waiting until {(datetime.datetime.now() + datetime.timedelta(seconds=int(wait))).time().strftime("%H:%M:%S")} to run again...\n')
        time.sleep(wait)
        
    except Exception as e:
        wait = 60
        print(f'Error: {e}\nRetrying at {(datetime.datetime.now() + datetime.timedelta(seconds=int(wait))).time().strftime("%H:%M:%S")}...')
        # If there was an error, we'll wait 60 seconds before trying again
        time.sleep(wait)
