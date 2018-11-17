---
title: "Advanced control"
date: 2018-07-12T14:50:55-07:00
weight: 40
---

Extra debug context items that work on individual media items can be enabled in the [add-on settings]({{< ref "usage/settings.md#disable-enable-artwork-beef-debug-context-items-per-skin" >}}).
"AB: Remove all artwork" will remove all artwork from the single selected item.
"AB: Log debug info" will run through the automatic process like "AB: Add missing artwork" and
logs the result to the standard Kodi log, but it doesn't change anything (helpful for troubleshooting).

## Commands

Scripts, skins, and other add-ons can use commands to control bits and pieces of Artwork Beef.

### Run automatic processing on the library

You can disable the automatic processing after library updates and schedule them
with something like the [Kodi Callbacks](https://kodi.wiki/view/Add-on:Kodi_Callbacks) add-on
or trigger them in some other way.

- Process new items
  - `NotifyAll(script.artwork.beef:control, ProcessNewVideos)`
  - `NotifyAll(script.artwork.beef:control, ProcessNewMusic)`
- Process new and old items, but not all in between
  - `NotifyAll(script.artwork.beef:control, ProcessNewAndOldVideos)`
  - `NotifyAll(script.artwork.beef:control, ProcessNewAndOldMusic)`
- Update local artwork only for all items in the video library
  - `NotifyAll(script.artwork.beef:control, ProcessLocalVideos)`

### Run Artwork Beef on individual media items

Like the context menu items generally under "Manage ...", skins can add them somewhere else.

- `RunScript(script.artwork.beef, mode=gui, mediatype=tvshow, dbid=$INFO[ListItem.DBID])`

`mode` can also be "auto", and `mediatype` can be "tvshow", "movie", "episode", "set", "musicvideo",
"artist", "album", and "song".

`mode=gui` isn't a complete replacement for Kodi's built in "Choose art" dialog: users can't unset artwork
from this dialog, nor can they manually navigate to and select other images in the file system.

### Watch for notifications

Artwork Beef will send out a notification when the library processing is finished.

- The sender is `script.artwork.beef` and the message is `Other.OnVideoProcessingFinished`
  or `Other.OnMusicProcessingFinished`.
