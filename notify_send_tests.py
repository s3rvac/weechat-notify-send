# -*- coding: utf-8 -*-
#
# Project:     weechat-notify-send
# Homepage:    https://github.com/s3rvac/weechat-notify-send
# Description: Unit tests for the project.
# License:     MIT (see below)
#
# Copyright (c) 2015-2016 by Petr Zemek <s3rvac@gmail.com> and contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import os
import sys
import unittest

try:
    from unittest import mock  # Python 3
except ImportError:
    import mock  # Python 2

# We need to mock the 'weechat' import because the tests do not run under
# WeeChat, so the import would fail.
weechat = mock.Mock()
sys.modules['weechat'] = weechat

from notify_send import Notification
from notify_send import default_value_of
from notify_send import escape_html
from notify_send import escape_slashes
from notify_send import ignore_notifications_from
from notify_send import is_below_min_notification_delay
from notify_send import nick_from_prefix
from notify_send import nick_separator
from notify_send import notification_cb
from notify_send import notification_should_be_sent
from notify_send import prepare_notification
from notify_send import send_notification
from notify_send import shorten_message


def new_notification(source='source', message='message', icon='icon.png',
                     timeout=5000, urgency='normal'):
    return Notification(source, message, icon, timeout, urgency)


def set_config_option(option, value):
    """Sets the given configuration option to the given value."""
    orig_config_get_plugin = weechat.config_get_plugin.side_effect

    def config_get_plugin(opt):
        if opt == option:
            return value

        if orig_config_get_plugin is not None:
            return orig_config_get_plugin(opt)

        # Assume that options are off by default.
        return 'off'

    weechat.config_get_plugin.side_effect = config_get_plugin


def set_buffer_string(buffer, string, value):
    """Sets the given buffer string to the given value."""
    orig_buffer_get_string = weechat.buffer_get_string.side_effect

    def buffer_get_string(b, s):
        if b == buffer and s == string:
            return value

        if orig_buffer_get_string is not None:
            return orig_buffer_get_string(b, s)

        return ''

    weechat.buffer_get_string.side_effect = buffer_get_string


class TestsBase(unittest.TestCase):
    """A base class for all tests."""

    def setUp(self):
        # Mock weechat again before running any tests. We need to do this
        # because tests may change the global mock (return value, side effects,
        # etc.) and thus affect other tests.
        patcher = mock.patch('notify_send.weechat')
        global weechat
        weechat = patcher.start()
        self.addCleanup(patcher.stop)

        # Mock time.time().
        patcher = mock.patch('notify_send.time.time')
        self.time = patcher.start()
        self.addCleanup(patcher.stop)
        self.time.return_value = 0.0


class DefaultValueOfTests(TestsBase):
    """Tests for default_value_of()."""

    def test_returns_correct_value(self):
        self.assertEqual(default_value_of('nick_separator'), ': ')


class NickFromPrefixTests(TestsBase):
    """Tests for nick_from_prefix()."""

    def test_returns_correct_value_when_prefix_is_just_nick(self):
        self.assertEqual(nick_from_prefix('nick'), 'nick')

    def test_returns_correct_value_when_prefix_is_nick_with_op(self):
        self.assertEqual(nick_from_prefix('@nick'), 'nick')

    def test_returns_correct_value_when_prefix_is_nick_with_voice(self):
        self.assertEqual(nick_from_prefix('+nick'), 'nick')


class NotificationCBTests(TestsBase):
    """Tests for notification_cb()."""

    def setUp(self):
        super().setUp()

        # Mock notification_should_be_sent().
        patcher = mock.patch('notify_send.notification_should_be_sent')
        self.notification_should_be_sent = patcher.start()
        self.addCleanup(patcher.stop)

        # Mock send_notification().
        patcher = mock.patch('notify_send.send_notification')
        self.send_notification = patcher.start()
        self.addCleanup(patcher.stop)

    def notification_cb(self, data=None, buffer='buffer', date=None, tags=None,
                        is_displayed=None, is_highlight='0', prefix='prefix',
                        message='message'):
        return notification_cb(data, buffer, date, tags, is_displayed,
                               is_highlight, prefix, message)

    def test_sends_notification_when_it_should_be_sent(self):
        self.notification_should_be_sent.return_value = True

        rc = self.notification_cb()

        self.assertTrue(self.notification_should_be_sent.called)
        self.assertTrue(self.send_notification.called)
        self.assertEqual(rc, weechat.WEECHAT_RC_OK)

    def test_does_not_send_notification_when_it_should_not_be_sent(self):
        self.notification_should_be_sent.return_value = False

        rc = self.notification_cb()

        self.assertTrue(self.notification_should_be_sent.called)
        self.assertFalse(self.send_notification.called)
        self.assertEqual(rc, weechat.WEECHAT_RC_OK)


