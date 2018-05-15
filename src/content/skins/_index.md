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

The music library just got a "Kodi standard way" in Kodi 18. Skins can access all artwork from the
library just like they do from the video library. Prefixes for artwork like 'artist.' and 'album.'
and 'albumartist.' pull up parent artwork from songs in the same way 'tvshow.' is used in the video
library. 'artist.' is also available for albums. `discart` for multiple disc albums are a bit hairier,
as discs aren't a separate media item in the Kodi library with their own place for artwork.
Artwork Beef will add separate discart as `discart1`, `discart2`, and so on to the album; use a variable like
below to pick the right one for a song ListItem.

```xml
<variable name="ListItemSongDiscart">
	<value condition="Integer.IsEqual(ListItem.DiscNumber,1) + !String.IsEmpty(ListItem.Art(album.discart1))">$INFO[ListItem.Art(album.discart1)]</value>
	<value condition="Integer.IsEqual(ListItem.DiscNumber,2) + !String.IsEmpty(ListItem.Art(album.discart2))">$INFO[ListItem.Art(album.discart2)]</value>
	<value condition="Integer.IsEqual(ListItem.DiscNumber,3) + !String.IsEmpty(ListItem.Art(album.discart3))">$INFO[ListItem.Art(album.discart3)]</value>
	<value condition="Integer.IsEqual(ListItem.DiscNumber,4) + !String.IsEmpty(ListItem.Art(album.discart4))">$INFO[ListItem.Art(album.discart4)]</value>
	<value condition="Integer.IsEqual(ListItem.DiscNumber,6) + !String.IsEmpty(ListItem.Art(album.discart6))">$INFO[ListItem.Art(album.discart6)]</value>
	<value condition="Integer.IsEqual(ListItem.DiscNumber,7) + !String.IsEmpty(ListItem.Art(album.discart7))">$INFO[ListItem.Art(album.discart7)]</value>
	<value condition="Integer.IsEqual(ListItem.DiscNumber,8) + !String.IsEmpty(ListItem.Art(album.discart8))">$INFO[ListItem.Art(album.discart8)]</value>
	<value condition="Integer.IsEqual(ListItem.DiscNumber,9) + !String.IsEmpty(ListItem.Art(album.discart9))">$INFO[ListItem.Art(album.discart9)]</value>
	<value>$INFO[ListItem.Art(album.discart)]</value>
</variable>
```
