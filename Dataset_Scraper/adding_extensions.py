""" This module is for adding extension to all midi files in dataset since when i scraped the dataset it was scraped without extensions.

Running this module in the directory containing the dataset will add extensions to all the midi files.
"""
import os
root = os.getcwd()
for file in os.listdir('.'):
   if not os.path.isfile(file):
       continue

   head, tail = os.path.splitext(file)
   if not tail:
       src = os.path.join(root, file)
       dst = os.path.join(root, file + '.mid')

       if not os.path.exists(dst): # check if the file doesn't exist
           os.rename(src, dst)