class NotificationShouldBeSentTests(TestsBase):
    """Tests for notification_should_be_sent()."""

    def setUp(self):
        super().setUp()
        set_config_option('min_notification_delay', 0)
        set_config_option('notify_when_away', 'on')
        set_config_option('notify_for_current_buffer', 'on')

    def notification_should_be_sent(self, buffer='buffer', prefix='prefix',
                                    is_highlight=True):
        return notification_should_be_sent(buffer, prefix, is_highlight)

    def test_returns_false_when_away_and_option_is_off(self):
        set_config_option('notify_when_away', 'off')

        should_be_sent = self.notification_should_be_sent()

        self.assertFalse(should_be_sent)

    def test_returns_false_when_highlight_in_current_buffer_and_option_is_off(self):
        set_config_option('notify_for_current_buffer', 'off')
        BUFFER = 'buffer'
        weechat.current_buffer.return_value = BUFFER

        should_be_sent = self.notification_should_be_sent(buffer=BUFFER)

        self.assertFalse(should_be_sent)

    def test_returns_false_for_notification_from_self(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'localvar_type', 'private')
        PREFIX = 'prefix'
        set_buffer_string(BUFFER, 'localvar_nick', PREFIX)

        should_be_sent = self.notification_should_be_sent(
            buffer=BUFFER,
            prefix=PREFIX
        )

        self.assertFalse(should_be_sent)

    def test_returns_false_when_neither_private_message_or_highlight(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'localvar_type', '')

        should_be_sent = self.notification_should_be_sent(
            buffer=BUFFER,
            is_highlight=False
        )

        self.assertFalse(should_be_sent)

    def test_returns_false_when_nick_is_ignored(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'localvar_type', 'private')
        set_config_option('ignore_nicks', 'nick')

        should_be_sent = self.notification_should_be_sent(
            prefix='nick'
        )

        self.assertFalse(should_be_sent)

    def test_returns_false_when_is_below_min_notification_delay(self):
        BUFFER = 'buffer'
        set_buffer_string(
            BUFFER,
            'localvar_notify_send_last_notification_time',
            '0.7'
        )
        set_config_option('min_notification_delay', 500)
        self.time.return_value = 1.0

        should_be_sent = self.notification_should_be_sent()

        self.assertFalse(should_be_sent)

    def test_sends_notification_on_private_message(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'localvar_type', 'private')

        should_be_sent = self.notification_should_be_sent(
            buffer=BUFFER,
            is_highlight=False
        )

        self.assertTrue(should_be_sent)

    def test_sends_notification_on_highlight(self):
        should_be_sent = self.notification_should_be_sent(
            is_highlight=True
        )

        self.assertTrue(should_be_sent)


class IsBelowMinNotificationDelayTests(TestsBase):
    """Tests for is_below_min_notification_delay()."""

    def test_returns_false_when_min_notification_delay_is_zero(self):
        BUFFER = 'buffer'
        set_buffer_string(
            BUFFER,
            'localvar_notify_send_last_notification_time',
            '1.0'
        )
        self.time.return_value = 1.0
        set_config_option('min_notification_delay', 0)

        self.assertFalse(is_below_min_notification_delay(BUFFER))

    def test_returns_false_when_last_time_is_not_below_min_notification_delay(self):
        BUFFER = 'buffer'
        set_buffer_string(
            BUFFER,
            'localvar_notify_send_last_notification_time',
            '0.4'
        )
        self.time.return_value = 1.0
        set_config_option('min_notification_delay', 500)

        self.assertFalse(is_below_min_notification_delay(BUFFER))

    def test_returns_true_when_last_time_is_below_min_notification_delay(self):
        BUFFER = 'buffer'
        set_buffer_string(
            BUFFER,
            'localvar_notify_send_last_notification_time',
            '1.4'
        )
        self.time.return_value = 1.0
        set_config_option('min_notification_delay', 500)

        self.assertTrue(is_below_min_notification_delay(BUFFER))

    def test_updates_last_notification_time(self):
        CURRENT_TIME = 1.0
        self.time.return_value = CURRENT_TIME
        BUFFER = 'buffer'

        is_below_min_notification_delay(BUFFER)

        weechat.buffer_set.assert_called_once_with(
            BUFFER,
            'localvar_set_notify_send_last_notification_time',
            str(CURRENT_TIME)
        )


