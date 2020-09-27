from email_keyword_matcher import EmailKeywordMatcher
from remind_me_some import Goal, ScheduleManager
import schedule

from datetime import timedelta
import logging
import os
import threading
import time
import typing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


class EmailManager:

    def __init__(
            self,
            email_to: str = os.environ['EMAIL_TO'],
            send_email_address: str = os.environ['ROBOT_EMAIL_ADDRESS'],
            send_email_password: str = os.environ['ROBOT_EMAIL_PASSWORD'],
            send_email_host: str = os.environ['ROBOT_EMAIL_HOST'],
            send_email_port: int = int(os.environ['ROBOT_EMAIL_PORT']),
    ):
        logger.info(f'Initializing {self.__class__.__name__} instance')

        if None in [email_to, send_email_address, send_email_password, send_email_host, send_email_port]:
            raise ValueError("Not all args are defined")
        self._to_email = email_to
        self._email_keyword_matcher = EmailKeywordMatcher(
            email_address=send_email_address,
            password=send_email_password,
            host=send_email_host,
            port=send_email_port,
        )
        for keyword in ['done', 'snooze', 'cancel']:
            self._email_keyword_matcher.add_keyword(keyword, self._make_keyword_callback(keyword))

    @staticmethod
    def _make_keyword_callback(name):
        def callback():
            logger.info(f"Callback for '{name}' called")
        return callback

    def make_send_email_callback(self, name):
        def callback():
            self._email_keyword_matcher.send(
                to_email=self._to_email,
                subject=f'Reminder: {name}',
                contents=name,
            )
        return callback


class RemindMeSomeApp:

    def __init__(
            self,
            sleep_duration: int = 5,
            save_file_path: typing.Optional[str] = None,
            email_manager_kwargs: dict = None,
            schedule_manager_kwargs: dict = None,
    ):
        logger.info(f'Initializing {self.__class__.__name__} instance')

        self._sleep_duration = sleep_duration
        self._save_file_path = save_file_path

        if email_manager_kwargs is None:
            email_manager_kwargs = dict()
        self._email_manager = EmailManager(**email_manager_kwargs)

        if schedule_manager_kwargs is None:
            schedule_manager_kwargs = dict()
        self.schedule_manager = ScheduleManager(**schedule_manager_kwargs)

        self._scheduler = schedule.Scheduler()
        self._scheduler.every().minute.do(self._run_schedule_manager)
        self._scheduler.every().day.do(self._update_schedule)

        self._is_running = False
        self._save()

    @property
    def is_running(self):
        return self._is_running

    def _run_schedule_manager(self):
        logger.info("Running schedule")
        self.schedule_manager.run()
        self._save()

    def _update_schedule(self):
        logger.info("Updating schedule")
        self.schedule_manager.update_schedule()
        self._save()

    def _save(self):
        if self._save_file_path is not None:
            self._save_schedule_manager()

    def _save_schedule_manager(self):
        logger.info(f'Saving state to {self._save_file_path}')
        with open(self._save_file_path, 'wb') as f:
            pass
    
    def _load_schedule_manager(self):
        if self._save_file_path is None:
            raise ValueError('No file path given')
        logger.info(f'Loading state from {self._save_file_path}')
        with open(self._save_file_path, 'rb') as f:
            pass

    def add_goal(
            self,
            name: str,
            frequency: timedelta,
            **kwargs,
    ):
        if 'callback' not in kwargs:
            kwargs['callback'] = self._email_manager.make_send_email_callback(name),
        logger.info(f"Adding goal '{name}'")
        self.schedule_manager.add_goal(
            Goal(
                name=name,
                frequency=frequency,
                **kwargs,
            )
        )
        self._update_schedule()

    def start(self):
        self._is_running = True
        threading.Thread(target=self._run_loop).start()

    def _run_loop(self):
        logger.info('Starting run loop')
        while self.is_running:
            logger.debug('Run loop running')
            self._scheduler.run_pending()
            time.sleep(self._sleep_duration)
        logger.info('Exiting run loop')

    def stop(self):
        logger.info('Stopping run loop')
        self._is_running = False

    def __del__(self):
        self._is_running = False


if __name__ == '__main__':

    app = RemindMeSomeApp()
    goals = (
        ("Call Mom", timedelta(weeks=1)),
        ("Call Dad", timedelta(weeks=1)),
        ("Call Grandma", timedelta(weeks=2)),
        ("Call Grandpa", timedelta(weeks=2)),
        ("Call Cousin", timedelta(weeks=4)),
        ("Call Uncle", timedelta(weeks=4)),
    )
    for goal in goals:
        app.add_goal(goal[0], goal[1])

    app.start()
    while app.is_running:
        time.sleep(10)
