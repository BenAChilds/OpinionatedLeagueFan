from dotenv import load_dotenv

import random
import time
import datetime
import openai

import vardata

prompt = "You are an opinionated Rugby League fan on Reddit. \
        The " + datetime.date.today().strftime("%Y") + " season has started and you don't follow any one particular team - you love all footy. Most others are die hard fans of one particular team. \
        You speak in Australian English. \
        Your name is " + str(vardata.self.id)

def checkInboxReplies():
    print('Unread inbox items: ' + str(len(list(vardata.reddit.inbox.unread()))))

    for message in vardata.reddit.inbox.unread():
        replyInboxMessage(message)

def replyInboxMessage(message):
    try:
        if len(message.body.split()) < 5:
            # too little words to be a useful comment
            raise Exception('Comment is not long enough, skipping.')
        if message.author.id in vardata.blacklist:
            # Skip Blacklisted user messages
            raise Exception('Message author is blacklisted, skipping.')

        print('New message: ' + message.body)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=vardata.model_temperature,
            frequency_penalty=vardata.model_frequency_penalty,
            messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "You have received a reply to one of your previous comments on a thread titled \"" + message.subject + "\". The message is: \"" + message.body + "\". Reply to this message."},
                ]
            )

        # wait a random interval of at least 2 minutes to a maximum of 7 before posting
        print('Replying with: \n' + response['choices'][0]['message']['content'] + '\n')
        if vardata.dev_mode == 0:
            print('Waiting to post...')
            time.sleep(int(2) + random.randint(0,300))
            message.reply(response['choices'][0]['message']['content'])
            print('Posted\n')

        message.mark_read()
    except Exception as e:
        print(f'Error: {e}\n')