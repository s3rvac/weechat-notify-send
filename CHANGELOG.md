Changelog
=========

dev
---

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
