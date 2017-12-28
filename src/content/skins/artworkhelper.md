---
title: "Artwork helper"
date: 2017-11-21T22:45:47-07:00
weight: 10
---

Artwork Helper provides skins with a few options for building a list of images for a `multiimage`
or list control from images available via InfoLabels.
This is a small add-on that skins can use as a dependency, only doing what a skin asks it to do.

Current version only works for Kodi 17 and 18, use version 0.7.1 for 15 and 16.

## Add-on setting

There is an add-on setting to pull extrafanart and extrathumbs from the filesystem, if there is
only a single image in the library. It is off by default, but can be turned on by the end user/viewer.
This setting is not needed if Artwork Beef is used to manage artwork.
It can be found by navigating to Kodi settings -> System settings -> Add-ons -> Manage dependencies -> Artwork Helper.
The Settings level may need to be set to Advanced to see dependencies in "Add-ons".

## Paths built from InfoLabels

These paths use InfoLabels to gather image URLs just like skins do.

### ListItem multi image plugin path

The simplest form grabs multiple images for the currently focused ListItem.  
`plugin://script.artwork.helper/multiimage/listitem/?refresh=$INFO[ListItem.DBID]`

Mostly for fanart (fanart#), but works for any art type that has one or more images.
Additional query params are available to modify its behavior, separate them with `&amp;&amp;`.

- `refresh` is required to get Kodi to fire off the plugin when the focused item changes. Set it
  to something that will change when the fanart should change, like ListItem.DBID or Label
- `containerid` points to the current ListItem in a specific container; either leave blank for the currently selected
  container on the **Kodi 18 home window**, or set to the desired container's skin ID
- `arttype` lets you select different artwork. Defaults to 'fanart'.

With the full complement of options:  
`plugin://script.artwork.helper/multiimage/listitem/?refresh=$INFO[Container.ListItem.DBID]&amp;&amp;containerid=&amp;&amp;arttype=tvshow.fanart`

### Container multi image plugin path

This grabs multiple images for the current skin Container.  
`plugin://script.artwork.helper/multiimage/container/?refresh=$INFO[Container.FolderName]`

Additional query params are available to modify its behavior, separate them with `&amp;&amp;`.

- `refresh` is required to get Kodi to fire off the plugin when the focused item changes. Set it
  to something that will change when the fanart should change, like Container.FolderName
- `arttype` lets you select different artwork. Defaults to 'tvshow.fanart'.

With the full complement of options:  
`plugin://script.artwork.helper/multiimage/container/?refresh=$INFO[ListItem.DBID]&amp;&amp;arttype=set.fanart`

### Smart series multi image plugin path

This grabs multiple images for the current series, keeping the path the same through
series-season-episode lists so that the fanart display stays smooth (only on the video library window).
`plugin://script.artwork.helper/multiimage/smartseries/?title=$INFO[ListItem.Title]`

Additional query params are available to modify its behavior, separate them with `&amp;&amp;`.

- `title` is required to get Kodi to fire off the plugin when the focused item changes, like
  'refresh' in ListItem/Container paths. Set it to ListItem.Title if Container.Content is tvshows
  and Container.TVShowTitle if seasons/episodes.
- `arttype` lets you select different artwork. Defaults to 'fanart'. Use only the base
  art type like 'fanart', the plugin will decide if tvshow.* is needed.

With the full complement of options:  
`plugin://script.artwork.helper/multiimage/smartseries/?title=$INFO[ListItem.Title]&amp;&amp;arttype=fanart`

### Arbitrary images plugin path

This format lets you stitch any images together into a list by specifying their paths.  
`plugin://script.artwork.helper/multiimage/?image=<image_path>&amp;&amp;image=<image_path>&amp;&amp;image=<image_path>&amp;&amp;image=<image_path>&amp;&amp;image=<image_path>&amp;&amp;image=<image_path>`

When the ListItem option above doesn't work for you, this is your very wordy friend. Repeat the
image block for as many images as you like, and it will ignore empty ones. The
double ampersand `&amp;&amp;` separator between images is required.

This path doesn't read any InfoLabels like the others, just returning the images you gave it into a
format that `multiimage` or list controls can use. You can of course pass in the image paths from
the InfoLabels yourself.
