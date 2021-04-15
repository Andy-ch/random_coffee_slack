# -*- coding: utf-8 -*-

from slack_bolt import App
from loguru import logger
from mysql.connector import connect, Error
import threading
from algo import pair
from database.dao import meets, users
from entities import user

sigSecret = ""
otoken = ""

# Initializes your app with your bot token and signing secret
app = App(
    token=otoken,
    signing_secret=sigSecret,
)


@app.action("action_start_join")
def action_start_join(body, ack, say):
    # Acknowledge the action
    ack(
        # redirect(url_for('message_onboard'))
    )
    print(body)
    say(
        text=f"Расскажи немного о себе",
        blocks=[
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Done"
                        },
                        "style": "primary",
                        "action_id": "123",
                        "value": "click_me_123"
                    }
                ]
            }

        ],
        attachments=[
            {
                "fallback": "Upgrade your Slack client to use messages like these.",
                "color": "3AA3E3",
                "attachment_type": "default",
                "callback_id": "select_remote_1234",
                "actions": [
                    {
                        "name": "Location",
                        "text": "You location",
                        "type": "select",

                        "options": [
                            {
                                "text": "Saratov",
                                "value": "saratov"
                            },
                            {
                                "text": "St. Petersburg",
                                "value": "spb"
                            },
                        ],
                    }
                ]
            }
        ]
    )


@app.message("start")
def message_start(message, say):
    print(message)
    say(
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Привет человек!👋\n" \
                            "Недавно я узнал о Random coffee challenge и понял - он нужен.\n" \
                            "Каждую неделю я буду предлагать тебе для встречи интересного человека, случайно выбранного среди других участников. " \
                            "Вы с ним увидите никнеймы друг друга и сможете сразу выбрать подходящий формат для встречи (в офисе, skype, zoom и т.д.).\n" \
                            "Интересно? Тогда присоединяйся!"
                },
                "accessory": {
                    "type": "image",
                    "image_url": "https://banner2.cleanpng.com/20180426/dww/kisspng-donuts-cafe-coffee-menu-donut-worry-pink-donut-5ae1808952de31.0211226315247279453394.jpg",
                    "alt_text": "cute donut"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Join"
                        },
                        "style": "primary",
                        "action_id": "action_start_join",
                        "value": "click_me_123"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Help"
                        },
                        "action_id": "Help",
                        "value": "click_me_123"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "emoji": True,
                            "text": "Cancel"
                        },
                        "style": "danger",
                        "action_id": "cancel",
                        "value": "click_me_123"
                    }
                ]
            }
        ],
        text=f"Hello <@{message['user']}>!"
    )


def get_db():
    try:
        connection = connect(
            host="localhost",
            user="root",
            password="fuckfuckFUCK",
            port=3306,
            database="coffee",
        )
        print("connected")
        return connection
    except Error as e:
        print(e)


def add_when_join():
    uuser = user.User(username="test", uid="uid")
    users.add(connection, uuser)

if __name__ == "__main__":
    connection = get_db()

    bot = threading.Thread(target=app.start(port=80), args=())
    bot.start()

    pairs = threading.Thread(target=pair.create, args=(app.client, 60,))
    pairs.start()

    pairs.join()
    bot.join()
