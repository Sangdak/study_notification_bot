import logging
import textwrap
import time

from environs import Env
import requests
import telegram


# logging.basicConfig(level=logging.INFO)
# logging.info('Bot starting now')
class TelegramLogsHandler(logging.Handler):
    def __init__(self, tg_bot, tg_chat_id):
        super().__init__()
        self.tg_bot = tg_bot
        self.tg_chat_id = tg_chat_id

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.tg_chat_id, text=log_entry)


def main():
    env = Env()
    env.read_env(override=True)

    dvmn_api_token = env.str('DVMN_TOKEN')
    api_long_polling_url = 'https://dvmn.org/api/long_polling/'
    tg_bot_token = env.str('TG_TOKEN')
    tg_chat_id = env.str('TG_CHAT')

    tg_bot = telegram.Bot(token=tg_bot_token)

    logger = logging.getLogger('TG_Logger')
    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(tg_bot, tg_chat_id))

    logger.info('Bot starting now')

    headers = {'Authorization': f'Token {dvmn_api_token}'}
    params = {}

    while True:
        try:
            response = requests.get(url=api_long_polling_url, headers=headers, params=params)
            response.raise_for_status()

        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError as err:
            logger.error(err, exc_info=True)
            logger.error('Some problem with connection. Wait 60 seconds before repeat.')
            # print(f'Some problem with connection. Wait 60 seconds before repeat.')
            time.sleep(60)

        work_status_data = response.json()
        new_attempts_data = work_status_data["new_attempts"][0]

        if work_status_data['status'] == 'found':
            params['timestamp'] = work_status_data['last_attempt_timestamp']
            if new_attempts_data['is_negative']:
                task_status = 'Работа требует доработки.'
            else:
                task_status = 'Работа принята.'

            message = f'''Преподаватель проверил работу: \"{new_attempts_data["lesson_title"]}\".
            {new_attempts_data["lesson_url"]}
            {task_status}
            '''

            tg_bot.send_message(
                chat_id=tg_chat_id,
                text=textwrap.dedent(message),
            )

        elif work_status_data['status'] == 'timeout':
            params['timestamp'] = work_status_data['timestamp_to_request']


if __name__ == '__main__':
    main()
