---
title: "Fun without add-ons"
date: 2017-11-21T22:44:56-07:00
weight: 10
---

Because who wants another dependency?

### Display multiple fanart

Artwork Helper isn't strictly needed, how about that? It is a bit more work though.

The trick is to use a `fadelabel` control to gather multiple InfoLabels and randomize them,
then use that control's label as the final image to be displayed.

```xml
<control type="fadelabel" id="398045">
	<description>Randomizer for plugin-free multiple fanart</description>
	<top>-1000</top> <!-- Don't need to see it, but can't change its visibility. Put it off screen -->
	<width>1</width>
	<height>1</height>
	<info>ListItem.Art(fanart)</info>
	<info>ListItem.Art(fanart1)</info>
	<info>ListItem.Art(fanart2)</info>
	<!-- ... repeat for each numbered fanart -->
	<info>ListItem.Art(fanart9)</info>
	<!-- tvshow.fanart are filled with the series fanart when navigating season and episode lists -->
	<info>ListItem.Art(tvshow.fanart)</info>
	<info>ListItem.Art(tvshow.fanart1)</info>
	<info>ListItem.Art(tvshow.fanart2)</info>
	<!-- ... repeat for each numbered fanart -->
	<info>ListItem.Art(tvshow.fanart9)</info>
	<!-- Container.ListItem.Art() are filled based on the focused ListItem in the **focused container** in Leia -->
	<info>Container.ListItem.Art(fanart)</info>
	<info>Container.ListItem.Art(fanart1)</info>
	<info>Container.ListItem.Art(fanart2)</info>
	<info>Container.ListItem.Art(tvshow.fanart)</info>
	<info>Container.ListItem.Art(tvshow.fanart1)</info>
	<info>Container.ListItem.Art(tvshow.fanart2)</info>
	<randomize>true</randomize>
	<pauseatend>30000</pauseatend> <!-- Time to show each image, in milliseconds -->
	<!-- No scrolling so only the pauseatend above (plus a short fade-in) affects length of time each
		image is shown -->
	<scroll>false</scroll>
	<scrollout>false</scrollout>
	<!-- Resets the timer when navigating to a new item, so each item's first visible fanart will
		show for the full amount of time -->
	<resetonlabelchange>true</resetonlabelchange>
</control>
```

With that on your window, the InfoLabel `$INFO[Control.GetLabel(398045)]` will contain the URL/path
to a single image that can be given to an `image` or `multiimage` path, and it will randomly
rotate through every available image. It will skip any that are empty, so no blank spaces will be
left.

You can make another structure with Player.Art for music visualization or a fullscreen now-playing window.

### Grab random fanart (plus any other info) from items in any library path

Stick this little invisible list on your window somewhere:

```xml
<control type="list" id="12341">
	<content sortby="random">videodb://movies/titles/</content>
	<autoscroll time="30000">true</autoscroll> <!-- Time to show each image, in milliseconds -->
	<itemlayout />
	<focusedlayout />
</control>
```

The path in the `<content>` element can be any path that Kodi supports, including any  `videodb` paths
in the library, playlists, and plugins, as long as it directly contains items with fanart.

Then `$INFO[Container(12341).ListItem.Art(fanart)]` will contain the URL/path to a single image
that can be given to an `image` or `multiimage` path, and it will randomly rotate through every item
in the list. Use any other ListItem InfoLabels as you need them.

On `MyVideoNav`, when navigating categories like genres, studios, and years, this can pull fanart from items
in just the focused category item by using `$INFO[ListItem.FolderPath]` for the `<content>` element.
Big lists can take some time to fill when a new item is focused, so try a `limit="20"` attribute to the
content element.

This can be combined with "Display multiple fanart" above to pick from all fanart set for all items
in the list. Set the `fadelabel` timer to be longer than this list to still display just one image
from each item, or shorter to flip through more than one fanart for each item.

**NOTE**: This works best with lists of items that mostly all have fanart, which may be a deal-breaker
depending on your design, so keep it in mind when choosing this add-on free route.

#### Interesting path options

- All movies - `videodb://movies/titles/`
- All TV shows - `videodb://tvshows/titles/`
- All album artists - `musicdb://artists/?albumartistsonly=true`
- Skin playlists - `special://skin/playlists/random_albums.xsp`
- User playlists - `special://profile/playlists/video/latest_episodes.xsp`
- Custom video nodes to separate concerts/children's shows/sports games/etc
  + `library://video/movies/concerts.xml/`
  + `library://video/movies/notconcerts.xml/`
  + `library://video/tvshows/children.xml/`
  + `library://video/tvshows/notchildren.xml/`
  - playlists can be used for similar purposes

#### Combining multiple paths

One limitation of this vs an add-on is that there is no global library list that includes
every media item in the library. Kodi 18 Leia adds a new feature that may convincingly accomplish
something similar. Multiple content elements can be provided, so replace the single `<content>`
above with something like below:

```xml
	<content sortby="random" limit="5">videodb://movies/titles/</content>
	<content sortby="random" limit="5">videodb://musicvideos/titles/</content>
	<content sortby="random" limit="5">videodb://tvshows/titles/</content>
	<content sortby="random" limit="5">videodb://movies/sets/</content>
	<content sortby="random" limit="5">musicdb://artists/</content>
	<content sortby="random" limit="5">videodb://movies/titles/</content>
	<content sortby="random" limit="5">videodb://musicvideos/titles/</content>
	<content sortby="random" limit="5">videodb://movies/sets/</content>
	<content sortby="random" limit="5">videodb://tvshows/titles/</content>
	<content sortby="random" limit="5">musicdb://artists/</content>
```

The limit is low to avoid grouping too many of the same item together ("That's not very random!"),
and then repeat the available paths at least once to add back a bit of variety.

### Does an episode or season have its own fanart?

If `ListItem.Art(fanart)` is the same image as `ListItem.Art(tvshow.fanart)` then it is a fallback
image and the episode doesn't have its own. A variable value like below will show the single fanart
image alone, because an episode with its own fanart is fancy.

```xml
<value condition="[Container.Content(episodes) | Container.Content(seasons)] + !String.IsEqual(ListItem.Art(tvshow.fanart), ListItem.Art(fanart))">$INFO[ListItem.Art(fanart)]</value>
```
