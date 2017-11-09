# Artwork Beef
<span style="font-size: 1.2em; font-weight: 600">An add-on for Kodi</span>

Artwork Beef automatically adds extra artwork for media in your video library. It is generally intended to
handle extended artwork just as Kodi and scrapers already do for basic artwork. It grabs artwork from the wonderful web
services [fanart.tv], [TheTVDB.com], [The Movie Database], and [TheAudioDB.com].

[fanart.tv]: https://fanart.tv/
[TheTVDB.com]: http://thetvdb.com/
[The Movie Database]: https://www.themoviedb.org/
[TheAudioDB.com]: http://www.theaudiodb.com/

It is developed for Kodi 17 **Krypton**, and should also work for 16 **Jarvis** and 18 **Leia**.
15 Isengard should mostly still work, but it's really time to update.  
[Support and feedback thread](https://forum.kodi.tv/showthread.php?tid=258886) on the Kodi forums.  
[Source](https://github.com/rmrector/script.artwork.beef) hosted on GitHub.

It fully supports series and season artwork from TheTVDB.com; movie, movie set, music video, series,
and season artwork from fanart.tv; movie and movie set artwork from The Movie Database;
and music video artwork from TheAudioDB.
For those series that really pop, [high-quality fanart] for each episode can be
added from The Movie Database.

[high-quality fanart]: https://forum.kodi.tv/showthread.php?tid=236248

The full list of artwork types grabbed from external web services:  
**movies** and **movie sets**: `poster`, `fanart`, `banner`, `clearlogo`, `landscape`, `clearart`, `discart`  
**music videos**: `poster` (album/single cover), `cdart`, `fanart`, `artistthumb`, `banner`, `clearlogo`  
**series**: `poster`, `fanart`, `banner`, `clearlogo`, `landscape`, `clearart`, `characterart`  
**seasons**: `poster`, `fanart`, `banner`, `landscape`  
**episodes**: `fanart`  

It will also prefer local artwork stored in the file system if it exists.

### Installing

Install my [dev repository] to get updates delivered to you automatically. After the repo is
installed, Artwork Beef can be installed from "Program add-ons". Artwork Beef can also
be installed with a [single zip file], but you will have to return here for updates.

_Artwork Helper_ can be installed with this single [installable zip] for Kodi 17 and above
(or this one [for Kodi 16] and below), but it's only necessary if a skin depends on it.
Inclusion in the official Kodi repo isn't likely for now, some of this functionality may make
its way into Leia so it will probably see some feature churn before long.

These URLs will always point to the latest stable version.

[dev repository]: https://github.com/rmrector/repository.rector.stuff/raw/master/latest/repository.rector.stuff-latest.zip
[single zip file]: https://github.com/rmrector/repository.rector.stuff/raw/master/latest/script.artwork.beef-latest.zip
[installable zip]: https://github.com/rmrector/repository.rector.stuff/raw/master/latest/script.artwork.helper-latest.zip
[for Kodi 16]: https://github.com/rmrector/repository.rector.stuff/raw/master/latest/script.artwork.helper-jarvis-latest.zip

### Usage

Install it. Tada! It will automatically run after library updates, grabbing extended
artwork for new items, much like Kodi and scrapers do for info and basic artwork.

You can also run it from Program add-ons to trigger the automatic process for new or all items, or existing
items that need an update; a currently running process can also be canceled here. To operate on a single
media item, open the context menu on that item, then under "Manage..." there are options
to automatically "Add missing artwork" or manually "Select artwork...".

Over time it will re-process media items still missing artwork, checking for new artwork from
web services and the file system.

**Episode fanart** requires using a scraper that grabs the TheTVDB ID for each episode, like the standard TheTVDB scraper.
You must enable adding episode fanart manually for each series through the add-on settings, as they add a bundle of new
API calls to The Movie Database and just aren't available for many series.

Grabbing **movie set artwork** from web services may not work automatically if the set name in
Kodi doesn't exactly match the set name on TheMovieDB. After your sets are processed for the
first time, run Artwork Beef from Program Add-ons and select "identify unmatched sets with TheMovieDB"
to show a list of all still-unmatched movies sets, then select one and enter the name of the set
exactly as it is on TheMovieDB. If a set was matched incorrectly, navigate to the set in the video
library and choose "Select artwork..." from the "Manage" menu of the context menu, then choose "Search for set".

There are add-on settings to specify exactly which types of artwork and how many to download automatically.
Under "Advanced" there are settings to generate a thumbnail from video files for movies, episodes, and music videos
(this requires the Kodi setting "Extract thumbnails and video information" under "Media" -> "Videos" to be enabled).

If you have multiple Kodi installations sharing a database, only enable the automatic
processing on one of them. Don't use Artwork Beef's automatic processing with Artwork Downloader's
full library mode. The results won't be terrible, but they'll step all over each
other and take up extra time and network resources.

### From NFO and image files

Artwork can be added from image files stored next to your media. Name them `[media file name]-[art type].[ext]` for
movies, episodes, and music videos; `[art type].[ext]` for TV shows and as an alternative for movies and MVs,
Kodi names artwork in this same format when exporting the library to separate files.

Artwork Beef also adds artwork from a standard [Kodi NFO file] next to your media. Add an `art` element to the root
`movie`/`tvshow`/`episodedetails`/`set`/`musicvideo`, and its children are individual
artwork tagged with the exact artwork type and a URL to the image; there is a full example in
`resources/example.nfo`. Kodi uses this same format when exporting the library
to a single file, except sets.

**Movie set artwork** can be pulled from a central directory (configured in the add-on settings),
containing artwork named `[set name]-[art type].[ext]`, and NFO file named `[set name].nfo`.
This central directory can also contain subdirectories named exactly as the sets, with images inside
named `[art type].[ext]`, NFO file named `set.nfo`. Finally, Artwork Beef can also
be configured to pull set artwork from a parent directory of movies, if the directory name exactly matches
the set name, with artwork named `[art type].[ext]`, NFO file named `set.nfo`. This should match artwork
arranged for [Movie Set Artwork Automator].

Artwork from these files aren't limited to the artwork types listed above; artwork types must be
lowercase and alphanumeric, but can otherwise be freely named. The artwork type should have the exact
name to be set in Kodi; for instance, multiple fanart will have one single `fanart`,
one `fanart1`, one `fanart2`, and so on.

It will also pull in artwork files that match Artwork Downloader file names, in cases where they
are different than the art types used in Kodi; for instance, `character.png` is added as
`characterart` and extrafanart are added as `fanart#`. Ditto MSAA, but only for its default
filenames (`logo.png` to `clearlogo`, `folder.jpg` to `thumb`).

If you are using NFO and/or image files, use a [separate directory] for each movie.
If you manage all of your artwork with image files and/or NFO files, the add-on setting
"Auto add artwork from filesystem only" under "General" will prevent the add-on from
querying the web services during automatic processing, saving time and network resources.

[Kodi NFO file]: http://kodi.wiki/view/NFO_files
[Movie Set Artwork Automator]: https://forum.kodi.tv/showthread.php?tid=153502
[separate directory]: http://kodi.wiki/view/Movies_(Video_Library)

### Skin support

For the most part, skins will still access images in the same Kodi standard way.
Episode and season fanart may just work, depending on how your skin accesses them when listing
episodes or seasons. `$INFO[ListItem.Art(fanart)]` pulls the episode or season fanart if it exists,
otherwise, Kodi falls back to the series fanart.

Extrafanart has been integrated into the library and no longer has to be in the file system,
but does require skins to access them differently. Extrathumbs can be similarly integrated.
You can use a `fadelabel` to feed the `fanart` and all `fanart#` together for an `image`/`multiimage` control
(See the file [resources/example-multifanart.xml] for an example), or your skin can depend on [Artwork Helper],
a small plugin that provides a number of paths that can be used to fill a `multiimage` control for the
currently selected item.

[Artwork Helper]: https://github.com/rmrector/script.artwork.helper
[resources/example-multifanart.xml]: resources/example-multifanart.xml

### Current gotchas

- Scrapers and NFO files need to set web service IDs like IMDB number, TVDB ID, or TMDB ID
  for media types that Kodi supports such IDs for: movies, TV shows, and episodes
- It doesn't add animated artwork, yet
- It's not in the official Kodi repo, yet
- It cannot set artwork for "all seasons". [related trac ticket](https://trac.kodi.tv/ticket/16139)

### Thoughts

- It doesn't download any artwork; it just adds the URLs to Kodi's database, then Kodi
  downloads them as part of its regular caching process.
- Movie thumbnails aren't added from external sources. There is no way to tell the difference between stills
  and press/marketing images from the web services, while thumbs should only include stills; resizing
  them currently requires downloading them, which I want to avoid, see above. If they aren't resized nor
  different than fanart then skins can use multiple fanart for the same purpose. Generating more than one thumb from
  a video file is outside the scope of this add-on, but any provided by an art file/nfo manager is added to the library.
  Plugins can also set these to the ListItem, if their source provides more than one thumbnail.
- It would be nice to have a Kodi built-in way for skins to feed multiple art to a `multiimage`,
  maybe something like `$INFO[ListItem.MultiArt(fanart)]` to pull all `fanart` and `fanart#` together.
  I have no idea how it could be implemented in Kodi, though.

Those were my thoughts. **What are yours?** Skinners, viewers/end users, developers, anyone, I'd like
to hear what you think.
