weechat-notify-send
===================

A [WeeChat](https://weechat.org/) plugin that sends highlight and
private-message notifications through
[notify-send](http://manpages.ubuntu.com/manpages/vivid/man1/notify-send.1.html).
It requires [libnotify](https://developer.gnome.org/libnotify/), which provides
the `notify-send` application.

A sample screenshot:

![Screenshot](resources/screenshot.png "title")

Note that the precise appearance depends on the configuration of your
notification system as well as on the used icon.

Installation
------------

* Put the `notify_send.py` script to `~/.weechat/python/`
* Add a symbolic link to it in the `~/.weechat/python/autoload/` directory
  to make the script load automatically when WeeChat starts:

```
$ cd ~/.weechat/python/autoload
$ ln -s ../notify_send.py
```

Settings
--------

The plugin allows you to set the following settings (either by running `/set
plugins.var.python.notify_send.XXX YYY` or by using the
[iset.pl](https://weechat.org/scripts/source/iset.pl.html/) plugin.

* `escape_html`: Escapes the `<`, `>`, and `&` HTML
  characters in notification messages. Default: `on`.
* `icon`: Path to an icon to be shown in notifications. Default:
  `/usr/share/icons/hicolor/32x32/apps/weechat.png`.
* `timeout`: Time after which the notification disappears (in milliseconds).
  Set to 0 to disable. Default: 5000.
* `urgency`: Notification urgency (`low`, `normal`, `critical`). Default:
  `normal`.

License
-------

Copyright (c) 2015 Petr Zemek (s3rvac@gmail.com) and contributors.

Distributed under the MIT license. See the `LICENSE` file for more details.
