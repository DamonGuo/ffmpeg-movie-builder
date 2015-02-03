#!/usr/bin/env python

import sys, os
import argparse
import subprocess

def generateImage(string, output_file, size="1024x768"):
    subprocess.check_call(["convert", "-size", size, 
                           "xc:black",
                           "-pointsize", "60",
                           "-fill", "white",
                           "-gravity", "center",
                           "-draw", ("text 0, 0 '%s'" % string).replace("\\n", """
"""),
                           output_file])

def main():
    if len(sys.argv) != 3:
        raise Exception("You need to specify string and output file")
    generateImage(sys.argv[1], sys.argv[2])
    

if __name__ == "__main__":
   main()
   

