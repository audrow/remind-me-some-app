from remind_me_some_app import EmailManager

import os
import pytest


keywords: dict = {
    'EMAIL_TO': 'foo@bar.baz',
    'ROBOT_EMAIL_ADDRESS': 'bar@foo.baz',
    'ROBOT_EMAIL_PASSWORD': 'aenuthetnhua',
    'ROBOT_EMAIL_HOST': 'smtp.gmail.com',
    'ROBOT_EMAIL_PORT': '587',
}


def test_init_with_args(mocker):

    ekm_mock = mocker.patch('remind_me_some_app.EmailKeywordMatcher')
    assert not ekm_mock.called
    EmailManager(
        email_to=keywords['EMAIL_TO'],
        send_email_address=keywords['ROBOT_EMAIL_ADDRESS'],
        send_email_password=keywords['ROBOT_EMAIL_PASSWORD'],
        send_email_host=keywords['ROBOT_EMAIL_HOST'],
        send_email_port=keywords['ROBOT_EMAIL_PORT'],
    )
    assert ekm_mock.called


def test_init_with_env_vars(mocker):
    for key, value in keywords.items():
        os.environ[key] = value

    ekm_mock = mocker.patch('remind_me_some_app.EmailKeywordMatcher')
    assert not ekm_mock.called
    EmailManager()
    assert ekm_mock.called


@pytest.mark.parametrize('missing_args', [
    ['EMAIL_TO'],
    ['ROBOT_EMAIL_ADDRESS'],
    ['ROBOT_EMAIL_PASSWORD'],
    ['ROBOT_EMAIL_HOST'],
    ['ROBOT_EMAIL_PORT'],
    ['EMAIL_TO', 'ROBOT_EMAIL_ADDRESS'],
    ['EMAIL_TO', 'ROBOT_EMAIL_ADDRESS', 'ROBOT_EMAIL_PASSWORD'],
    ['EMAIL_TO', 'ROBOT_EMAIL_ADDRESS', 'ROBOT_EMAIL_PASSWORD',
     'ROBOT_EMAIL_HOST', 'ROBOT_EMAIL_PORT'],
])
def test_init_with_missing_env_vars(mocker, missing_args):
    temp_keywords = keywords.copy()
    for missing_arg in missing_args:
        temp_keywords[missing_arg] = None

    mocker.patch('remind_me_some_app.EmailKeywordMatcher')
    with pytest.raises(ValueError):
        EmailManager(
            email_to=temp_keywords['EMAIL_TO'],
            send_email_address=temp_keywords['ROBOT_EMAIL_ADDRESS'],
            send_email_password=temp_keywords['ROBOT_EMAIL_PASSWORD'],
            send_email_host=temp_keywords['ROBOT_EMAIL_HOST'],
            send_email_port=temp_keywords['ROBOT_EMAIL_PORT'],
        )


def test_make_keyword_callback():
    assert callable(EmailManager._make_keyword_callback('name'))


def test_make_send_email_callback(mocker):
    for key, value in keywords.items():
        os.environ[key] = value
    mocker.patch('remind_me_some_app.EmailKeywordMatcher')
    em = EmailManager()
    cb = em.make_send_email_callback('name')
    assert callable(cb)
    assert not em._email_keyword_matcher.send.called
    cb()
    assert em._email_keyword_matcher.send.called
