---
title: "NFO and image files"
date: 2017-12-28T22:45:58-07:00
weight: 3
---

## Artwork file naming conventions for the video library

Artwork Beef will pick up any properly named artwork files next to your video files. It has two
conventions for loading most artwork: `[media file name]-[art type].[ext]` for movies,
episodes, and music videos, and `[art type].[ext]` for TV shows and as a less specific alternative for
movies and music videos with their own directories. This generally matches Kodi's file naming conventions.

`[art type]` must be alphanumeric, lowercase, and no longer than 20 characters, but can
otherwise be freely named. They should exactly match the name that skins can use to access
them, and extra fanart are saved as `fanart1`, `fanart2`, and so on; the same goes for any
other art type you want to save more than one of, though it requires a skin to actually support
multiple in some way.

### Movies, episodes, and music videos

Artwork for `//MRHOOD/Movies/Movie Name (2017)/Base File Name.mkv` can generally be stored at
`//MRHOOD/Movies/Movie Name (2017)/Base File Name-[art type].[ext]`. Episode artwork is stored similarly,
the important part is that it's in the same directory and has the same base file name as the episode video.

A few specific examples are

- `... /Movie Name (2017)/Movie File Name-poster.jpg`
- `... /Movie Name (2017)/Movie File Name-fanart.jpg`
- `... /Movie Name (2017)/Movie File Name-fanart1.jpg`
- `... /Movie Name (2017)/Movie File Name-fanart2.jpg`
- `... /Movie Name (2017)/Movie File Name-fanart3.jpg`
- `... /Movie Name (2017)/Movie File Name-clearlogo.png`
- Artwork can also be pulled from an NFO file named
  - `... /Movie Name (2017)/Movie File Name.nfo`

If your movie or music video library is large, I suggest you keep each item in their own directory
for performance reasons. Artwork Beef doesn't work any differently if you keep them all in one directory,
but its processing will slow down just like Kodi's library update the more files that are packed together.

### TV shows and alternative for movies and music videos

TV shows have a directory associated with them rather than an individual file, so there is no
base file name to use. Artwork for `//MRHOOD/TVShows/TV Show 1/` can generally be stored at
`//MRHOOD/TVShows/TV Show 1/[art type].[ext]`. Movies and music videos stored in separate directories
can also use this style, though if both styles exist for one movie it will choose the other,
more specific, one -- handy for 3D or special editions that have their own artwork, if you keep them
in the same directory.

A few specific examples

- `... /TV Show 1/poster.jpg`
- `... /TV Show 1/fanart.jpg`
- `... /TV Show 1/fanart1.jpg`
- `... /TV Show 1/fanart2.jpg`
- `... /TV Show 1/fanart3.jpg`
- `... /TV Show 1/clearlogo.png`
- Artwork can also be pulled from an NFO file named
  - `... /TV Show 1/tvshow.nfo`
  - `... /Movie Name (2017)/movie.nfo`
  - `... /Music Artist - Track Title/musicvideo.nfo`

### Movie collection artwork

Movie collection artwork can be pulled from a central directory (configured in the add-on settings)
containing artwork named in a similar fashion to the second option above.
Movie collections generally don't have an individual file nor folder they can call their own,
so instead use the set's name as the directory name. Remove characters which are not
file system safe, like `:?"/\<>*|`, and make sure directories do not end with a space or period.
Artwork Beef will be more lenient in its matching to catch styles that other tools may use,
but those two simple rules should always steer true.

A few specific examples are

- `... /[central movie set info directory]/Movie Collection Name/poster.jpg`
- `... /[central movie set info directory]/Movie Collection Name/fanart.jpg`
- `... /[central movie set info directory]/Movie Collection Name/fanart1.jpg`
- `... /[central movie set info directory]/Movie Collection Name/clearlogo.png`
- an NFO file named
  - `... /[central movie set info directory]/Movie Collection Name/set.nfo`

### Legacy names

It will also pull in artwork files that match Artwork Downloader file names, in cases where
they are different than the art types used in Kodi; for instance, logo.png is added as clearlogo
and extrafanart are added as fanart#. Ditto Movie Set Artwork Automator, but only for its
default file names (logo.png to clearlogo, folder.jpg to thumb). This is controlled with an
add-on setting, enabled by default. It also supports other file paths that MSAA supported,
though I do not suggest you use them for a new setup.

## From NFO files

Artwork Beef will also add artwork specified in a standard Kodi NFO file next to your media. Add an
`art` element to the root element whose children are individual artwork tagged with the
exact artwork type and a URL to the image.

```xml
<?xml version="1.0" encoding="UTF-8" ?>
<tvshow> <!-- Or 'movie', 'episodedetails', 'set', 'musicvideo' -->
  <title>TV Show 1</title>
  <!-- ... -->
  <art>
    <!-- The tag is the exact artwork type, freely named (lowercase alphanumeric), and the content is the URL to the image -->
    <arttype>https://example.frank/artstuff/maidbilberry/1234.jpg</arttype>
    <banner>https://thetvdb.com/banners/graphical/110381-g5.jpg</banner>
    <characterart>https://assets.fanart.tv/fanart/tv/110381/characterart/archer-2009-514f89ade07a7.png</characterart>
    <characterart1>https://assets.fanart.tv/fanart/tv/110381/characterart/archer-2009-54a8d64278ea4.png</characterart1>
    <clearart>https://assets.fanart.tv/fanart/tv/110381/hdclearart/archer-2009-54053c1930642.png</clearart>
    <clearlogo>https://assets.fanart.tv/fanart/tv/110381/hdtvlogo/archer-2009-505429fee4b03.png</clearlogo>
    <fanart>https://thetvdb.com/banners/fanart/original/110381-23.jpg</fanart>
    <fanart1>https://thetvdb.com/banners/fanart/original/110381-22.jpg</fanart1>
    <fanart2>https://thetvdb.com/banners/fanart/original/110381-18.jpg</fanart2>
    <fanart3>https://thetvdb.com/banners/fanart/original/110381-20.jpg</fanart3>
    <fanart4>https://thetvdb.com/banners/fanart/original/110381-16.jpg</fanart4>
    <landscape>https://assets.fanart.tv/fanart/tv/110381/tvthumb/A_110381.jpg</landscape>
    <poster>https://thetvdb.com/banners/posters/110381-1.jpg</poster>
    <!-- 'season' elements only for 'tvshow' -->
    <season num="0"> <!-- 0 = Specials -->
      <!-- Also freely named -->
      <banner>https://thetvdb.com/banners/seasonswide/110381-0.jpg</banner>
      <landscape>https://assets.fanart.tv/fanart/tv/110381/seasonthumb/archer-2009-51484c7a15cb2.jpg</landscape>
      <poster>https://thetvdb.com/banners/seasons/110381-0-2.jpg</poster>
    </season>
    <season num="1"> <!-- Repeat for each season -->
      <banner>https://thetvdb.com/banners/seasonswide/110381-1.jpg</banner>
      <landscape>https://assets.fanart.tv/fanart/tv/110381/seasonthumb/archer-2009-51484c8624d76.jpg</landscape>
      <poster>https://thetvdb.com/banners/seasons/110381-1-3.jpg</poster>
    </season>
  </art>
</tvshow>
```

## Downloading artwork to share with multiple Kodi devices

Enable the option "Download all processed artwork to file system" and
Artwork Beef will download all artwork for each item processed automatically, and any images
selected manually. Images will be saved next to the media files with the most specific
file names detailed above.
