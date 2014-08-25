ffmpeg-movie-builder
====================

This is a python script to generate a movie from title strings and
movies. The script just concatenates the movies in time series and
insert titles.

[sample movie](https://www.youtube.com/watch?v=mb-1J2-_iYc&feature=youtu.be)



How to use
----------

### command line
```sh
$ ffmpeg_movie_builder.py -c hello -c world -m foo.mp4 -c "next movie" -m bar.mp4 output.mp4
```

### use configuration file
```sh
$ ffmpeg_movie_builder.py --config sample.yaml output.mp4
```
