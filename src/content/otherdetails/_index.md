---
title: "Problems and other questions"
date: 2018-03-22T18:00:25-07:00
weight: 2
---

#### How do I quick-start this thing?

- The quickest way to get started is to install it and configure it to your liking.
- Do you want Artwork Beef to automatically add artwork for new media?
    - Enable the setting "Add artwork for new videos after library updates" and / or
      "Add artwork for new music after library updates".
- Do you want Artwork Beef to download image files to your local file system?
    - Then enable the settings "Download image files for processed ..." for each media type
      at the top of the 'TV shows', 'Movies', 'Music videos', and 'Music' tabs.
- Do you want Artwork Beef to only identify artwork you have already gathered locally with
  a media manager, avoiding web services for automatic processing?
    - Enable the setting "Do not automatically add artwork from web services, only identify local files".
- Do you want Artwork Beef to ignore certain media types during automatic processing?
    - Turn on the settings "Disable all automatic processing ..." for that media type.
- See [First usage]({{< ref "usage/firstusage.md" >}}) for more details.

#### Why don't I see new artwork I just submitted to a web service when manually selecting artwork?

- It may take a few days for new artwork to be available.
- Artwork Beef caches the previous image results from web services for 72 hours.

#### Images from web services are not visible.

Most likely the web service is temporarily/intermittently unavailable. Try again later.
Configuring Artwork Beef to download artwork to your local file system is probably a good idea.

#### Manual selection of artwork doesn't show any artwork from one or any web service.

- Does it happen for all media items of a particular type?
    - Have you futzed with API keys other than the Fanart.tv personal API key?
        - Reinstall Artwork Beef from the latest _stable_ zip and try again before changing
          the API keys.
  - Or maybe the web service is temporarily unavailable, or your Kodi device's internet connection
    is broken. The Kodi log and Artwork Beef's artwork report may have more details.
  - Otherwise post a reply on the forum thread with a description of the problem, a
    [Kodi debug log], and the latest group of artwork-report.txt.
- Or just a handful of media items?
  - Artwork Beef requires web service IDs (like an IMDB number) in the Kodi library. These
    should be included in NFO files or scrapers.
      - If you use scrapers for the media item, make sure your scrapers are up to date and
        refresh the item.
      - If you have NFO files, make sure there is a "uniqueid" element in it.
        An "imdbnumber" element should also work (for movies and TV shows), and an "id" element might work.
        If your NFOs don't have these elements then upgrade your media manager and recreate the NFOs,
        then refresh the item in Kodi.
      - Music must be tagged with MusicBrainz IDs. Use MusicBrainz Picard for tagging files.

[Kodi debug log]: https://kodi.wiki/view/Debug-log

#### The Kodi skin or web interface is showing a thumbnail image instead of a movie poster.

The skin / web interface is pulling up the movie thumb and expecting the fallback poster,
but it should instead pick the poster first and fall back to the thumb only if the poster
doesn't exist. They are two different images for two different purposes and should be chosen
based on the interface design.

#### Where do I put my API keys for other web services?

- At the bottom of the Advanced page of add-on settings.

#### Where is the option to replace the fanart slideshow from Artwork Downloader?

No such option is available, Artwork Beef will not duplicate image files for this purpose.
[Skins have other options] that don't require duplicating files.

[Skins have other options]: {{< ref "skins/addonfreefun.md#grab-random-fanart-plus-any-other-info-from-items-in-any-library-path" >}}
