---
title: "First usage"
date: 2017-12-27T22:45:06-07:00
weight: 2
---

- Artwork Beef must process all items in your library, and will do so automatically. There are some
  artwork in the file system that isn't added to Kodi's database with any/many other tools. It
  will also check web services for new artwork to fill out any media items still missing some, unless
  "Automatically add artwork from file system only" is enabled.
- If you haven't been managing **movie collection** artwork, Kodi sets posters and fanart to those of one of the movies
  in the collection. You may want to run Artwork Beef from Program Add-ons and remove all existing artwork from
  movie collections before running Artwork Beef's full process.
- If you manage all of your artwork with **image files** and/or NFO files, the add-on setting
  "Automatically add artwork from file system only" under "Advanced" will prevent the add-on from
  querying the web services during automatic processing, saving time and network resources.
  - You may also want to disable "Update artwork for old items daily" if you don't frequently add
    new artwork for existing items in the library.
- If you have multiple Kodi devices sharing a MySQL database, only enable the
  automatic processing on one of them.
- For multiple Kodi devices with their own databases and you want Artwork Beef to download
  **image files** to be shared across them, enable "Automatically add artwork from file system only" on
  all but the master Kodi device.

Okay, so these are more interesting just _after_ the first run:

- Grabbing **movie collection** artwork from web services may not work automatically if the collection name in
  Kodi doesn't exactly match the collection name on TheMovieDB. After your collections are processed for the
  first time, run Artwork Beef from Program Add-ons and select "identify unmatched sets with TMDb"
  to show a list of all still-unmatched movies collections, then select one and enter the name of the collection
  exactly as it is on TheMovieDB. If a collection was matched incorrectly, navigate to the collection in the video
  library and choose "Select artwork..." from the "Manage" menu of the context menu, then choose "Search for item".
- Ditto **music video** artwork, but when entering the name use `[artist name] - [track name]` to search
  on TheAudioDB.
