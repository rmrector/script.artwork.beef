# Artwork Beef

Artwork Beef adds extended artwork for your movies and series to your library from the wonderful web services fanart.tv, TheTVDB.com, and The Movie Database. Artwork Downloader has served me well for some time, but now I want more out of an artwork doohickey.

It automatically adds artwork for new media items as they are added to your library. It plays nicely with the web services (and greatly speeds up scanning for artwork for new items) by skipping items that it has processed recently.

It fully supports series and season artwork from TheTVDB.com; movie, series, and season artwork from fanart.tv; and movie artwork from The Movie Database. For those series that really pop, [high quality fanart](http://forum.kodi.tv/showthread.php?tid=236248) for each episode can be added from The Movie Database.

### Installing

At the moment it depends on a couple of python modules not available in the official Kodi repo, and my own goofy devheper, so it will be simplest to install my [dev repository](https://github.com/rmrector/repository.rector.stuff), and then install it from there. The context items can also be installed from the repo.

### Usage

Install it. Tada! It's a work in progress, so there are all sorts of things that can go wrong, but that is the idea.

For individual media items, use context items "Select Artwork to Download" to select specific artwork, and "Download All Artwork" to download all configured artwork.

Episode fanart requires using the standard TheTVDB scraper for series. Automatically adding episode fanart must be enabled per series, as they add a bundle of new API calls to The Movie Database and just aren't available for many series.

### Skin support

For the most part skins will still access images in the same way. Extrafanart has been replaced by [multi fanart](http://forum.kodi.tv/showthread.php?tid=236649), which does require skins to access them differently.

### Current gotchas

- It does not support local artwork, images in the filesystem next to your media.
- It adds the full complement of extended artwork during automatic operation, the only option being to limit the number of fanart for movies and series.
- There aren't very many other options, either.
- Music video artwork is nowhere to be seen.
- It's very chatty. Moo.
- It uses the beta v2 API from TheTVDB.com, which can be a bit goofy.
- Results from web services are cached for a full week.
