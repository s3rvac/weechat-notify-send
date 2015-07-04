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

import sys
import unittest

try:
    from unittest import mock  # Python 3
except ImportError:
    import mock  # Python 2

# We need to mock the 'weechat' import because the tests do not run under
# weechat. Moreover, it allows us to test the module properly.
weechat = mock.Mock()
sys.modules['weechat'] = weechat

from notify_send import Notification
from notify_send import escape_html
from notify_send import send_notification
from notify_send import shorten_message


def new_notification(source='source', message='message', icon='icon.png',
                     timeout=5000, urgency='normal'):
    return Notification(source, message, icon, timeout, urgency)


class EscapeHtmlTests(unittest.TestCase):
    """Tests for escape_html()."""

    def test_properly_escapes_needed_html_characters(self):
        self.assertEqual(
            escape_html('< > &'),
            '&lt; &gt; &amp;'
        )


class ShortenMessageTests(unittest.TestCase):
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


class SendNotificationTests(unittest.TestCase):
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

        self.subprocess.check_call.assert_called_once_with([
            'notify-send',
            '-a', 'weechat',
            '-i', 'icon.png',
            '-t', 5000,
            '-u', 'normal',
            'source',
            'message'
        ])