class IgnoreNotificationsFromTests(TestsBase):
    """Tests for ignore_notifications_from()."""

    def test_returns_false_when_nothing_is_ignored(self):
        set_config_option('ignore_nicks', '')
        set_config_option('ignore_nicks_starting_with', '')

        self.assertFalse(ignore_notifications_from('nick'))

    def test_returns_false_when_nick_is_not_between_ignored(self):
        set_config_option('ignore_nicks', 'nick1,nick2,nick3')

        self.assertFalse(ignore_notifications_from('wizard'))

    def test_returns_true_when_nick_is_ignored(self):
        set_config_option('ignore_nicks', 'nick')

        self.assertTrue(ignore_notifications_from('nick'))

    def test_returns_true_when_nick_is_between_ignored(self):
        set_config_option('ignore_nicks', 'nick1,nick2,nick3')

        self.assertTrue(ignore_notifications_from('nick2'))

    def test_strips_beginning_and_trailing_whitespace_from_ignored_nicks(self):
        set_config_option('ignore_nicks', '  nick  ')

        self.assertTrue(ignore_notifications_from('nick'))

    def test_returns_false_when_nick_is_not_prefixed_with_ignored_prefix(self):
        set_config_option('ignore_nicks_starting_with', 'pre_')

        self.assertFalse(ignore_notifications_from('nick'))

    def test_returns_true_when_nick_is_prefixed_with_ignored_prefix(self):
        set_config_option('ignore_nicks_starting_with', 'pre_')

        self.assertTrue(ignore_notifications_from('pre_nick'))

    def test_returns_true_when_nick_is_prefixed_with_prefix_between_ignored_prefixes(self):
        set_config_option('ignore_nicks_starting_with', 'pre1_,pre2_,pre3_')

        self.assertTrue(ignore_notifications_from('pre2_nick'))

    def test_strips_beginning_and_trailing_whitespace_from_ignored_prefixes(self):
        set_config_option('ignore_nicks_starting_with', '  pre_  ')

        self.assertTrue(ignore_notifications_from('pre_nick'))


class EscapeHtmlTests(TestsBase):
    """Tests for escape_html()."""

    def test_properly_escapes_needed_html_characters(self):
        self.assertEqual(
            escape_html('< > &'),
            '&lt; &gt; &amp;'
        )


class EscapeSlashesTests(TestsBase):
    """Tests for escape_slashes()."""

    def test_properly_escapes_slashes(self):
        self.assertEqual(
            escape_slashes(r'a\tb\nc'),
            r'a\\tb\\nc'
        )


