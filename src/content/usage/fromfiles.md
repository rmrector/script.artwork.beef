---
title: "Image files"
date: 2017-12-28T22:45:58-07:00
weight: 20
---

## Downloading and managing local artwork files

By default, Artwork Beef does not modify existing local artwork files. There are some options
to change that, though. With the settings "Download these artwork types to the local file system"
you can configure exactly which types of artwork to download for each media type.
By default most video library images will be saved next to the media files
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

Artwork Beef will pick up artwork files next to your video files if they match the
configured art types in add-on settings. It has two
conventions for loading most artwork: `[media base file name]-[art type].[ext]` for movies,
episodes, and music videos, and `[art type].[ext]` for TV shows and as a less specific alternative for
movies and music videos within their own directories. This generally matches Kodi's file naming conventions.

`[art type]` must be alphanumeric and lowercase, but can
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
- `... /TV Show 1/season-specials-poster.png`
- `... /TV Show 1/season-specials-landscape.png`
- `... /TV Show 1/season01-poster.png`
- `... /TV Show 1/season01-landscape.png`

### Movie collection artwork

Movie collection artwork can be pulled from a central directory (configured in the add-on settings)
containing artwork named in a similar fashion to both options above.
Movie collections may not have a folder they can call their own,
so instead use the set's name as the directory name.

A few specific examples are

- `... /[central movie set info directory]/Movie Collection Name-poster.jpg`
- `... /[central movie set info directory]/Movie Collection Name-fanart.jpg`
- `... /[central movie set info directory]/Movie Collection Name-fanart1.jpg`
- `... /[central movie set info directory]/Movie Collection Name-clearlogo.png`

or

- `... /[central movie set info directory]/Movie Collection Name/poster.jpg`
- `... /[central movie set info directory]/Movie Collection Name/fanart.jpg`
- `... /[central movie set info directory]/Movie Collection Name/fanart1.jpg`
- `... /[central movie set info directory]/Movie Collection Name/clearlogo.png`

Artwork Beef can also be configured to pull collection artwork from a parent directory of movies,
if that directory name exactly matches the cleaned collection name, with artwork
named `[art type].[ext]`.

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
for disc 2, and so on. Multiple disc albums can also have their songs and discart stored in disc specific
subfolders, but other artwork can stay in the top album folder.

Artwork Beef will also identify album and song artwork next to the song files if all songs for
one album are in a single folder, and don't share that folder with songs from any other album.
Song artwork organized this way must match the base name of the song file, rather than just the
song name as when in the artist folder. There is also an option to save album and song artwork
to this directory if possible.

**Note:** Albums nested inside of artist folders in the _central directory_ may not be the best
idea for the future, but that's what Artwork Beef does for now.

### Central directory folder naming

When artwork is in the central directory (for music and movie sets), the folder name must exactly
match the name in the library, including look-alike characters such as hyphen and
[hyphen-minus](https://en.wikipedia.org/wiki/Hyphen#Hyphen-minus).

### File system safe names

For music and movie set artwork, the file name is made from the title or name of items, which
may not be safe for the file system with characters like `:?"/\<>*|`. Replace these characters
with an underscore '_', and remove spaces and periods from the end to match Kodi's file name cleaning.
Artwork Beef will be more lenient in its matching to catch other styles.

### Legacy file names

Artwork Beef will also identify several other filenames that are / have been used by other tools,
such as Artwork Downloader and Movie Set Artwork Automator,
in cases when they are different than the art type name skins use to access them.

`logo.png` is added as clearlogo, `character.png` is added as characterart, `folder.jpg` to thumb,
`disc.png` and `cdart.png` to discart, files in the extrafanart directory are added as fanart#,
and files in the extrathumbs directory are added as thumb#.

### An option to rename artwork files

If you have a Linux computer with Perl installed, here is a collection of commands to rename
some artwork files from Artwork Downloader to Kodi file names. Moving extrafanart and extrathumbs
is a bit more work. Only do this if all of your media management tools support the new names,
Artwork Beef will support both for some time yet. These commands are just "dry runs" that will
print out what the rename _would_ do, remove the `-n` option from each line to actually rename the files.

```sh
# For movies and TV shows
find /path/to/media/ \( -iname "logo.png" -o -iname "*-logo.png" \) -exec rename -n 's/logo.png$/clearlogo.png/i' '{}' \;
find /path/to/media/ \( -iname "disc.png" -o -iname "*-disc.png" \) -exec rename -n 's/disc.png$/discart.png/i' '{}' \;
find /path/to/media/ \( -iname "character.png" -o -iname "*-character.png" \) -exec rename -n 's/character.png$/characterart.png/i' '{}' \;

# Music videos and the music library
find /path/to/media/ \( -iname "cdart.png" -o -iname "*-cdart.png" \) -exec rename -n 's/cdart.png$/discart.png/i' '{}' \;
```
