from remind_me_some_app import RemindMeSomeApp

from freezegun import freeze_time
from datetime import datetime, timedelta
import pytest


def test_add_goal_updates_schedule(mocker):
    mocker.patch('remind_me_some_app.EmailKeywordMatcher')
    app = RemindMeSomeApp()
    app._schedule_manager = mocker.Mock()
    assert not app._schedule_manager.update_schedule.called
    app.add_goal(name='goal1', frequency=timedelta(days=2))
    assert app._schedule_manager.update_schedule.called


def test_add_goals_creates_actions(mocker):
    mocker.patch('remind_me_some_app.EmailKeywordMatcher')

    app = RemindMeSomeApp()
    assert not app._schedule_manager.goals
    assert not app._schedule_manager.actions
    for i in range(1, 5):
        app.add_goal(name=f'goal {i}', frequency=timedelta(days=2))
        assert len(app._schedule_manager.goals) == i
        assert len(app._schedule_manager.actions) == i


@pytest.mark.parametrize('num_goals', [0, 1, 5])
def test_start_and_stop(mocker, num_goals):
    mocker.patch('remind_me_some_app.EmailKeywordMatcher')
    mocker.patch('remind_me_some_app.Scheduler')

    app = RemindMeSomeApp()
    for i in range(1, num_goals):
        app.add_goal(name=f'goal {i}', frequency=timedelta(days=2))

    assert not app.is_running
    assert not app._scheduler.run_pending.called

    times_to_run = 5
    for i in range(1, times_to_run):
        app.start()
        assert app.is_running
        assert app._scheduler.run_pending.call_count == i

        app.stop()
        assert not app.is_running


@pytest.mark.parametrize('num_goals', [0, 1, 5])
@pytest.mark.timeout(1)
def test_del_stops_thread(mocker, num_goals):
    mocker.patch('remind_me_some_app.EmailKeywordMatcher')
    mocker.patch('remind_me_some_app.Scheduler')

    app = RemindMeSomeApp(sleep_duration=0.001)
    for i in range(1, num_goals):
        app.add_goal(name=f'goal {i}', frequency=timedelta(days=2))
    app.start()
    del app


@pytest.mark.parametrize('num_goals', [1, 5])
def test_behavior(mocker, num_goals):
    mocker.patch('remind_me_some_app.EmailKeywordMatcher')
    with freeze_time(datetime(2020, 1, 6, 0, 0)):  # Monday
        app = RemindMeSomeApp()
        for i in range(num_goals):
            app.add_goal(name=f'goal {i}', frequency=timedelta(days=2))
        assert len(app._schedule_manager.goals) == num_goals
        assert len(app._schedule_manager.actions) == num_goals
        action = app._schedule_manager.actions[0]
        assert action.is_ready()
        assert not action.is_called()
        assert not action.is_completed()
        app._run_once()
    with freeze_time(datetime(2020, 1, 6, 0, 2)):
        assert action.is_ready()
        assert not action.is_called()
        assert not action.is_completed()
        app._run_once()  # run the action
        assert not action.is_ready()
        assert action.is_called()
        assert action.is_completed()
        if len(app._schedule_manager.actions) > 1:
            next_action = app._schedule_manager.actions[1]
            assert not next_action.is_ready()
            assert not next_action.is_called()
            assert not next_action.is_completed()

        # Nothing happens until the next run job is scheduled
        for _ in range(5):
            app._run_once()
            assert not action.is_ready()
            assert action.is_called()
            assert action.is_completed()
    with freeze_time(datetime(2020, 1, 6, 0, 4)):
        assert len(app._schedule_manager.actions) == num_goals
        app._run_once()  # clear the job
        if app._schedule_manager.actions:
            action = app._schedule_manager.actions[0]
            assert not action.is_ready()
            assert not action.is_called()
            assert not action.is_completed()
        assert len(app._schedule_manager.actions) == num_goals-1

    # Don't create a new action until update is called
    for hour in range(1, 24):
        with freeze_time(datetime(2020, 1, 6, hour, 0)):
            app._run_once()  # create a new action
            assert len(app._schedule_manager.actions) == num_goals-1

    with freeze_time(datetime(2020, 1, 7, 0, 0)):  # Tuesday
        if app._schedule_manager.actions:
            action = app._schedule_manager.actions[0]
            assert action.is_ready()
            assert not action.is_called()
            assert not action.is_completed()
        app._run_once()  # create a new action
        assert not action.is_ready()
        assert action.is_called()
        assert action.is_completed()

        assert len(app._schedule_manager.actions) == num_goals

    with freeze_time(datetime(2020, 1, 7, 0, 2)):  # Tuesday
        if num_goals > 1:
            app._run_once()  # create a new action
            assert len(app._schedule_manager.actions) == num_goals-1
        else:
            assert len(app._schedule_manager.actions) == num_goals
