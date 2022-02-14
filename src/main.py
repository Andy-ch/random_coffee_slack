# -*- coding: utf-8 -*-

import os

from multiprocessing import Process
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from loguru import logger
from db.exceptions import UserNotFoundError, RatingNotFoundError, NotificationNotFoundError
from db import utils as db_utils

from utils import config, season
from daemons import week
from constants import messages, elements, common
from utils import msg

from models.user import User
from models.notification import Notification
from models.rating import Rating

config = config.load("../resources/config.yml")
app = App(
    token=config["slack"]["botToken"]
)


@app.command("/rcb")
def rcb_command(body, ack, say):
    msg = body["text"]
    if msg:
        if msg == "start":
            flow_participate_0(body, ack, say)
        elif msg == "help":
            ack()
            say(text=messages.FLOW_HELP)
        elif msg == "quit":
            flow_quit(body, ack, say)
        elif msg == "status":
            flow_status(body, ack, say)
        elif msg == "stop":
            try:
                _ = user_repo.get_by_id(body["user_id"])
            except UserNotFoundError:
                ack()
                say(text=messages.USER_NOT_FOUND)
            else:
                flow_stop(ack, body)
        elif msg == "change_meet_location":
            flow_change_meet_location(body, ack, say)
        else:
            ack()
            say(text=messages.COMMAND_NOT_FOUND)
    else:
        ack()
        say(text=messages.COMMAND_NOT_FOUND)


@app.action("help")
def action_help(ack, body, client):
    logger.info("flow::help")

    ack()
    client.chat_update(
        channel=body['channel']['id'],
        ts=msg.get_ts(body),
        text="You have a new notification in the chat",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": messages.FLOW_HELP
                }
            }
        ]
    )


def flow_stop(ack, body):
    ack()
    app.client.chat_postMessage(
        channel=body["user_id"],
        text="You have a new notification in the chat",
        blocks=[{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": messages.FLOW_STOP
            },
        }] + elements.FLOW_STOP
    )


@app.event("message")
def handle_message_events(body, say):
    pass
    # logger.debug(f"Handled message event, body: {body}")
    # TODO
    # if body["event"]["type"] == "message":
    #     say(text=messages.COMMAND_NOT_FOUND)


@app.action("change_meet_location")
def action_change_meet_location(ack, body, client):
    logger.info("flow::help")
    ack()

    new_meet_loc = body["actions"][0]["selected_option"]["value"]
    usr = user_repo.get_by_id(body["user"]["id"])
    # TODO: Add verification
    usr.meet_loc = new_meet_loc
    user_repo.update(usr)

    client.chat_update(
        channel=body['channel']['id'],
        ts=msg.get_ts(body),
        text="You have a new notification in the chat",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Your meet location has been changed to {new_meet_loc}"
                }
            }
        ]
    )


def flow_change_meet_location(body, ack, say):
    uid = body['user_id']
    logger.info(f"flow::change meet location for user {uid}")
    ack()
    blocks = [{
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": messages.FLOW_CHANGE_MEET_LOCATION
        },
        "accessory": {
            "type": "static_select",
            "placeholder": {
                "type": "plain_text",
                "text": "Select an item",
                "emoji": True
            },
            "options": elements.LOCATIONS,
            "action_id": "change_meet_location"
        }
    }]

    say(text="You have a new notification in the chat", blocks=blocks)


def flow_status(body, ack, say):
    uid = body['user_id']
    logger.info(f"flow::status for user {uid}")

    usr = user_repo.get_by_id(uid)

    pause_in_weeks = str(usr.pause_in_weeks)

    if pause_in_weeks == "0":
        week_msg = "on this week"
    else:
        week_msg = f"in {pause_in_weeks} weeks"

    ack()
    say(text=messages.FLOW_STATUS.format(pause_in_weeks, week_msg, usr.meet_loc))


def flow_quit(body, ack, say):
    uid = body['user_id']

    logger.info(f"flow::quit for user {uid}")

    ack()
    say(text=messages.FLOW_QUIT)

    notify_uid2_about_uid_quit(uid)
    user_repo.delete_by_id(uid)


