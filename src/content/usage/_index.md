---
title: "Installation & usage"
date: 2017-11-21T22:46:04-07:00
weight: 1
---

## Installing

Install my [dev repository] to get updates delivered to you automatically. After the repo is
installed, Artwork Beef can be installed from "Program add-ons". It can also
be installed with a [single zip file], but you will have to return here for updates.

**Artwork Helper** can be installed with this single [installable zip], but it's only necessary if a
skin depends on it.
Inclusion in the official Kodi repo isn't likely for now, some of this functionality may make
its way into Leia so it will probably see some feature churn before long.

[dev repository]: https://github.com/rmrector/repository.rector.stuff/raw/master/latest/repository.rector.stuff-latest.zip
[single zip file]: https://github.com/rmrector/repository.rector.stuff/raw/master/latest/script.artwork.beef-latest.zip
[installable zip]: https://github.com/rmrector/repository.rector.stuff/raw/master/latest/script.artwork.helper-latest.zip

## Usage

Install it, and configure it to your liking. It is designed to run after library updates with the
add-on settings "Automatically add artwork for new videos" and "Automatically add artwork for new music".

{{% notice note %}}
There are a few actions and settings you may want to flip before letting Artwork Beef do its thing.
See [First usage]({{< ref "usage/firstusage.md" >}}) for details.
{{% /notice %}}

### Automatic processing

Artwork Beef must process all items in your library, and will do so automatically the first
time it runs. Over time (4-8 months) it will re-process media items still missing artwork,
checking for new artwork from web services and the file system. If the option "only identify local files"
is enabled it will check for new local artwork files monthly.

### Manual processing

You can also run it from Program add-ons to trigger the automatic process for new or all items, or items old
enough to need an update; a currently running process can also be canceled here. Some other
actions are available here. To operate on a single
media item, open the context menu on that item, then under "Manage..." there are options
"AB: Add missing artwork" which processes the single item like the automatic process, checking for
new local files and searching the web services for any missing art; and "AB: Select artwork..." to
manually select new artwork.

### Episode fanart

Episode fanart requires using a scraper that grabs the TheTVDB ID for each episode, like the
standard TheTVDB scraper and The Movie Database _TV show_ scraper, or an NFO manager that does the same.
You must enable adding episode fanart manually for each series through the add-on settings, as they add a bundle of new
API calls to The Movie Database and just aren't available for many series.

### Change report

It generates a report of changes to
[userdata](http://kodi.wiki/view/Userdata)/addon_data/script.artwork.beef/artwork-report.txt.
