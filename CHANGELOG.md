Changelog
=========

dev
---

* Do not show notifications for some more messages that were ignored in
  previous versions of the plugin. More specifically, do not show notifications
  for messages tagged with `irc_part`, `irc_status`, `irc_nick_back`,
  `irc_401`, and `irc_402`.

0.6 (2016-09-27)
----------------

* All messages are now intercepted, not only those tagged with `irc_privmsg`.
  This should make the plugin working also for networks other than IRC (e.g.
  Matrix [#3](https://github.com/s3rvac/weechat-notify-send/issues/3)).
* Added a new option: `ignore_messages_tagged_with`: A comma-separated list of
  message tags for which no notifications should be shown. Default:
  `'irc_join,irc_quit'`.
* Added a new option: `notify_on_all_messages_in_buffers`. It is a
  comma-separated list of buffers for which you want to receive notifications
  on all messages that appear in them. You can use either short names
  (`#buffer`) or full names (`network.#buffer`). This list is empty by default.
* Do not notify on filtered (hidden) messages by default.
* Added a new option: `notify_on_filtered_messages`. By turning it `on`, you
  can instruct the plugin to send notifications also for filtered (hidden)
  messages.
* Improved the detection of nicks from the information passed by WeeChat.
  Originally, the nick was obtained only from the prefix. However, the prefix
  is not always the nick. Now, the nick is first tried to be obtained from a
  tag of the form `nick_XYZ`, where `XYZ` is the nick that sent the message. If
  this fails, the nick is obtained from the prefix (fallback).
* Improved the removal of modes from messages prefixes. Originally, only `@`
  (op on IRC) and `+` (voice on IRC) were removed. Now, any character from the
  following list is removed from the beginning of the prefix: `~&@%+- `. The
  meaning depends on the used protocol.
* Improved the detection whether a notification should be shown based on the
  authorship of the message (do not show notifications for messages from self).
* Fixed sending of notifications whose source or message starts with `--`.

0.5 (2016-05-27)
----------------

* Added a new option: `ignore_buffers`. It is a comma-separated list of buffers
  from which no notifications should be shown.
* Added a new option: `ignore_buffers_starting_with`. It is a comma-separated
  list of buffer prefixes from which no notifications should be shown.
* Show default values of options in their descriptions (e.g. when viewed via
  `iset.pl`).

0.4 (2016-04-23)
----------------

* Added a new option: `min_notification_delay`. It represents a minimal delay
  between successive notifications from the same buffer. It is used to protect
  from floods/spam. The default value is 500 milliseconds. Set it to 0 to
  disable this feature (i.e. all notifications will be shown).
* Added a new option: `notify_on_highlights`. It allows you to disable
  notifications on highlights. By default, notifications on highlights are
  enabled.
* Added a new option: `notify_on_privmsgs`. It allows you to disable
  notifications on private messages. By default, notifications on private
  messages are enabled.

0.3.4 (2015-12-22)
------------------

* Fixed occasional messing of the WeeChat screen when assertion messages are
  emitted by notify-send.

0.3.3 (2015-10-02)
------------------

* Fixed interpretation of messages containing backslashes by escaping
  them.

0.3.2 (2015-07-29)
------------------

* Fixed the obtaining of a nick from WeeChat. Previously, the nick might have
  been prefixed with a mode, e.g `@` when the user was an op. Modes are now
  removed and not shown in the notifications.

0.3.1 (2015-07-27)
------------------

* Fixed sending of notifications when `ignore_nicks_starting_with` is empty
  (the script erroneously ignored all notifications).

0.3 (2015-07-25)
----------------

* Added a new option: `ignore_nicks_starting_with`. It is a comma-separated
  list of nick prefixes from which no notifications should be shown.
* Added a new option: `ignore_nicks`. It is a comma-separated list of nicks
  from which no notifications should be shown.
* Added a new option: `nick_separator`. It allows to set a custom separator
  between a nick and a message.
* Added a new option: `notify_when_away`. It allows to disable sending of
  notifications when away.

0.2 (2015-07-05)
----------------

* Added a new option: `notify_for_current_buffer`. It allows to disable sending
  of notifications for the currently active buffer.
* Added new options: `max_length` and `ellipsis`. They allow to limit the
  maximal length of notifications.
* Added a new option: `escape_html`. It escapes the `<`, `>`, and `&` HTML
  characters in notification messages.
* Fix notifications which do not have a timeout, icon, or urgency set.

0.1 (2015-06-21)
----------------

Initial release.