def flow_participate_0(body, ack, say):
    logger.info(f"flow::participate::0 for user {body['user_id']}")

    ack()
    say(
        text="You have a new notification in the chat",
        blocks=[{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": messages.FLOW_PARTICIPATE_0
            },
            "accessory": elements.DONUT
        }] + elements.FLOW_PART_0
    )


@app.action("location")
def location(ack, body, client):
    logger.info(f"flow::location for user {body['user']['id']}")

    ack()

    usr = user_repo.get_by_id(body["user"]["id"])

    if usr.loc == "none":
        usr.loc = body["actions"][0]["selected_option"]["value"]
        user_repo.update(usr)

    flow_participate_2(ack, body, client)


@app.action("flow_participate_1")
def flow_participate_1(ack, body, client):
    uid = body["user"]["id"]

    logger.info(f"flow::participate::1 for user {uid}")
    ack()

    try:
        msg_user = user_repo.get_by_id(uid)
        msg_user.pause_in_weeks = "0"

        user_repo.update(msg_user)

        flow_participate_2(ack, body, client)
    except UserNotFoundError as ex:
        new_user = User(id=uid, username=body["user"]["username"], pause_in_weeks="0")

        user_repo.add(new_user)
        rating_repo.init(new_user.id)

        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": messages.FLOW_PARTICIPATE_1
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an item",
                        "emoji": True
                    },
                    "options": elements.LOCATIONS,
                    "action_id": "location"
                }
            }
        ]

        client.chat_update(
            channel=body['channel']['id'],
            ts=msg.get_ts(body),
            text="You have a new notification in the chat",
            blocks=blocks
        )


@app.action("flow_participate_2")
def flow_participate_2(ack, body, client):
    logger.info(f"flow::participate::2 for user {body['user']['id']}")

    ack()

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": messages.FLOW_PARTICIPATE_2
            },
            "accessory": elements.DONUT
        }
    ]

    client.chat_update(
        channel=body['channel']['id'],
        ts=msg.get_ts(body),
        text="You have a new notification in the chat",
        blocks=blocks
    )


@app.action("flow_next_week_yes")
def flow_next_week_yes(ack, body, client):
    ack()

    usr = user_repo.get_by_id(body["user"]["id"])
    usr.pause_in_weeks = "0"
    user_repo.update(usr)

    client.chat_update(
        channel=body['channel']['id'],
        ts=msg.get_ts(body),
        text="RCB: next week survey",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": messages.FLOW_WEEK_YES

                }
            }
        ]
    )


def notify_uid2_about_uid_quit(uid1: str) -> None:
    season_id = season.get()
    meets = meet_repo.list({"season": season_id, "or": {"uid1": uid1, "uid2": uid1}})

    if meets:
        meet = meets[0]
        if meet.uid1 == uid1:
            uid2 = meet.uid2
        else:
            uid2 = meet.uid1

        # NOTE: Send message to uid2 that uid1 take a break
        app.client.chat_postMessage(
            channel=uid2,
            text="You have a new notification in the chat",
            blocks=[{
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": messages.FLOW_PARTNER_LEFT
                },
            }]
        )

        # Delete meet and all notifications about it
        meet_repo.delete(meet)
    else:
        logger.info(f"User {uid1} didn't have a scheduled meet with anyone else")


def stop_wrapper(ack, body, client, period, message):
    ack()

    usr = user_repo.get_by_id(body["user"]["id"])
    usr.pause_in_weeks = period
    user_repo.update(usr)

    notify_uid2_about_uid_quit(usr.id)

    # NOTE: Message for uid1 about successful pause
    client.chat_update(
        channel=body['channel']['id'],
        ts=msg.get_ts(body),
        text="You have a new notification in the chat",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
    )


@app.action("flow_next_week_pause_1w")
def flow_next_week_pause_1w(ack, body, client):
    # NOTE: 2 but not 1 here because bot will do decrement on the nearest Sunday and in the next Sunday
    stop_wrapper(ack, body, client, "2", messages.FLOW_WEEK_PAUSE_1W)


@app.action("flow_next_week_pause_1m")
def flow_next_week_pause_1m(ack, body, client):
    # NOTE: 5 but not 4 here because bot will do decrement on the nearest Sunday and in the next Sunday
    stop_wrapper(ack, body, client, "5", messages.FLOW_WEEK_PAUSE_1M)


