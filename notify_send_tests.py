# -*- coding: utf-8 -*-
#
# Project:     weechat-notify-send
# Homepage:    https://github.com/s3rvac/weechat-notify-send
# Description: Unit tests for the project.
# License:     MIT (see below)
#
# Copyright (c) 2015 by Petr Zemek <s3rvac@gmail.com> and contributors
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
from notify_send import add_default_value_to
from notify_send import default_value_of
from notify_send import escape_html
from notify_send import escape_slashes
from notify_send import ignore_notifications_from_buffer
from notify_send import ignore_notifications_from_messages_tagged_with
from notify_send import ignore_notifications_from_nick
from notify_send import is_below_min_notification_delay
from notify_send import message_printed_callback
from notify_send import names_for_buffer
from notify_send import nick_separator
from notify_send import nick_that_sent_message
from notify_send import notification_should_be_sent
from notify_send import notify_on_all_messages_in_buffer
from notify_send import notify_on_messages_that_match
from notify_send import prepare_notification
from notify_send import send_notification
from notify_send import shorten_message


def new_notification(source='source', message='message', icon='icon.png',
                     timeout=5000, transient=True, urgency='normal'):
    return Notification(source, message, icon, timeout, transient, urgency)


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

        # Default values for config options.
        set_config_option('notify_on_highlights', 'on')
        set_config_option('notify_on_privmsgs', 'on')
        set_config_option('notify_on_filtered_messages', 'off')
        set_config_option('notify_when_away', 'on')
        set_config_option('notify_for_current_buffer', 'on')
        set_config_option('notify_on_all_messages_in_buffers', '')
        set_config_option('min_notification_delay', '0')
        set_config_option('ignore_messages_tagged_with', '')
        set_config_option('ignore_buffers', '')
        set_config_option('ignore_buffers_starting_with', '')
        set_config_option('ignore_nicks', '')
        set_config_option('ignore_nicks_starting_with', '')
        set_config_option('nick_separator', '')
        set_config_option('escape_html', 'off')
        set_config_option('max_length', '0')
        set_config_option('ellipsis', '')
        set_config_option('icon', '')
        set_config_option('timeout', '0')
        set_config_option('transient', 'on')
        set_config_option('urgency', '')

        # Mimic the behavior of weechat.buffer_get_string() by returning the
        # empty string by default.
        weechat.buffer_get_string.side_effect = lambda buffer, string: ''


class DefaultValueOfTests(TestsBase):
    """Tests for default_value_of()."""

    def test_returns_correct_value(self):
        self.assertEqual(default_value_of('nick_separator'), ': ')


class AddDefaultValueToTests(TestsBase):
    """Tests for add_default_value_to()."""

    def test_adds_correct_default_value_when_default_value_is_nonempty(self):
        description = add_default_value_to('Option description.', 'on')

        self.assertEqual(description, 'Option description. Default: on.')

    def test_adds_correct_default_value_when_default_value_is_empty(self):
        description = add_default_value_to('Option description.', '')

        self.assertEqual(description, 'Option description. Default: "".')


