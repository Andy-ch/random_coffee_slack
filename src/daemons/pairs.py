# -*- coding: utf-8 -*-

import time


def create(client, period=60):
    # TODO: kvendingoldo after implementation of DAO layer
    while True:
        # make pairs
        # notify user
        print("pairs daemons")

        client.chat_postMessage(channel="D01TRBDB8EA",
                                text="Привет!\n"
                                     "Твоя пара в random coffee на эту неделю: @nickname \n"
                                     "Не откладывай, договорись о встрече сразу 🙂 \n"
                                     "Будут вопросы, пиши в чат `help`.\n"
                                     "👨‍💻 Рекомендуем на этой неделе провести встречу по видеосвязи.\n"
                                     "Берегите себя и близких! И поддерживайте общение с окружающими онлайн")
        time.sleep(period)
