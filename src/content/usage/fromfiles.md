---
title: "Image files"
date: 2017-12-28T22:45:58-07:00
weight: 3
---

## Downloading and managing local artwork files

By default, Artwork Beef does not modify existing local artwork files. There are some options
to change that, though. With the settings "Download artwork for processed [media type]"
enabled for a media type it will download all remote artwork for processed items, and any new images
selected manually. By default most video library images will be saved next to the media files
with the most specific file names detailed below, with options to save movie and music video artwork
without the base file name if you like, and options to save movie and music video fanart# to an
"extrafanart" directory for skins using the classic style.

- The add-on setting "Delete deselected artwork files" will delete existing "fanart" files that are
  deselected manually in the GUI, to prevent that artwork file from being added back to the library
  when the media item is next processed.
- The add-on setting "Recycle deleted and replaced files to temp/cache directory" will move
  deleted and replaced artwork to Kodi's temp or cache directory. This is fairly simple and
  does not check the available space on the drive, and can overwrite the first recycled file
  if the same art type is modified again.

## Artwork file naming conventions for the video library

Artwork Beef will pick up any properly named artwork files next to your video files. It has two
conventions for loading most artwork: `[media base file name]-[art type].[ext]` for movies,
episodes, and music videos, and `[art type].[ext]` for TV shows and as a less specific alternative for
movies and music videos within their own directories. This generally matches Kodi's file naming conventions.

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

### Movie collection artwork

Movie collection artwork can be pulled from a central directory (configured in the add-on settings)
containing artwork named in a similar fashion to the second option above.
Movie collections generally don't have an individual file nor folder they can call their own,
so instead use the set's name as the directory name.

A few specific examples are

- `... /[central movie set info directory]/Movie Collection Name/poster.jpg`
- `... /[central movie set info directory]/Movie Collection Name/fanart.jpg`
- `... /[central movie set info directory]/Movie Collection Name/fanart1.jpg`
- `... /[central movie set info directory]/Movie Collection Name/clearlogo.png`

### Music artwork

Music artwork is gathered from and downloaded to the "Artist information folder" setting in Kodi,
added in 18 Leia under "Media settings", "Music", "Library". The results are structured as

- `... /[Artist information folder]/[artist name]/thumb.jpg`
- `... /[Artist information folder]/[artist name]/fanart.jpg`
- `... /[Artist information folder]/[artist name]/fanart1.jpg`
- `... /[Artist information folder]/[artist name]/clearlogo.png` for artist artwork
- `... /[Artist information folder]/[artist name]/[album name]/thumb.jpg`
- `... /[Artist information folder]/[artist name]/[album name]/back.jpg`
- `... /[Artist information folder]/[artist name]/[album name]/spine.jpg`
- `... /[Artist information folder]/[artist name]/[album name]/discart.png` for album artwork
- `... /[Artist information folder]/[artist name]/[album name]/[song name]-thumb.jpg` for song artwork

When there is more than one artist with the same name, the first four characters of the
artist MusicBrainz ID is add to the end of the folder like `[artist name]_12fe`. Same goes
when there is more than one album with the same name for a single artist (like remasters or
other recordings), with the album / release MusicBrainz ID (not release group).

For albums with multiple discs, you can add disc artwork as 'discart1.png' for disc 1, 'discart2.png'
for disc 2, and so on. You may still want to keep a 'discart.png' image, though. Skins still
need to do a bit of magic to line these up with selected songs and discart is an easy fallback.

Artwork Beef will also identify album and song artwork next to the song files if all songs for
one album are in a single folder, and don't share that folder with songs from any other album.
Song artwork organized this way must match the base name of the song file, rather than just the
song name as when in the artist folder. There is also an option to save album and song artwork
to this directory if possible.

### File system safe names
For music and movie set artwork, the file name is made from the title or name of items, which
may not be safe for the file system with characters like `:?"/\<>*|`. Replace these characters
with an underscore '_', and make sure file names do not end with a space or period.
Artwork Beef will be more lenient in its matching to catch other styles,
but those two simple rules should steer true.

### Legacy names

It will also pull in artwork files that match Artwork Downloader file names, in cases where
they are different than the art types used in Kodi; for instance, logo.png is added as clearlogo
and extrafanart are added as fanart#. Ditto Movie Set Artwork Automator, but only for its
default file names (logo.png to clearlogo, folder.jpg to thumb). This is controlled with an
add-on setting, enabled by default. It also supports other file paths that MSAA supported,
though I do not suggest you use them for a new setup.
