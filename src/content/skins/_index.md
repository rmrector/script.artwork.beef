---
title: "Skin support"
date: 2017-11-21T22:46:49-07:00
weight: 2
---

For the most part, skins will still access images in the same Kodi standard way.
Episode and season fanart may just work, depending on how your skin accesses them when listing
episodes or seasons. `$INFO[ListItem.Art(fanart)]` pulls the episode or season backdrop if it exists,
otherwise, Kodi falls back to the series backdrop.

Extrafanart has been integrated into the library and no longer has to be in the file system,
but does require skins to access them differently. Extrathumbs can be similarly integrated.
[Artwork Helper] is a small add-on that skins can depend on to easily gather fanart/thumbs for a
`multiimage` control either way.

While Artwork Helper is consistently faster than loading extrafanart from a spinning hard drive,
it can still have a noticeable delay compared to directly accessing other artwork with `ListItem.Art(clearlog)`
(especially on Windows). There is a way to gather these images without an add-on, but it's a bit more
work. See [Fun without add-ons] for an example.

Skins should not list Artwork Beef as a dependency, nor depend on its installation for displaying
artwork, as Artwork Beef isn't the only one that can set these. Check for the existence of
`fanart1` to tell if the ListItem has these multiple fanart.

[Artwork Helper]: {{< ref "skins/artworkhelper.md" >}}
[Fun without add-ons]: {{< ref "skins/addonfreefun.md" >}}
