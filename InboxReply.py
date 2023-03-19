from dotenv import load_dotenv

import random
import time
import datetime
import openai

import vardata

def checkInboxReplies():
    print(f"Unread inbox items: {str(len(list(vardata.reddit.inbox.unread())))}")

    for message in vardata.reddit.inbox.unread():
        print('--------------------\n')
        replyInboxMessage(message)
        print('--------------------\n')

def replyInboxMessage(message):
    try:
        if len(message.body.split()) < 5:
            # too little words to be a useful comment
            raise Exception('Comment is not long enough, skipping.')
        if message.author.id in vardata.blacklist:
            # Skip Blacklisted user messages
            raise Exception('Message author is blacklisted, skipping.')

        print('--------------------\n')
        print(f"New message:\n\"{message.body}\"")
        print('--------------------\n')

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=vardata.model_temperature,
            frequency_penalty=vardata.model_frequency_penalty,
            messages=[
                    {"role": "system", "content": vardata.prompt},
                    {"role": "user", "content": f"You have received a reply to one of your previous comments on a thread titled \"{message.subject}\".\nThe message is: \"{message.body}\".\nReply to this message."},
                ]
            )
        
        print('--------------------\n')
        print(f"Replying with: \n{response['choices'][0]['message']['content']}\n")
        print('--------------------\n')
        if vardata.dev_mode == 0:
            # wait a random interval of at least 2 minutes to a maximum of 7 before posting
            waitBeforePost = int(120) + random.randint(0,300)
            print(f"Waiting until {(datetime.datetime.now() + datetime.timedelta(seconds=int(waitBeforePost))).time().strftime('%H:%M:%S')} to post...")
            time.sleep(waitBeforePost)
            message.reply(response['choices'][0]['message']['content'])
            print('Posted\n')

        message.mark_read()
    except Exception as e:
        print(f'Error: {e}\nRetrying...\n')