---
title: "Why replace extrafanart/extrathumbs"
date: 2017-11-21T22:46:53-07:00
---

- Kodi's support for freely named artwork in the library is pretty great, so let's use it!
- Placing artwork in the library allows skins to work with multiple fanart no matter where they
  are stored.
- Avoid filesystem delays/access issues (unavailable network file system, removable media) when
  the images have been cached. Classic extrafanart always hits the file system at least once
  when first listing the path to get a list of the images, even if they are all cached.
- Skins can more easily work with all fanart together (main + extra fanart)
  - Display them in a `multiimage` control with a skin structure described in
    [Fun without add-ons]({{< ref "skins/addonfreefun.md" >}}).
  - There are also **plugin://** paths to accomplish this.
    See [Artwork Helper]({{< ref "skins/artworkhelper.md" >}}).
- Skins can look up each fanart image directly, which makes it simpler to display more than
  one at a time in arbitrary locations.
  - Probably overkill for fanart, but other art types could be multiplied for great effect.
    I've been playing with [characterart]({{< ref "examples/_index.md#and-multiple-characterart" >}}).
- It works for items in the library that may not point to a location on a file system that
  should even care about artwork on this/any level, maybe a movie from UPNP or whatever.
- Plugins can fill their own ListItems with this artwork, which skins can access in exactly the same way.
- Should generally work for other library items that can have freely named artwork;
  movie sets, music videos, TV show seasons, episodes, even music artists, albums, and songs.
- Get that gross nasty other stuff out of your file system, if you also think it is gross and nasty.
  - Ugh. This is of course the simplest and most obvious way to share information among different
    Kodi installs, so maybe I'm a bit unreasonable here.
