---
title: "Why replace extrafanart/extrathumbs"
date: 2017-11-21T22:46:53-07:00
---

I think that multiple fanart for individual media items should be integrated into the
library like all other artwork. Here is a list of my reasons.

1. Media file organization and skin display should be completely independent.
2. Skins and other interfaces should access all library artwork in the same way.

or a list of particulars:

- Kodi's support for freely named artwork in the library is pretty great, so let's use it!
- It works for items in the library that may not point to a location on a file system that
  should even care about artwork on this/any level, maybe a movie from UPNP or VOD plugin.
- Plugins can fill their own ListItems with this artwork, which skins can access in exactly the same way.
- Should generally work for other library items that can have freely named artwork;
  movie sets, music videos, TV show seasons, episodes; even music artists, albums, and songs.
- Placing artwork in the library allows skins to work with multiple fanart without demanding one
  specific location for the files. Users can decide to keep them with their media files or
  in a secondary location, separated from the media for non-Kodi access. It can
  also be stored and accessed as URLs to web services or private information servers
  like Plex and Emby, just like all other artwork.
- Avoid file system delays or access issues (unavailable network file system, removable media, disk spinup)
  once the images have been cached. Classic extrafanart always hits the file system at least once for each
  movie/TV show when first listing the path to get a list of the images, even if they are all cached.
- Skins can more easily work with all fanart together (main + extra fanart)
  - Display them in a `multiimage` control with a skin structure described in
    [Fun without add-ons]({{< ref "skins/addonfreefun.md" >}}).
  - There are also **plugin://** paths to accomplish this.
    See [Artwork Helper]({{< ref "skins/artworkhelper.md" >}}).
- Skins can look up each fanart image directly, which makes it simpler to display more than
  one at a time in arbitrary locations.
  - Probably overkill for fanart, but other art types could be multiplied for great effect.
    I've been playing with [characterart]({{< ref "examples/_index.md#and-multiple-characterart" >}}).
