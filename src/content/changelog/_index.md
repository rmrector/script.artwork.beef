---
title: "Changelog"
date: 2017-12-27T22:44:34-07:00
weight: 100
---

{{< version "0.15.1" "2018-01-11" >}}

- {{< changelog fix >}} incorrect names for all artwork when 'extrafanart' enabled
- {{< changelog fix >}} missing artwork identification when files are moved

{{< version "0.15.0" "2018-01-09" >}}

- {{< changelog feature >}} add option to save additional fanart to 'extrafanart' directory
  rather than matching Kodi export names
- {{< changelog feature >}} remove deselected local artwork, add option to recycle changed local artwork
- {{< changelog fix >}} limit songs when processing single album/artist

{{< version "0.14.0" "2018-01-02" >}}

- {{< changelog feature >}} music library support (for latest Leia nightlies only)
- {{< changelog fix >}} crash when processing music video without an artist
- {{< changelog fix >}} don't create movie set central directory unless there is artwork to download
- {{< changelog fix >}} crash on Jarvis when building UA

{{< version "0.13.0" "2017-12-27" >}}

- {{< changelog feature >}} add option to download artwork
- {{< changelog feature >}} add options to change the in progress display
- {{< changelog fix >}} don't automatically add fanart for old items from web services if they have
  any local fanart to avoid adding duplicates
- {{< changelog fix >}} set music video 'discart' rather than 'cdart'

{{< version "0.12.4" "2017-12-05" >}}

- {{< changelog feature >}} 'clearart' for music videos (from artist)
- {{< changelog fix >}} warn instead of error when music video IDs not found

{{< version "0.12.3" "2017-11-14" >}}

- {{< changelog fix >}} Properly check before removing missing local artwork
- {{< changelog fix >}} tweak final notification

{{< version "0.12.2" "2017-11-09" >}}

- {{< changelog feature >}} add French translation
- {{< changelog fix >}} missing IDs in Jarvis and lower
- {{< changelog fix >}} don't notify over video, add final count message to progress dialog

{{< version "0.12.1" "2017-11-04" >}}

- {{< changelog fix >}} mismatched IDs for movie sets and music videos

{{< version "0.12.0" "2017-11-03" >}}

- {{< changelog feature >}} grab music video artwork from TheAudioDB and fanart.tv
- {{< changelog feature >}} support multiple uniqueids as expanded in Krypton, support TheMovieDB TV scraper in particular
- {{< changelog feature >}} show latest artwork report in Kodi from the add-on settings
- {{< changelog feature >}} add option to prefer artwork from The Movie DB when available
- {{< changelog fix >}} clean file system unsafe characters when matching local set artwork
- {{< changelog fix >}} more localized strings, including notifications and the artwork report
- {{< changelog fix >}} another Leia compatibility fix, localized string formatting changes
- {{< changelog cleanup >}} simplify web service request retries and session management

{{< version "0.11.1" "2017-09-05" >}}

- {{< changelog fix >}} reporting error for new users

{{< version "0.11.0" "2017-09-02" >}}

- {{< changelog feature >}} use HTTPS for all API and image URLs
- {{< changelog feature >}} generate a report of all changed artwork
- {{< changelog feature >}} add option to override image language (defaults to Kodi interface language)
- {{< changelog feature >}} add option to prefer posters without a title
- {{< changelog feature >}} add option to generate thumbnail from video files
- {{< changelog feature >}} add option to remove all artwork for specific types of media
- {{< changelog feature >}} add temporary action to reset all movie set IDs
- {{< changelog fix >}} a few Leia compatibility changes
- {{< changelog fix >}} reset items' processed status when the Kodi library is rebuilt
- {{< changelog cleanup >}} rearrange some Advanced add-on settings

{{< version "0.10.2" "2017-07-25" >}}

- {{< changelog fix >}} don't repeatedly request artwork from an unavailable web service
- {{< changelog fix >}} don't remove animated artwork set by other add-ons
- {{< changelog fix >}} always allow movie sets to be re-matched from TMDB

{{< version "0.10.1" "2017-05-12" >}}