class PrepareNotificationTests(TestsBase):
    """Tests for prepare_notification()."""

    def setUp(self):
        super().setUp()
        set_config_option('ellipsis', '')
        set_config_option('escape_html', 'off')
        set_config_option('icon', '')
        set_config_option('max_length', 0)
        set_config_option('timeout', 0)
        set_config_option('urgency', '')

    def prepare_notification(self, buffer='buffer', is_highlight=False,
                             nick='nick', message='message'):
        return prepare_notification(buffer, is_highlight, nick, message)

    def test_notification_has_correct_source_and_message_when_not_highlight(self):
        NICK = 'nick'
        MESSAGE = 'message'

        notification = self.prepare_notification(
            is_highlight=False,
            nick=NICK,
            message=MESSAGE
        )

        self.assertEqual(notification.source, NICK)
        self.assertEqual(notification.message, MESSAGE)

    def test_notification_has_correct_source_and_message_when_is_highlight(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', BUFFER)
        set_config_option('nick_separator', ': ')
        notification = self.prepare_notification(
            buffer=BUFFER,
            is_highlight=True,
            nick='nick',
            message='message'
        )

        self.assertEqual(notification.source, BUFFER)
        self.assertEqual(notification.message, 'nick: message')

    def test_notification_has_correct_icon(self):
        ICON = '/path/to/icon.png'
        set_config_option('icon', ICON)

        notification = self.prepare_notification()

        self.assertEqual(notification.icon, ICON)

    def test_notification_has_correct_timeout(self):
        TIMEOUT = 1000
        set_config_option('timeout', TIMEOUT)

        notification = self.prepare_notification()

        self.assertEqual(notification.timeout, TIMEOUT)

    def test_notification_has_correct_urgency(self):
        URGENCY = 'critical'
        set_config_option('urgency', URGENCY)

        notification = self.prepare_notification()

        self.assertEqual(notification.urgency, URGENCY)

    def test_shortens_message_when_max_length_is_non_zero_and_message_is_long(self):
        set_config_option('max_length', 10)
        set_config_option('ellipsis', '[..]')

        notification = self.prepare_notification(message='123456789abcd')

        self.assertEqual(notification.message, '123456[..]')

    def test_does_not_shorten_message_when_max_length_zero(self):
        set_config_option('max_length', 0)
        MESSAGE = '123456789'

        notification = self.prepare_notification(message=MESSAGE)

        self.assertEqual(notification.message, MESSAGE)

    def test_does_not_shorten_message_when_message_is_short_enough(self):
        set_config_option('max_length', 10)
        MESSAGE = 10 * 'a'

        notification = self.prepare_notification(message=MESSAGE)

        self.assertEqual(notification.message, MESSAGE)

    def test_escapes_html_when_escape_html_is_on(self):
        set_config_option('escape_html', 'on')

        notification = self.prepare_notification(message='<>')

        self.assertEqual(notification.message, '&lt;&gt;')

    def test_does_not_escape_html_when_escape_html_is_off(self):
        set_config_option('escape_html', 'off')

        notification = self.prepare_notification(message='<>')

        self.assertEqual(notification.message, '<>')


class NickSeparatorTests(TestsBase):
    """Tests for nick_separator()."""

    def test_returns_value_from_config_when_set(self):
        NICK_SEPARATOR = ' --> '
        set_config_option('nick_separator', NICK_SEPARATOR)

        self.assertEqual(nick_separator(), NICK_SEPARATOR)

    def test_returns_default_value_when_config_value_is_not_set(self):
        set_config_option('nick_separator', '')

        self.assertEqual(
            nick_separator(),
            default_value_of('nick_separator')
        )


class ShortenMessageTests(TestsBase):
    """Tests for shorten_message()."""

    def test_returns_complete_message_when_max_length_is_zero(self):
        message = 'abcde'
        self.assertEqual(
            shorten_message(message, max_length=0, ellipsis='[..]'),
            message
        )

    def test_returns_complete_message_if_its_length_is_max_length(self):
        message = 'abcde'
        self.assertEqual(
            shorten_message(message, max_length=len(message), ellipsis='[..]'),
            message
        )

    def test_returns_just_ellipsis_when_max_length_is_length_of_ellipsis(self):
        message = 'abcde'
        ellipsis = '[..]'
        self.assertEqual(
            shorten_message(message, len(ellipsis), ellipsis),
            ellipsis
        )

    def test_returns_shorter_message_when_it_is_longer_than_max_length(self):
        self.assertEqual(
            shorten_message('abcdef', max_length=5, ellipsis='[..]'),
            'a[..]'
        )

    def test_returns_part_of_ellipsis_when_ellipsis_is_too_long(self):
        self.assertEqual(
            shorten_message('abcdef', max_length=3, ellipsis='[..]'),
            '[..'
        )


class SendNotificationTests(TestsBase):
    """Tests for send_notification()."""

    def setUp(self):
        # Mock subprocess.
        patcher = mock.patch('notify_send.subprocess')
        self.subprocess = patcher.start()
        self.addCleanup(patcher.stop)

    def test_calls_correct_command_when_all_notification_parameters_are_set(self):
        notification = new_notification(
            source='source',
            message='message',
            icon='icon.png',
            timeout=5000,
            urgency='normal'
        )

        send_notification(notification)

        class AnyDevNullStream:
            def __eq__(self, other):
                return other.name == os.devnull

        self.subprocess.check_call.assert_called_once_with(
            [
                'notify-send',
                '--app-name', 'weechat',
                '--icon', 'icon.png',
                '--expire-time', '5000',
                '--urgency', 'normal',
                'source',
                'message'
            ],
            stderr=self.subprocess.STDOUT,
            stdout=AnyDevNullStream()
        )

    def test_does_not_include_icon_in_command_when_icon_is_not_set(self):
        notification = new_notification(icon='')

        send_notification(notification)

        notify_cmd = self.subprocess.check_call.call_args[0][0]
        self.assertNotIn('--icon', notify_cmd)

    def test_does_not_include_expire_time_in_command_when_timeout_is_not_set(self):
        notification = new_notification(timeout='')

        send_notification(notification)

        notify_cmd = self.subprocess.check_call.call_args[0][0]
        self.assertNotIn('--expire-time', notify_cmd)

    def test_does_not_include_urgency_in_command_when_urgency_is_not_set(self):
        notification = new_notification(urgency='')

        send_notification(notification)

        notify_cmd = self.subprocess.check_call.call_args[0][0]
        self.assertNotIn('--urgency', notify_cmd)
