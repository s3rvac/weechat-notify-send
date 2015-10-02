Changelog
=========

dev
---

* -

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