- Fix removing auto-created thumbnails
- Don't crash on ConnectionError with web providers, but warn
- Fix error when removing specific or all not-configured artwork from all seasons
- Fix error with unicode characters from NFO file
- Convert JSON results from providers to UTF-8 encoded bytestrings `str`

{{< version "0.10.0" "2017-04-21" >}}

- Automatically find new artwork for old items only once per day
  - Plus option to disable automatic updates for old items altogether
- Remove movie thumbnail Kodi automatically creates if your scraper is not configured to add a poster
- Remove explicit action "clean URLs", this happens automatically as items are processed
- Add manual action to remove all artwork of a specific type

{{< version "0.9.1" "2017-02-11" >}}

- Fix setting season artwork

{{< version "0.9.0" "2017-01-27" >}}

- Support movie set artwork
- Merge context items into main add-on
- Rearrange libs, drop last dependency not available in official Kodi repo
- Spread out checking for new artwork so they don't happen all at once (after the first run)
- Fix error when displaying non-ASCII characters in GUI
- Improve error handling for certain HTTP 5xx errors from fanart.tv
- Reduce TheMovieDB image rating sort adjustment
- Adjust TVDB image rating sort, so that an image with one rating of 10 doesn't end up at the top
- Move code from resources/lib to lib

{{< version "0.8.2" "2016-12-01" >}}

- Fix manually selecting new fanart

{{< version "0.8.1" "2016-11-23" >}}

- Fix silly bug in 0.8.0

{{< version "0.8.0" "2016-11-21" >}}

- Add season fanart from fanart.tv
- Add button to remove extra artwork not enabled in add-on settings
- Cleanup and avoid errors when adding artwork from files
- Check existing URLs for problems
- Retry failed items in at most 2 days not 2 months
- Prefer English over other non-matching languages on non-English systems
- Ignore some false alarm updates from Kodi that aren't new items
- Other bug fixes

{{< version "0.7.0" "2016-10-03" >}}

- Clean up series and artwork selection GUIs for Kodi 17 Krypton
- Drop extra dependencies CacheControl and lockfile, use common plugin cache
- Make more requests of TheTVDB to grab more fanart
- Fix non-working season landscape images (encode URLs from fanart.tv)
 - Includes a button to fix existing URLs manually

 {{< version "0.6.4" "2016-09-18" >}}

- Fix error in series selection for episode artwork

{{< version "0.6.3" "2016-09-13" >}}

- Identify artwork with AD filenames
- Run full automatic process more often if filesystem only
- Add option to set minimum rating for auto processing
- Remove local artwork from library if file no longer exists
- Fix series banner sort
- Fix a few possible errors

{{< version "0.6.2" "2016-09-08" >}}

- Fix persistent error after saved JSON is corrupted
- Improve list processing speed if web services aren't accessed
- Reduce load on web services during automatic processing
- Use proper paths for local file artwork
- Fix datetime errors

{{< version "0.6.1" "2016-07-22" >}}

- Fix error when grabbing images from TheTVDB

{{< version "0.6.0" "2016-07-08" >}}

- Add setting to enter a fanart.tv personal API key
- Use production API for TheTVDB API v2, rather than beta
- Load artwork from filesystem for stacked movies and VIDEO_TS/BDMV rips
- Localize messages

{{< version "0.5.0" "2016-03-04" >}}

- Add artwork from NFO and image files
- Add option to prefer fanart with no title
- Multiple characterart can be selected
- Better web service handling

{{< version "0.4.0" "2016-02-15" >}}

- Fix persistent notification being too persistent
- Add settings to select artwork types to automatically download
- Sort and limit posters by height, not width

{{< version "0.3.2" "2016-02-09" >}}

- better handle rapid fire library updates
- Use persistent notification for progress
- Fix up new season detection
- Use TheTVDB id for settings

{{< version "0.3.1" "2016-02-06" >}}

- Python 2.6 support
- Fix preview image for Isengard
- Fix caching on Android

{{< version "0.3.0" "2016-02-04" >}}

- Watch for library updates and automatically add artwork for new items
- Add series, season, and movie artwork from fanart.tv to the library
- Add series and season artwork from TheTVDB
- Add movie and episode (fanart/stills) artwork from The Movie Database
- Select specific artwork for individual media items
- Add all missing artwork for a single item, all items, or new items added since last run
