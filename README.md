# Artwork Beef

Artwork Beef automatically adds extra artwork for TV shows and movies into your library. It is generally intended to
handle extended artwork just as Kodi and scrapers already do for basic artwork. It grabs artwork from the wonderful web
services [fanart.tv], [TheTVDB.com], and [The Movie Database].

[fanart.tv]: https://fanart.tv/
[TheTVDB.com]: http://thetvdb.com/
[The Movie Database]: https://www.themoviedb.org/

[Support and discussion thread](http://forum.kodi.tv/showthread.php?tid=258886) on the Kodi forums.  
[Source](https://github.com/rmrector/script.artwork.beef) hosted on GitHub.

It fully supports series and season artwork from TheTVDB.com; movie, series, and season artwork from fanart.tv; and
movie artwork from The Movie Database. For those series that really pop, [high quality fanart] for each episode can be
added from The Movie Database.

[high quality fanart]: http://forum.kodi.tv/showthread.php?tid=236248

The full list of supported artwork types for **movies**: `poster`, `fanart`, `banner`, `clearlogo`, `landscape`, `clearart`, `discart`  
For **series**: `poster`, `fanart`, `banner`, `clearlogo`, `landscape`, `clearart`, `characterart`  
And **seasons**: `poster`, `fanart`, `banner`, `landscape`  
Finally, **episodes**: `fanart`

### Installing

It still has one dependency not available in the official Kodi repo, and the context items
are available as separate add-ons so it will be simplest
to install my [dev repository], then install Artwork Beef from "Program add-ons",
and Kodi will take care of downloading the dependency. The context items can also be installed
from the repo from "Context menus".

Artwork Helper can be installed with this single [installable zip], but it's only necessary if a
skin depends on it.

[dev repository]: https://github.com/rmrector/repository.rector.stuff/raw/master/repository.rector.stuff/repository.rector.stuff-1.0.0.zip
[installable zip]: https://github.com/rmrector/repository.rector.stuff/raw/master/script.artwork.helper/script.artwork.helper-0.7.1.zip

### Usage

Install it. Tada! It will automatically run after library updates, grabbing extended
artwork for new items, much like Kodi and scrapers do for info and basic artwork.

You can also run it from Program add-ons to trigger the automatic
process for new or all items; a currently running process can also be canceled here. Finally,
to select specific artwork for individual media items, install the context item "Select
artwork to add", and add all configured artwork with "Add missing artwork". After
installation, these context items are in the context menu for movies, series, and episodes, under "Manage...".

The first run and then roughly every two months (15 days for filesystem only) it will process all items still missing
artwork, in case new artwork has been submitted to the web services. This may take some
time, if many items are missing some artwork.

Episode fanart requires using a scraper that grabs the TheTVDB ID for each episode, like the standard TheTVDB scraper.
You must enable adding episode fanart automatically by series through the add-on settings, as they add a bundle of new
API calls to The Movie Database and just aren't available for many series.

There are add-on settings to specify exactly which types of artwork and how many to
download automatically.

### From NFO and image files

Artwork can be added from a standard [Kodi NFO file] next to your media. Add an `art` element to the root
`movie`/`tvshow`/`episodedetails`, and its children are individual artwork tagged with the exact artwork type and a URL
to the image; there is a full example in `resources/example.nfo`. Kodi uses this same format when exporting the library
to a single file.

Artwork Beef also adds artwork from image files stored next to your media. Name them like basic [Kodi artwork],
replacing "fanart"/"thumb" with the exact artwork type. Kodi names artwork in this same format when exporting the
library to separate files.

Artwork from these files aren't limited to the artwork types listed above; artwork types must be
lowercase and alphanumeric, but can otherwise be freely named. The artwork type should have the exact
name; for instance, multiple fanart will have one single `fanart`, one `fanart1`, one `fanart2`, and so on.

It will also pull in artwork files that match Artwork Downloader file names, in cases where they
are different than the art types used in Kodi, for instance `character.jpg` is added as
`characterart` and extrafanart are added as `fanart#`.

If you manage all of your artwork with image files and/or NFO files, the add-on setting
"Auto add artwork from filesystem only" under "Advanced" will prevent the add-on from
querying the web services during automatic processing, saving time and network resources.

[Kodi NFO file]: http://kodi.wiki/view/NFO_files
[Kodi artwork]: http://kodi.wiki/view/Artwork#Naming_conventions

### Skin support

For the most part skins will still access images in the same Kodi standard way.
Episode and season backdrops may just work, depending on how your skin accesses them when listing
episodes or seasons. `$INFO[ListItem.Art(fanart)]` pulls the episode or season backdrop if it exists,
otherwise Kodi falls back to the series backdrop.

Extrafanart has been integrated [into the library] and no longer has to be in the filesystem,
but does require skins to access them differently. Extrathumbs are similarly integrated, implemented
in the library as `thumb1`, `thumb2`, and so on. [Artwork Helper] is a small add-on that skins can
depend on to easily gather fanart/thumbs for a `multiimage` control. Skins should not list
Artwork Beef as a dependency.

[into the library]: http://forum.kodi.tv/showthread.php?tid=236649
[Artwork Helper]: https://github.com/rmrector/script.artwork.helper

### Current gotchas

- Music video and set artwork will require a new search function, which will come at some point in the future.
- It expects scrapers to set an IMDB number for movies, and a TVDB ID for series, like the default scrapers.
- It cannot set artwork for "all seasons" with JSON-RPC. [related trac ticket](http://trac.kodi.tv/ticket/16139)

### Thoughts

- It doesn't download any artwork, and likely never will; it just adds the URLs to Kodi's database, then Kodi
  downloads them as part of its regular caching process.
- Extrathumbs aren't added from external sources. I don't want to resize backdrops/fanart from TMDB
  like Artwork Downloader (I much prefer to use those for multiple fanart), and generating
  the thumbs are outside the scope of this add-on. An external art/nfo manager could generate them.
  Plugins can also set these to the ListItem, if their source provides more than one thumbnail.
- It would be nice to have a Kodi built-in way for skins to feed multiple art to a `multiimage`,
  maybe something like `$INFO[ListItem.MultiArt(fanart)]` to pull all `fanart` and `fanart#` together.
  I have no idea how it could be implemented in Kodi, though.

Those were my thoughts. **What are yours?** Skinners, viewers/end users, developers, anyone, I'd like
to hear what you think.
