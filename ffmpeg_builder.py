#!/usr/bin/env python
import subprocess
import os, sys
import tempfile
class Task():
  def run(self):
    pass

class ImageGenerateTask(Task):
  def __init__(self, text, 
               size="640x480",
               background="black",
               font="Dejavu-Sans-Book",
               foreground="white",
               pointsize="30"):
    self.output = tempfile.mktemp(".png")
    self.text = text
    self.size = size
    self.background = background
    self.font = font
    self.foreground = foreground
    self.pointsize = pointsize
  def run(self):
    command = ["convert",
               "-size", self.size,
               "xc:" + self.background,
               "-font", self.font,
               "-pointsize", self.pointsize,
               "-fill", self.foreground,
               "-gravity", "center",
               "-draw", "text 0, 0 '%s'" % (self.text),
               self.output]
    subprocess.check_call(command)

class MovieGenerateTask(Task):
  def __init__(self, input, duration = 4.0):
    self.output_prefix = tempfile.mktemp()
    self.input = input
    # png...?
    self.mid_image0 = self.output_prefix + "_0.png"
    self.mid_image1 = self.output_prefix + "_1.png"
    self.output = self.output_prefix + ".mp4"
    self.duration = duration
  def run(self):
    command0 = ["convert", self.input,
                "-quality", "0",
                self.mid_image0]
    command1 = ["convert", self.input,
                "-quality", "0",
                self.mid_image1]
    command2 = ["ffmpeg", "-r", str(1.0 / self.duration),
                "-i", self.output_prefix + "_%d.png",
                self.output]
    subprocess.check_call(command0)
    subprocess.check_call(command1)
    subprocess.check_call(command2)
               
    
def usage():
  print "ffmpeg_builder.py [-m|c|i] arg0 [-m|c|i] arg1 ... output"

def main():
  argv = sys.argv[1:]
  # parse argv in the order
  movie_files = []
  image_generate_tasks = []               #string -> image
  movie_generate_tasks = []               #image -> movie
  while True:
    if len(argv) == 1:
      # output
      print "writing to ", argv[0]
      output = argv[0]
      break
    else:
      option = argv[0]
      option_arg = argv[1]
      if option == "-m":
        print "use ", option_arg, " as movie"
        movie_files.append(option_arg)
      elif option == "-c":
        print "generate caption from string", option_arg
        image_generate_tasks.append(ImageGenerateTask("hello world"))
        movie_generate_tasks.append(MovieGenerateTask(
          image_generate_tasks[-1].output))
        movie_files.append(movie_generate_tasks[-1].output)
      elif option == "-i":
        print "use the image as caption: ", option_arg
        movie_generate_tasks.append(MovieGenerateTask(option_arg))
        movie_files.append(movie_generate_tasks[-1].output)
      argv = argv[2:]
  for i in image_generate_tasks:
    i.run()
  for i in movie_generate_tasks:
    i.run()
  command = ["mmcat"] + movie_files + [output]
  print " ".join(command)
  subprocess.check_call(command)
if __name__ == "__main__":
  main()
