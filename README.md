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

Full documentation available at https://rmrector.github.io/script.artwork.beef/.

### Current gotchas

- Music library support is for Kodi 18 Leia only, and requires a recent nightly from 2018
- It doesn't add animated artwork, yet
- It's not in the official Kodi repo, yet
- It cannot set artwork for "all seasons". [related trac ticket](https://trac.kodi.tv/ticket/16139)

### Thoughts

- Scrapers and NFO files need to set web service IDs like IMDB number, TVDB ID, or TMDB ID
  for media types that Kodi supports such IDs for: movies, TV shows, and episodes
  - Music files need to be tagged with MusicBrainz IDs; Artist, Release Group, and Track IDs
- Movie thumbnails aren't added from external sources. There is no way to tell the difference between stills
  and press/marketing images from the web services, while thumbs should only include stills.
  Skins can try multiple fanart for a similar look. Generating more than one thumb from
  a video file is outside the scope of this add-on, but any provided by a media manager is added to the library.
  Plugins can also set these to the ListItem, if their source provides more than one thumbnail.
- It would be nice to have a Kodi built-in way for skins to feed multiple art to a `multiimage`,
  maybe something like `$INFO[ListItem.MultiArt(fanart)]` to pull all `fanart` and `fanart#` together.
  I have no idea how it could be implemented in Kodi, though.
