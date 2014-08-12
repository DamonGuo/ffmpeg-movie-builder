#!/usr/bin/env python

__doc__ = """
a script to generate and concatenate movies with titles.
"""
from compiler.ast import flatten
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

def queryYesNo(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


try:
    import yaml
except:
    print red("if you want to read configs from yaml file, please install pyyaml")

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
               size,
               background,
               font,
               foreground,
               pointsize):
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
    if ffmpeg_quiet:
      command.append("-loglevel")
      command.append("quiet")
    print green("converting movie to mpg: %s -> %s" % (self.input, self.output))
    self.exec_command(command)
    
class MovieGenerateTask(Task):
  """
  a task to generate a movie from an image.
  """
  def __init__(self, input, duration):
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
    if ffmpeg_quiet:
      command2.append("-loglevel")
      command2.append("quiet")
    print green("generating movie from images: -> %s"
                % (self.output))
    self.exec_command(command2)


    
class Config():
  """
  config looks like
  - type: movie
    input: foo.mp4
  - type: string
    string: "foo"
  - type: image
    input: foo.png
  """
  def __init__(self, config_type, args):
    self.config_type = config_type
    self.args = args
  def getParamValue(self, name, default):
    if self.args.has_key(name):
      return self.args[name]
    else:
      return default
  def generateTasks(self):
    if self.config_type == "movie":
      return [MovieConvertTask(os.path.expanduser(self.args["input"]))]
    elif self.config_type == "string":
      image_task = ImageGenerateTask(self.args["string"],
                                     self.getParamValue("size", "1024x768"),
                                     self.getParamValue("background", "black"),
                                     self.getParamValue("font", "Dejavu-Sans-Book"),
                                     self.getParamValue("foreground", "white"),
                                     self.getParamValue("pointsize", "30"))
      movie_task = MovieGenerateTask(image_task.output,
                                     self.getParamValue("duration", 4.0))
      return [image_task, movie_task]
    elif self.config_type == "image":
      movie_task = MovieGenerateTask(os.path.expanduser(self.args["input"]))
      return [movie_task]
    else:
      err_message = "unknown config_type: %s" % (self.config_type)
      print red(err_message)
      raise Exception(err_message)

def usage():
  print "ffmpeg_movie_builder.py [options] [-m|c|i] arg0 [-m|c|i] arg1 ... output"
  print "  or"
  print "ffmpeg_movie_builder.py [options] --config config.yml output"

def runWrap(obj):
  """
  a function to wrap Task.run method to call from
  Pool.map
  """
  return obj.run()

def loadYaml(yaml_file):
  if os.path.exists(yaml_file):
    return yaml.load(open(yaml_file))
  else:
    message = "failed to find %s" % (yaml_file)
    print red(message)
    raise Exception(message)

def main():
  global ffmpeg_quiet
  argv = sys.argv[1:]
  # parse argv in the order
  movie_files = []
  image_generate_tasks = []               #string -> image
  movie_generate_tasks = []               #image -> movie
  movie_convert_tasks = []
  # check args
  if len(argv) <= 1 or "-h" in argv or "--help" in argv:
    usage()
    sys.exit(1)
  else:                                   #process global config
    if "--ffmpeg-quiet" in argv:
      ffmpeg_quiet = True
      argv.remove("--ffmpeg-quiet")
    else:
      ffmpeg_quiet = False
    if "-y" in argv:
      force_to_yes = True
      argv.remove("-y")
    elif  "--yes" in argv:
      force_to_yes = True
      argv.remove("--yes")
    else:
      force_to_yes = False
  if argv[0] == "--config":                        #read from config
    params = loadYaml(argv[1])
    output = argv[2]
  else:                                       # read from command line
    params = []
    while True:
      if len(argv) == 1:
        # output
        output = argv[0]
        break
      else:
        option = argv[0]
        option_arg = argv[1]
        if option == "-m":
          params.append({"type": "movie", "input": option_arg})
        elif option == "-i":
          params.append({"type": "image", "input": option_arg})
        elif option == "-c":
          params.append({"type": "string", "string": option_arg})
        argv = argv[2:]
  configs = [Config(p["type"], p) for p in params]
  tasks = flatten([c.generateTasks() for c in configs])
  movie_convert_tasks = [t for t in tasks if isinstance(t, MovieConvertTask)]
  image_generate_tasks = [t for t in tasks if isinstance(t, ImageGenerateTask)]
  movie_generate_tasks = [t for t in tasks if isinstance(t, MovieGenerateTask)]
  movie_files = [t.output for t in tasks]
  [t.run() for t in image_generate_tasks]
  [t.run() for t in movie_generate_tasks]
  [t.run() for t in movie_convert_tasks]
  if os.path.exists(output):
    if force_to_yes or queryYesNo("remove %s?" % (output)):
      os.remove(output)
  command = "cat %s | ffmpeg -f mpeg -i - -sameq -vcodec mpeg4 %s" % (" ".join(movie_files), output)
  if ffmpeg_quiet:
    command = command + " -loglevel quiet"
  subprocess.check_call(["sh", "-c", command])
  print green("done, check out %s" % (output))
if __name__ == "__main__":
  main()
