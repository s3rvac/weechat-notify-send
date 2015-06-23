# -*- coding: utf-8 -*-
#
# Project:     weechat-notify-send
# Homepage:    https://github.com/s3rvac/weechat-notify-send
# Description: Sends highlight and private-message notifications through
#              notify-send. Requires libnotify.
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
import subprocess


# Ensure that we are running under weechat.
try:
    import weechat
except ImportError:
    print('This script has to run under WeeChat.')
    print('Get WeeChat now at http://www.weechat.org/')
    sys.exit(1)


# Name of the script.
SCRIPT_NAME = 'notify_send'

# Author of the script.
SCRIPT_AUTHOR = 's3rvac'

# Version of the script.
SCRIPT_VERSION = '0.2 (dev)'

# License under which the script is distributed.
SCRIPT_LICENSE = 'MIT'

# Description of the script.
SCRIPT_DESC = ('Sends highlight and private-message notifications '
               'through notify-send.')

# Name of a function to be called when the script is unloaded.
SCRIPT_SHUTDOWN_FUNC = ''

# Used character set (utf-8 by default).
SCRIPT_CHARSET = ''

# Script settings.
SETTINGS = {
    'escape_html': ('on',
                    "Escapes the '<', '>', and '&' characters "
                    "in notification messages."),
    'icon': ('/usr/share/icons/hicolor/32x32/apps/weechat.png',
             'Path to an icon to be shown in notifications.'),
    'timeout': ('5000',
                'Time after which the notification disappears '
                '(in milliseconds; set to 0 to disable).'),
    'urgency': ('normal',
                'Urgency (low, normal, critical).')
}


class Notification(object):
    """A representation of a notification."""

    def __init__(self, source, message, icon, timeout, urgency):
        self.source = source
        self.message = message
        self.icon = icon
        self.timeout = timeout
        self.urgency = urgency


def notification_cb(data, buffer, date, tags, is_displayed, is_highlight,
                    prefix, message):
    """A callback for notifications from WeeChat."""
    is_highlight = int(is_highlight)

    if notification_should_be_sent(buffer, prefix, is_highlight):
        notification = prepare_notification(
            buffer, is_highlight, prefix, message
        )
        send_notification(notification)

    return weechat.WEECHAT_RC_OK


def notification_should_be_sent(buffer, prefix, is_highlight):
    """Should a notification be sent?"""
    if is_private_message(buffer):
        if i_am_author_of_message(buffer, prefix):
            # Do not send notifications from myself.
            return False
        return True

    if is_highlight:
        return True

    # We send notifications only for private messages or hightlights.
    return False


def is_private_message(buffer):
    """Has a private message been sent?"""
    return weechat.buffer_get_string(buffer, 'localvar_type') == 'private'


def i_am_author_of_message(buffer, prefix):
    """Am I (the current WeeChat user) the author of the message?"""
    return weechat.buffer_get_string(buffer, 'localvar_nick') == prefix


def prepare_notification(buffer, is_highlight, prefix, message):
    """Prepares a notification from the given data."""
    if is_highlight:
        source = (weechat.buffer_get_string(buffer, 'short_name') or
                  weechat.buffer_get_string(buffer, 'name'))
        message = prefix + ': ' + message
    else:
        # A private message.
        source = prefix

    if weechat.config_get_plugin('escape_html') == 'on':
        message = escape_html(message)

    icon = weechat.config_get_plugin('icon')
    timeout = weechat.config_get_plugin('timeout')
    urgency = weechat.config_get_plugin('urgency')

    return Notification(source, message, icon, timeout, urgency)


def escape_html(message):
    """Escapes HTML characters in the given message."""
    # Only the following characters need to be escaped
    # (https://wiki.ubuntu.com/NotificationDevelopmentGuidelines).
    message = message.replace('&', '&amp;')
    message = message.replace('<', '&lt;')
    message = message.replace('>', '&gt;')
    return message


def send_notification(notification):
    """Sends the given notification to the user."""
    notify_cmd = [
        'notify-send',
        '-a', 'weechat',
        '-i', notification.icon,
        '-t', notification.timeout,
        '-u', notification.urgency,
        notification.source,
        notification.message
    ]
    subprocess.check_call(notify_cmd)


if __name__ == '__main__':
    # Registration.
    weechat.register(
        SCRIPT_NAME,
        SCRIPT_AUTHOR,
        SCRIPT_VERSION,
        SCRIPT_LICENSE,
        SCRIPT_DESC,
        SCRIPT_SHUTDOWN_FUNC,
        SCRIPT_CHARSET
    )

    # Initialization.
    for option, (default_value, description) in SETTINGS.items():
        weechat.config_set_desc_plugin(option, description)
        if not weechat.config_is_set_plugin(option):
            weechat.config_set_plugin(option, default_value)
    weechat.hook_print('', 'irc_privmsg', '', 1, 'notification_cb', '')
