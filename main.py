import logging
import time

from environs import Env
import requests
import telegram


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
        work_status_data = {}
        try:
            response = requests.get(url=api_long_polling_url, headers=headers, params=params)
            response.raise_for_status()
            work_status_data = response.json()
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError as connect_err:
            logger.error(connect_err, exc_info=True)
            logger.error('Some problem with connection. Wait 60 seconds before repeat.')
            time.sleep(60)
        except Exception as other_error:
            logging.exception(other_error)

        if work_status_data.get('status') == 'timeout':
            params['timestamp'] = work_status_data['timestamp_to_request']
            continue

        if work_status_data.get('status') == 'found':
            params['timestamp'] = work_status_data['last_attempt_timestamp']
            new_attempts_data = work_status_data.get('new_attempts')[0]
            task_status = 'Работа требует доработки.' if new_attempts_data['is_negative'] else 'Работа принята.'

            message = f'Преподаватель проверил работу: \"{new_attempts_data["lesson_title"]}\". \
                       {new_attempts_data["lesson_url"]} \
                       {task_status}'

            tg_bot.send_message(
                chat_id=tg_chat_id,
                text=message,
            )


if __name__ == '__main__':
    main()
