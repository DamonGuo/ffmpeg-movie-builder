#!/usr/bin/env python
import subprocess
import os, sys
import tempfile

def getcolor(colorname):
    colors = {
        'clear': '\033[0m',
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'purple': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m'
        }
    def func2(c):
        return colors[colorname] + c + colors['clear']

    return func2

black  = getcolor('black')
red    = getcolor('red')
green  = getcolor('green')
yellow = getcolor('yellow')
blue   = getcolor('blue')
purple = getcolor('purple')
cyan   = getcolor('cyan')
white  = getcolor('white')

class Task():
  def run(self):
    pass
  def exec_command(self, commands):
    subprocess.check_call(commands)

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
    print green("generating image from text: %s -> %s" %(self.text, self.output))
    self.exec_command(command)

class MovieConvertTask(Task):
  def __init__(self, input):
    self.input = input
    self.output = tempfile.mktemp(".mp4")
  def run(self):
    command = ["ffmpeg", "-loglevel", "quiet",
               "-i", self.input,
               "-q:a", "1",
               "-q:v", "1",
               "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
               self.output]
    print green("converting movie to mp4: %s -> %s" % (self.input, self.output))
    self.exec_command(command)
    
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
    command2 = ["ffmpeg",
                "-loglevel", "quiet",
                "-r", str(1.0 / self.duration),
                "-i", self.output_prefix + "_%d.png",
                self.output]
    print green("copying image: %s -> %s" % (self.input, self.mid_image0))
    self.exec_command(command0)
    print green("copying image: %s -> %s" % (self.input, self.mid_image1))
    self.exec_command(command1)
    print green("generating movie from two images: (%s, %s) -> %s"
                % (self.mid_image0, self.mid_image1, self.output))
    self.exec_command(command2)
    
def usage():
  print "ffmpeg_builder.py [-m|c|i] arg0 [-m|c|i] arg1 ... output"

def main():
  argv = sys.argv[1:]
  # parse argv in the order
  movie_files = []
  image_generate_tasks = []               #string -> image
  movie_generate_tasks = []               #image -> movie
  movie_convert_tasks = []
  while True:
    if len(argv) == 1:
      # output
      output = argv[0]
      break
    else:
      option = argv[0]
      option_arg = argv[1]
      if option == "-m":
        movie_convert_tasks.append(MovieConvertTask(option_arg))
        movie_files.append(movie_convert_tasks[-1].output)
      elif option == "-c":
        image_generate_tasks.append(ImageGenerateTask("hello world"))
        movie_generate_tasks.append(MovieGenerateTask(
          image_generate_tasks[-1].output))
        movie_files.append(movie_generate_tasks[-1].output)
      elif option == "-i":
        movie_generate_tasks.append(MovieGenerateTask(option_arg))
        movie_files.append(movie_generate_tasks[-1].output)
      argv = argv[2:]
  for i in image_generate_tasks:
    i.run()
  for i in movie_generate_tasks:
    i.run()
  for i in movie_convert_tasks:
    i.run()
  command = ["mmcat"] + movie_files + [output]
  print " ".join(command)
  # subprocess.check_call(command)
if __name__ == "__main__":
  main()
