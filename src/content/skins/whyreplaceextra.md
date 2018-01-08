---
title: "Why replace extrafanart/extrathumbs"
date: 2017-11-21T22:46:53-07:00
---

- Kodi's support for freely named artwork in the library is pretty great, so let's use it!
- Avoid filesystem delays/access issues (unavailable network file system, removable media) when
  the images have been cached. Classic extrafanart always had to hit the file system at least
  once when the path changed to get a list of all extrafanart, even if they were all cached.
- Skins can more easily work with all fanart together (main + extra fanart)
  - There are **plugin://** paths to stitch together fanart images for 'multiimage' controls,
    'fanart' and 'fanart#' alike! See [Artwork Helper]({{< ref "skins/artworkhelper.md" >}}).
  - It is also possible to do without an add-on dependency at all, see
    [Fun without add-ons]({{< ref "skins/addonfreefun.md" >}}).
- Skins don't have to worry about detecting if the media item has extrafanart, so that they
  need to display the main fanart or risk leaving a gaping hole.
- Skins can look up each fanart image directly, which makes it simpler to display more than
  one at a time in arbitrary locations. I think I remember playing around with a Nox way back
  in the day that did this with extrathumbs.
- It works for items in the library that may not point to a location on a file system that
  should even care about artwork on this/any level, maybe a movie from UPNP or whatever.
- Plugins can fill their own ListItems with this artwork, which skins can access in exactly the same way.
- Should generally work for other library items that can have freely named artwork;
  movie sets, music videos, TV show seasons, episodes, even music artists, albums, and songs.
- Get that gross nasty other stuff out of your file system, if you also think it is gross and nasty.
  - Ugh. This is of course the simplest and most obvious way to share information among different
    Kodi installs, so maybe I'm a bit unreasonable here.
