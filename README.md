# Artwork Beef

Artwork Beef automatically adds extra artwork for TV shows and movies into your library. It is generally intended to
handle extended artwork just as Kodi and scrapers already do for basic artwork. It grabs artwork from the wonderful web
services [fanart.tv], [TheTVDB.com], and [The Movie Database].

[fanart.tv]: https://fanart.tv/
[TheTVDB.com]: http://thetvdb.com/
[The Movie Database]: https://www.themoviedb.org/

[Support and discussion thread](http://forum.kodi.tv/showthread.php?tid=258886) on the Kodi forums.

It fully supports series and season artwork from TheTVDB.com; movie, series, and season artwork from fanart.tv; and
movie artwork from The Movie Database. For those series that really pop, [high quality fanart] for each episode can be
added from The Movie Database.

[high quality fanart]: http://forum.kodi.tv/showthread.php?tid=236248

The full list of supported artwork types for **movies**: `poster`, `fanart`, `banner`, `clearlogo`, `landscape`, `clearart`, `discart`  
For **series**: `poster`, `fanart`, `banner`, `clearlogo`, `landscape`, `clearart`, `characterart`  
And **seasons**: `poster`, `banner`, `landscape`  
Finally, **episodes**: `fanart`

### Installing

At the moment it depends on a couple of python modules not available in the official Kodi repo, and my own goofy
devhelper, so it will be simplest to install my [dev repository], ([direct]), and then install from "Program add-ons",
and Kodi will take care of downloading the dependencies. The context items can also be installed from the repo from
"Context menus".

[dev repository]: https://github.com/rmrector/repository.rector.stuff
[direct]: https://github.com/rmrector/repository.rector.stuff/raw/master/repository.rector.stuff/repository.rector.stuff-1.0.0.zip

### Usage

Install it. Tada! It will automatically run after library updates, grabbing extended
artwork for new items. The automatic operation is handled by a service that watches
for library updates. You can also run it from Program add-ons to trigger the automatic
process for new or all items; a currently running process can also be canceled here. Finally,
to select specific artwork for individual media items, install the context item "Select
artwork to add", and add all configured artwork with "Add missing artwork". After
installation, these context items are in the context menu for movies, series, and episodes, under "Manage...".

The first run and then roughly every two months it will process all items still missing
artwork, in case new artwork has been submitted to the web services. This may take some
time, if many items are missing some artwork.

Episode fanart requires using a scraper that grabs the TheTVDB ID for each episode, like the standard TheTVDB scraper.
Automatically adding episode fanart must be enabled per series through the add-on settings, as they add a bundle of new
API calls to The Movie Database and just aren't available for many series.

There are add-on settings to specify exactly which types of artwork and how many to
download automatically.

### Skin support

For the most part skins will still access images in the same Kodi standard way. Extrafanart has been replaced by
[multiple fanart](http://forum.kodi.tv/showthread.php?tid=236649), which does require skins to access them differently.

Episode fanart may just work, depending on how your skin accesses fanart when listing episodes.
`$INFO[ListItem.Art(fanart)]` pulls the episode fanart if it exists, otherwise Kodi falls back to the series fanart.

### From NFO and image files

Artwork can be added from a standard [Kodi NFO file] next to your media. Add an `art` element to the root
`movie`/`tvshow`/`episodedetails`, and its children are individual artwork tagged with the exact artwork type and a URL
to the image; there is a full example in `resources/example.nfo`. Kodi uses this same format when exporting the library
to a single file.

Artwork Beef also adds artwork from image files stored next to your media. Name them like basic [Kodi artwork],
replacing "fanart"/"thumb" with the exact artwork type. Kodi names artwork in this same format when exporting the
library to separate files.

If you manage all of your artwork with image files and/or NFO files, the add-on setting
"Auto add artwork from filesystem only" under "Advanced" will prevent the add-on from
querying the web services during automatic processing, saving time and network resources,
and with image files avoids adding duplicates with multiple images of a single type.

Artwork from these files aren't limited to the artwork types listed above; artwork types can be freely named, as long
as they are alphanumeric. The artwork type should have the exact name; for instance, multiple fanart will have one
single `fanart`, one `fanart1`, one `fanart2`, and so on.

[Kodi NFO file]: http://kodi.wiki/view/NFO_files
[Kodi artwork]: http://kodi.wiki/view/Artwork#Naming_conventions

### Current gotchas

- Music video artwork is nowhere to be seen.
- It uses the v2 API from TheTVDB.com, which has a tendency to not list all artwork.
- Results from web services are cached for a full week.
- It expects scrapers to set an IMDB number for movies, and a TVDB ID for series, like the default scrapers.
