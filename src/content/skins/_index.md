---
title: "Skin support"
date: 2017-11-21T22:46:49-07:00
weight: 3
---

For the most part, skins will still access images in the same Kodi standard way.
Episode and season fanart may just work, depending on how your skin accesses them when listing
episodes or seasons. `$INFO[ListItem.Art(fanart)]` pulls the episode or season backdrop if it exists,
otherwise, Kodi falls back to the series backdrop.

Extrafanart has been integrated into the library and no longer has to be in the file system,
but does require skins to access them differently. Extrathumbs can be similarly integrated.
Skins can gather multiple fanart for random display with a `fadelabel`; see [Fun without add-ons] for an example.

[Artwork Helper] is a small add-on that skins can depend on to more easily gather fanart/thumbs for a
`multiimage` control. It can still have a noticeable delay compared to directly accessing
other artwork with `ListItem.Art(clearlogo)` (especially on Windows), so skins that have a greater
focus on fanart will probably prefer the plugin-free route.

Skins should not list Artwork Beef as a dependency, nor depend on its installation for displaying
artwork, as Artwork Beef isn't the only one that can set these. Check for the existence of
`fanart1` to tell if the ListItem has these multiple fanart.

[Artwork Helper]: {{< ref "skins/artworkhelper.md" >}}
[Fun without add-ons]: {{< ref "skins/addonfreefun.md" >}}
