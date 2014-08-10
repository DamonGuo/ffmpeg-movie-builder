#!/usr/bin/env python

__doc__ = """
a script to generate and concatenate movies with titles.
"""

from multiprocessing import Pool
import argparse
import subprocess
import os, sys
import tempfile

###########################################################
# utility function to colorize terminal output
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
############################################################

def generateParser():
  parser = argparse.ArgumentParser(
    "a script to generate and concatenate movies with titles")
  return parser
  

class Task():
  def run(self):
    pass
  def exec_command(self, commands):
    print cyan("[%s]" % " ".join(commands))
    subprocess.check_call(commands)

class ImageGenerateTask(Task):
  """
  Generate an image from caption string
  """
  def __init__(self, text, 
               size="1024x768",
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
  """
  a task to convert movie to mpeg1 movie
  """
  def __init__(self, input):
    self.input = input
    self.output = tempfile.mktemp(".mpg")
  def run(self):
    command = ["ffmpeg",
               "-i", self.input,
               "-sameq",
               # "-q:a", "1",
               # "-q:v", "1",
               "-r", "30",
               "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
               self.output]
    print green("converting movie to mpg: %s -> %s" % (self.input, self.output))
    self.exec_command(command)
    
class MovieGenerateTask(Task):
  """
  a task to generate a movie from an image.
  """
  def __init__(self, input, duration = 4.0):
    self.output_prefix = tempfile.mktemp()
    self.input = input
    # png...?
    self.mid_images = [self.output_prefix + ("_%d.png" % (i)) 
                       for i in range(int(duration * 30))]
    self.output = self.output_prefix + ".mpg"
    self.duration = duration
  def run(self):
    for mid_image in self.mid_images:
      command = ["convert", self.input,
                 "-quality", "0",
                 mid_image]
      print green("copying image: %s -> %s" % (self.input, mid_image))
      self.exec_command(command)
    command2 = ["ffmpeg",
                "-r", "30",
                "-i", self.output_prefix + "_%d.png",
                "-sameq",
                self.output]
    print green("generating movie from images: -> %s"
                % (self.output))
    self.exec_command(command2)
    
def usage():
  print "ffmpeg_builder.py [-m|c|i] arg0 [-m|c|i] arg1 ... output"

def runWrap(obj):
  """
  a function to wrap Task.run method to call from
  Pool.map
  """
  return obj.run()

  
def main():
  argv = sys.argv[1:]
  # parse argv in the order
  movie_files = []
  image_generate_tasks = []               #string -> image
  movie_generate_tasks = []               #image -> movie
  movie_convert_tasks = []
  # check args
  if len(argv) <= 1 or len(argv) % 2 == 0 or "-h" in argv or "--help" in argv:
    usage()
    sys.exit(1)
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
        image_generate_tasks.append(ImageGenerateTask(option_arg))
        movie_generate_tasks.append(MovieGenerateTask(
          image_generate_tasks[-1].output))
        movie_files.append(movie_generate_tasks[-1].output)
      elif option == "-i":
        movie_generate_tasks.append(MovieGenerateTask(option_arg))
        movie_files.append(movie_generate_tasks[-1].output)
      argv = argv[2:]
  pool = Pool(8)
  pool.map(runWrap, image_generate_tasks)
  pool.map(runWrap, movie_generate_tasks)
  pool.map(runWrap, movie_convert_tasks)
  if os.path.exists(output):
    os.remove(output)
  command = "cat %s | ffmpeg -f mpeg -i - -sameq -vcodec mpeg4 %s" % (" ".join(movie_files), output)
  subprocess.check_call(["sh", "-c", command])
  
if __name__ == "__main__":
  main()