class NickThatSentMessageTests(TestsBase):
    """Tests for nick_that_sent_message()."""

    def test_returns_prefix_when_there_are_no_tags_and_prefix_has_no_modes(self):
        self.assertEqual(nick_that_sent_message([], 'john'), 'john')

    def test_returns_prefix_without_mode_when_there_are_no_tags_and_prefix_has_mode(self):
        self.assertEqual(nick_that_sent_message([], '~john'), 'john')
        self.assertEqual(nick_that_sent_message([], '&john'), 'john')
        self.assertEqual(nick_that_sent_message([], '@john'), 'john')
        self.assertEqual(nick_that_sent_message([], '%john'), 'john')
        self.assertEqual(nick_that_sent_message([], '+john'), 'john')
        self.assertEqual(nick_that_sent_message([], '-john'), 'john')

    def test_removes_also_space_before_nick_when_obtained_from_prefix(self):
        self.assertEqual(nick_that_sent_message([], ' john'), 'john')

    def test_only_single_character_is_removed_as_mode_from_prefix(self):
        # Some protocols (e.g. Matrix) may start prefixes with a space.
        # However, any subsequent characters should be considered to be part of
        # the nick (e.g. from ' @john', we want '@john', including the '@').
        self.assertEqual(nick_that_sent_message([], ' @john'), '@john')

    def test_returns_nick_from_tags_when_tags_only_contains_nick(self):
        self.assertEqual(nick_that_sent_message(['nick_john'], '--'), 'john')

    def test_returns_nick_from_tags_when_tags_contain_also_other_info(self):
        tags = ['prefix_nick_lightcyan', 'nick_john', 'host_~user@domain.com']
        self.assertEqual(nick_that_sent_message(tags, '--'), 'john')

    def test_returns_empty_string_when_both_tags_and_prefix_are_empty(self):
        self.assertEqual(nick_that_sent_message([], ''), '')


class MessagePrintedCallbackTests(TestsBase):
    """Tests for message_printed_callback()."""

    def setUp(self):
        super(MessagePrintedCallbackTests, self).setUp()

        # Mock notification_should_be_sent().
        patcher = mock.patch('notify_send.notification_should_be_sent')
        self.notification_should_be_sent = patcher.start()
        self.addCleanup(patcher.stop)

        # Mock send_notification().
        patcher = mock.patch('notify_send.send_notification')
        self.send_notification = patcher.start()
        self.addCleanup(patcher.stop)

    def message_printed_callback(self, data=None, buffer='buffer', date=None,
                                 tags='', is_displayed='1', is_highlight='0',
                                 prefix='prefix', message='message'):
        return message_printed_callback(data, buffer, date, tags, is_displayed,
                                        is_highlight, prefix, message)

    def test_sends_notification_when_it_should_be_sent(self):
        self.notification_should_be_sent.return_value = True

        rc = self.message_printed_callback()

        self.assertTrue(self.notification_should_be_sent.called)
        self.assertTrue(self.send_notification.called)
        self.assertEqual(rc, weechat.WEECHAT_RC_OK)

    def test_does_not_send_notification_when_it_should_not_be_sent(self):
        self.notification_should_be_sent.return_value = False

        rc = self.message_printed_callback()

        self.assertTrue(self.notification_should_be_sent.called)
        self.assertFalse(self.send_notification.called)
        self.assertEqual(rc, weechat.WEECHAT_RC_OK)