@app.action("stop")
def action_stop(ack, body, client):
    stop_wrapper(ack, body, client, "inf", messages.ACTION_STOP)


def flow_meet_rate(ack, body, client, rating_diff):
    ack()

    uid1 = body["user"]["id"]
    uid2 = msg.get_uid(body['message']['blocks'][0]['text']['text'])
    season_id = season.get()

    meets = meet_repo.list(spec={"season": season_id, "uid1": uid1, "uid2": uid2}) + \
            meet_repo.list(spec={"season": season_id, "uid2": uid1, "uid1": uid2})

    if meets:
        meet = meets[0]
        meet.completed = True
        meet_repo.update(meet)
    else:
        logger.error("Meet hasn't been found for %s", uid1)

    try:
        rating = rating_repo.get_by_ids(uid1, uid2)
        rating.value += rating_diff
        rating_repo.update(rating)
    except RatingNotFoundError:
        rating_value = 1.0 + rating_diff
        rating = Rating(uid1=uid1, uid2=uid2, value=rating_value)
        rating_repo.add(rating)

    client.chat_update(
        channel=body['channel']['id'],
        ts=msg.get_ts(body),
        text="You have a new notification in the chat",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": messages.FLOW_MEET_RATE
                }
            }
        ]
    )


@app.action("flow_meet_p3")
def flow_meet_p3(ack, body, client):
    flow_meet_rate(ack, body, client, 0.15)


@app.action("flow_meet_p2")
def flow_meet_p2(ack, body, client):
    flow_meet_rate(ack, body, client, 0.10)


@app.action("flow_meet_p1")
def flow_meet_p1(ack, body, client):
    flow_meet_rate(ack, body, client, 0.00)


@app.action("flow_meet_n1")
def flow_meet_n1(ack, body, client):
    flow_meet_rate(ack, body, client, -0.05)


@app.action("flow_meet_n2")
def flow_meet_n2(ack, body, client):
    flow_meet_rate(ack, body, client, -0.1)


@app.action("flow_meet_was")
def flow_meet_was(ack, body, client):
    uid1 = body["user"]["id"]
    uid2 = msg.get_uid(body['message']['blocks'][0]['text']['text'])
    ack()

    blocks = [{
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (messages.FLOW_MEET_WAS).format(uid2)
        },

    }] + elements.MEET_WAS

    client.chat_update(
        channel=body['channel']['id'],
        ts=msg.get_ts(body),
        text="You have a new notification in the chat",
        blocks=blocks
    )

    try:
        ntf = ntf_repo.get({"uid": uid1, "type": common.NTF_TYPES.feedback, "season": season.get()})
        ntf.status = True
        ntf_repo.update(ntf)
    except NotificationNotFoundError as ex:
        ntf_repo.add(Notification(uid=uid1, season=season.get(), type=common.NTF_TYPES.feedback, status=True))


@app.action("flow_meet_was_not_yet")
def flow_meet_was_not_yet(ack, body, client):
    ack()

    client.chat_update(
        channel=body['channel']['id'],
        ts=msg.get_ts(body),
        text="You have a new notification in the chat",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": messages.FLOW_MEET_WAS_NOT_YET
                }
            }
        ]
    )


@app.action("flow_meet_was_not")
def flow_meet_was_not(ack, body, client):
    ack()

    client.chat_update(
        channel=body['channel']['id'],
        ts=msg.get_ts(body),
        text="You have a new notification in the chat",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": messages.FLOW_MEET_RATE
                }
            }
        ]
    )

    flow_meet_p1(ack, body, client)


if __name__ == "__main__":
    log_dir = os.getenv("RCB_LOG_DIR")
    logger.add(
        f"{log_dir}/rcb_{{time}}.log",
        level="INFO",
        rotation=config["log"]["rotation"],
        compression="zip"
    )

    logger.info("Bot launching ...")

    user_repo, ntf_repo, rating_repo, meet_repo = db_utils.get_repos(config)

    week = Process(
        target=week.care,
        args=(app.client, config,),
        daemon=True
    )
    week.start()

    bot = Process(
        target=SocketModeHandler(app, config["slack"]["appToken"]).start(),
        args=()
    )
    bot.start()
    bot.join()