class NotificationShouldBeSentTests(TestsBase):
    """Tests for notification_should_be_sent()."""

    def notification_should_be_sent(self, buffer='buffer', tags=(), nick='nick',
                                    is_displayed=True, is_highlight=True, message=''):
        return notification_should_be_sent(buffer, tags, nick,
                                           is_displayed, is_highlight, message)

    def test_returns_false_for_message_from_self(self):
        BUFFER = 'buffer'
        NICK = 'nick'
        set_buffer_string(BUFFER, 'localvar_nick', NICK)

        should_be_sent = self.notification_should_be_sent(
            buffer=BUFFER,
            nick=NICK
        )

        self.assertFalse(should_be_sent)

    def test_returns_false_when_message_is_filtered_and_option_is_off(self):
        set_config_option('notify_on_filtered_messages', 'off')

        should_be_sent = self.notification_should_be_sent(
            is_displayed=False  # WeeChat marks filtered messages as not displayed.
        )

        self.assertFalse(should_be_sent)

    def test_returns_true_when_message_is_not_filtered_and_option_is_on(self):
        set_config_option('notify_on_filtered_messages', 'on')

        should_be_sent = self.notification_should_be_sent(
            is_displayed=False  # WeeChat marks filtered messages as not displayed.
        )

        self.assertTrue(should_be_sent)

    def test_returns_true_when_message_matches(self):
        set_config_option('notify_on_messages_that_match', 'foo')

        should_be_sent = self.notification_should_be_sent(
            message='foobar',
            is_highlight=False,
        )

        self.assertTrue(should_be_sent)

    def test_returns_false_when_away_and_option_is_off(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'localvar_away', 'away')
        set_config_option('notify_when_away', 'off')

        should_be_sent = self.notification_should_be_sent(buffer=BUFFER)

        self.assertFalse(should_be_sent)

    def test_returns_false_when_highlight_in_current_buffer_and_option_is_off(self):
        set_config_option('notify_for_current_buffer', 'off')
        BUFFER = 'buffer'
        weechat.current_buffer.return_value = BUFFER

        should_be_sent = self.notification_should_be_sent(buffer=BUFFER)

        self.assertFalse(should_be_sent)

    def test_returns_false_when_ordinary_message_in_buffer_not_in_list(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('notify_on_all_messages_in_buffers', '')

        should_be_sent = self.notification_should_be_sent(
            buffer=BUFFER,
            is_highlight=False
        )

        self.assertFalse(should_be_sent)

    def test_returns_true_when_ordinary_message_in_buffer_in_list(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('notify_on_all_messages_in_buffers', '#buffer')

        should_be_sent = self.notification_should_be_sent(
            buffer=BUFFER,
            is_highlight=False
        )

        self.assertTrue(should_be_sent)

    def test_returns_false_when_neither_private_message_or_highlight(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'localvar_type', '')

        should_be_sent = self.notification_should_be_sent(
            buffer=BUFFER,
            is_highlight=False
        )

        self.assertFalse(should_be_sent)

    def test_returns_false_when_nick_is_missing(self):
        set_config_option('notify_on_highlights', 'on')

        should_be_sent = self.notification_should_be_sent(
            nick='',
            is_highlight=True
        )

        self.assertFalse(should_be_sent)

    def test_returns_false_when_message_is_between_ignored_tags(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'localvar_type', 'private')
        set_config_option('ignore_messages_tagged_with', 'tag1,tag2')

        should_be_sent = self.notification_should_be_sent(
            buffer=BUFFER,
            tags=['tag2', 'tag3']
        )

        self.assertFalse(should_be_sent)

    def test_returns_false_when_buffer_is_ignored(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('ignore_buffers', '#buffer')

        should_be_sent = self.notification_should_be_sent(
            buffer=BUFFER,
            is_highlight=True
        )

        self.assertFalse(should_be_sent)

    def test_returns_false_when_nick_is_ignored(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'localvar_type', 'private')
        set_config_option('ignore_nicks', 'nick')

        should_be_sent = self.notification_should_be_sent(
            nick='nick'
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

    def test_returns_true_on_private_message_when_notify_on_privmsgs_is_on(self):
        set_config_option('notify_on_privmsgs', 'on')
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'localvar_type', 'private')

        should_be_sent = self.notification_should_be_sent(
            buffer=BUFFER,
            is_highlight=False
        )

        self.assertTrue(should_be_sent)

    def test_returns_false_on_private_message_when_notify_on_privmsgs_is_off(self):
        set_config_option('notify_on_privmsgs', 'off')
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'localvar_type', 'private')

        should_be_sent = self.notification_should_be_sent(
            buffer=BUFFER,
            is_highlight=False
        )

        self.assertFalse(should_be_sent)

    def test_returns_true_on_highlight_when_notify_on_highlights_is_on(self):
        set_config_option('notify_on_highlights', 'on')

        should_be_sent = self.notification_should_be_sent(
            is_highlight=True
        )

        self.assertTrue(should_be_sent)

    def test_returns_false_on_highlight_when_notify_on_highlights_is_off(self):
        set_config_option('notify_on_highlights', 'off')

        should_be_sent = self.notification_should_be_sent(
            is_highlight=True
        )

        self.assertFalse(should_be_sent)


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


class NamesForBufferTests(TestsBase):
    """Tests for names_for_buffer()."""

    def test_returns_correct_list_when_buffer_has_both_names(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')

        self.assertEqual(
            names_for_buffer(BUFFER),
            ['network.#buffer', '#buffer']
        )

    def test_includes_short_name_with_hash_when_short_name_starts_with_gt(self):
        # This may happen with the wee_slack script, see the comment in
        # names_for_buffer().
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '>buffer')

        self.assertEqual(
            names_for_buffer(BUFFER),
            ['network.#buffer', '>buffer', '#buffer']
        )

    def test_returns_empty_list_when_buffer_has_no_name(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', '')
        set_buffer_string(BUFFER, 'short_name', '')

        self.assertEqual(names_for_buffer(BUFFER), [])


class IgnoreNotificationsFromMessagesTaggedWith(TestsBase):
    """Tests for ignore_notifications_from_messages_tagged_with()."""

    def test_returns_false_when_no_tags_are_ignored(self):
        set_config_option('ignore_messages_tagged_with', '')

        self.assertFalse(
            ignore_notifications_from_messages_tagged_with(['tag1', 'tag2'])
        )

    def test_returns_false_when_no_tag_is_between_ignored(self):
        set_config_option('ignore_messages_tagged_with', 'tagA,tagB')

        self.assertFalse(
            ignore_notifications_from_messages_tagged_with(['tag1', 'tag2'])
        )

    def test_returns_true_when_tag_is_between_ignored(self):
        set_config_option('ignore_messages_tagged_with', 'tag3,tag4,tag5')

        self.assertTrue(
            ignore_notifications_from_messages_tagged_with(['tag0', 'tag2', 'tag3'])
        )


class IgnoreNotificationsFromBufferTests(TestsBase):
    """Tests for ignore_notifications_from_buffer()."""

    def test_returns_false_when_nothing_is_ignored(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('ignore_buffers', '')
        set_config_option('ignore_buffers_starting_with', '')

        self.assertFalse(ignore_notifications_from_buffer(BUFFER))

    def test_returns_false_when_buffer_has_no_name(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', '')
        set_buffer_string(BUFFER, 'short_name', '')
        set_config_option('ignore_buffers', '')
        set_config_option('ignore_buffers_starting_with', '')

        self.assertFalse(ignore_notifications_from_buffer(BUFFER))

    def test_returns_false_when_buffer_is_not_between_ignored(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('ignore_buffers', '#buffer1,#buffer2,#buffer3')

        self.assertFalse(ignore_notifications_from_buffer(BUFFER))

    def test_returns_true_when_buffer_is_ignored_by_short_name(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('ignore_buffers', '#buffer')

        self.assertTrue(ignore_notifications_from_buffer(BUFFER))

    def test_returns_true_when_buffer_is_ignored_by_full_name(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('ignore_buffers', 'network.#buffer')

        self.assertTrue(ignore_notifications_from_buffer(BUFFER))

    def test_returns_true_when_buffer_is_between_ignored_by_short_name(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('ignore_buffers', '#aaa,#buffer,#bbb')

        self.assertTrue(ignore_notifications_from_buffer(BUFFER))

    def test_returns_true_when_buffer_is_between_ignored_by_full_name(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('ignore_buffers', '#aaa,network.#buffer,#bbb')

        self.assertTrue(ignore_notifications_from_buffer(BUFFER))

    def test_strips_beginning_and_trailing_whitespace_from_ignored_buffers(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('ignore_buffers', '  #buffer  ')

        self.assertTrue(ignore_notifications_from_buffer(BUFFER))

    def test_returns_false_when_buffer_is_not_prefixed_with_ignored_prefix(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('ignore_buffers_starting_with', 'some_prefix')

        self.assertFalse(ignore_notifications_from_buffer(BUFFER))

    def test_returns_true_when_buffer_full_name_is_prefixed_with_ignored_prefix(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('ignore_buffers_starting_with', '#aaa,network.,#bbb')

        self.assertTrue(ignore_notifications_from_buffer(BUFFER))

    def test_returns_true_when_buffer_short_name_is_prefixed_with_ignored_prefix(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('ignore_buffers_starting_with', '#aaa,#buf,#bbb')

        self.assertTrue(ignore_notifications_from_buffer(BUFFER))

    def test_strips_beginning_and_trailing_whitespace_from_ignored_prefixes(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('ignore_buffers_starting_with', '  network.  ')

        self.assertTrue(ignore_notifications_from_buffer(BUFFER))


class IgnoreNotificationsFromNickTests(TestsBase):
    """Tests for ignore_notifications_from_nick()."""

    def test_returns_false_when_nothing_is_ignored(self):
        set_config_option('ignore_nicks', '')
        set_config_option('ignore_nicks_starting_with', '')

        self.assertFalse(ignore_notifications_from_nick('nick'))

    def test_returns_false_when_nick_is_not_between_ignored(self):
        set_config_option('ignore_nicks', 'nick1,nick2,nick3')

        self.assertFalse(ignore_notifications_from_nick('wizard'))

    def test_returns_true_when_nick_is_ignored(self):
        set_config_option('ignore_nicks', 'nick')

        self.assertTrue(ignore_notifications_from_nick('nick'))

    def test_returns_true_when_nick_is_between_ignored(self):
        set_config_option('ignore_nicks', 'nick1,nick2,nick3')

        self.assertTrue(ignore_notifications_from_nick('nick2'))

    def test_strips_beginning_and_trailing_whitespace_from_ignored_nicks(self):
        set_config_option('ignore_nicks', '  nick  ')

        self.assertTrue(ignore_notifications_from_nick('nick'))

    def test_returns_false_when_nick_is_not_prefixed_with_ignored_prefix(self):
        set_config_option('ignore_nicks_starting_with', 'pre_')

        self.assertFalse(ignore_notifications_from_nick('nick'))

    def test_returns_true_when_nick_is_prefixed_with_ignored_prefix(self):
        set_config_option('ignore_nicks_starting_with', 'pre_')

        self.assertTrue(ignore_notifications_from_nick('pre_nick'))

    def test_returns_true_when_nick_is_prefixed_with_prefix_between_ignored_prefixes(self):
        set_config_option('ignore_nicks_starting_with', 'pre1_,pre2_,pre3_')

        self.assertTrue(ignore_notifications_from_nick('pre2_nick'))

    def test_strips_beginning_and_trailing_whitespace_from_ignored_prefixes(self):
        set_config_option('ignore_nicks_starting_with', '  pre_  ')

        self.assertTrue(ignore_notifications_from_nick('pre_nick'))


class NotifyOnMessagesThatMatchTests(TestsBase):
    """Tests for notify_on_messages_that_match()"""

    def test_returns_false_when_list_has_no_patterns(self):
        set_config_option('notify_on_messages_that_match', '')
        self.assertFalse(notify_on_messages_that_match("foobar"))

    def test_returns_true_when_message_matches(self):
        set_config_option('notify_on_messages_that_match', 'foo')
        self.assertTrue(notify_on_messages_that_match("foobar"))


class NotifyOnAllMessagesInBufferTests(TestsBase):
    """Tests for notify_on_all_messages_in_buffer()."""

    def test_returns_false_when_list_does_not_contain_any_buffer(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('notify_on_all_messages_in_buffers', '')

        self.assertFalse(notify_on_all_messages_in_buffer(BUFFER))

    def test_returns_false_when_buffer_has_no_name(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', '')
        set_buffer_string(BUFFER, 'short_name', '')
        set_config_option('notify_on_all_messages_in_buffers', '')

        self.assertFalse(notify_on_all_messages_in_buffer(BUFFER))

    def test_returns_false_when_buffer_is_not_in_list(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('notify_on_all_messages_in_buffers', '#buffer1,#buffer2')

        self.assertFalse(notify_on_all_messages_in_buffer(BUFFER))

    def test_returns_true_when_buffer_short_name_is_in_list(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('notify_on_all_messages_in_buffers', '#aaa,#buffer,#bbb')

        self.assertTrue(notify_on_all_messages_in_buffer(BUFFER))

    def test_returns_true_when_buffer_full_name_is_in_list(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('notify_on_all_messages_in_buffers', '#aaa,network.#buffer,#bbb')

        self.assertTrue(notify_on_all_messages_in_buffer(BUFFER))

    def test_strips_beginning_and_trailing_whitespace_from_buffers_in_list(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'name', 'network.#buffer')
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('notify_on_all_messages_in_buffers', '  #buffer  ')

        self.assertTrue(notify_on_all_messages_in_buffer(BUFFER))


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

    def prepare_notification(self, buffer='buffer', nick='nick', message='message',
                             is_private_message=True):
        if is_private_message:
            set_buffer_string(buffer, 'localvar_type', 'private')
        return prepare_notification(buffer, nick, message)

    def test_notification_has_correct_source_and_message_when_private_message(self):
        NICK = 'nick'
        MESSAGE = 'message'

        notification = self.prepare_notification(
            nick=NICK,
            message=MESSAGE,
            is_private_message=True
        )

        self.assertEqual(notification.source, NICK)
        self.assertEqual(notification.message, MESSAGE)

    def test_notification_has_correct_source_and_message_when_ordinary_message(self):
        BUFFER = 'buffer'
        set_buffer_string(BUFFER, 'short_name', '#buffer')
        set_config_option('nick_separator', ': ')

        notification = self.prepare_notification(
            buffer=BUFFER,
            nick='nick',
            message='message',
            is_private_message=False
        )

        self.assertEqual(notification.source, '#buffer')
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

    def test_notification_has_correct_transient_when_on(self):
        set_config_option('transient', 'on')

        notification = self.prepare_notification()

        self.assertTrue(notification.transient)

    def test_notification_has_correct_transient_when_off(self):
        set_config_option('transient', 'off')

        notification = self.prepare_notification()

        self.assertFalse(notification.transient)

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

    def test_does_not_split_message_inside_multibyte_character(self):
        self.assertEqual(
            shorten_message('čččč', max_length=3, ellipsis='.'),
            'čč.'
        )


class SendNotificationTests(TestsBase):
    """Tests for send_notification()."""

    def setUp(self):
        super(SendNotificationTests, self).setUp()

        # Mock subprocess.
        patcher = mock.patch('notify_send.subprocess')
        self.subprocess = patcher.start()
        self.addCleanup(patcher.stop)

        # Mock print.
        if sys.version_info.major == 3:
            patcher = mock.patch('builtins.print')
        else:
            patcher = mock.patch('notify_send.print')
        self.print_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_calls_correct_command_when_all_notification_parameters_are_set(self):
        notification = new_notification(
            source='source',
            message='message',
            icon='icon.png',
            timeout=5000,
            transient=True,
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
                '--hint', 'int:transient:1',
                '--urgency', 'normal',
                '--',
                'source',
                'message'
            ],
            stderr=self.subprocess.STDOUT,
            stdout=AnyDevNullStream()
        )

    def test_source_is_set_to_hyphen_when_source_is_empty(self):
        notification = new_notification(source='')

        send_notification(notification)

        notify_cmd = self.subprocess.check_call.call_args[0][0]
        self.assertIn('-', notify_cmd)

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

    def test_does_not_include_transient_hint_in_command_when_transient_is_off(self):
        notification = new_notification(transient=False)

        send_notification(notification)

        notify_cmd = self.subprocess.check_call.call_args[0][0]
        self.assertNotIn('int:transient:1', notify_cmd)

    def test_does_not_include_urgency_in_command_when_urgency_is_not_set(self):
        notification = new_notification(urgency='')

        send_notification(notification)

        notify_cmd = self.subprocess.check_call.call_args[0][0]
        self.assertNotIn('--urgency', notify_cmd)

    def test_prints_error_message_when_notification_sending_fails(self):
        self.subprocess.check_call.side_effect = OSError(
            'No such file or directory: notify-send'
        )

        send_notification(new_notification())

        self.assertIn(
            'OSError: No such file or directory',
            self.print_mock.call_args[0][0]
        )
