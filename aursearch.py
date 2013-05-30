#!/usr/bin/env python
"""
This script searches the Arch Linux AUR for the provided package names and prints out all results returned

Author: Matthew Raspberry
Email: nixalot[at]nixalot[dot]com

Copyright 2013 Matthew Raspberry

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import tarfile
import tempfile
import argparse
from threading import Thread,Lock
from queue import Queue

try:
    import requests
except ImportError:
    print("This script requires the requests library (http://docs.python-requests.org/en/latest/)",file=sys.stderr)
    sys.exit()

__version__='1.0'

global aurbase # just want to be clear what the intention is by declaring these here
global lock
aurbase = 'https://aur.archlinux.org'
lock = Lock()


def worker(workqueue):
    while True:
        pkgname = workqueue.get()
        url = aurbase + '/rpc.php'
        urlparams = {'type' : 'search',
                     'arg' : pkgname,
                    }
        results = requests.get(url,params=urlparams,verify=True)
        if results.json()['type'] == 'error':
            lock.acquire() # acquire the lock so we're the only ones printing
            print("No results found for",pkgname)
            lock.release()
        else:
            process_results(results,pkgname)

        workqueue.task_done()

def process_results(resultobj,pkgname):
    json = resultobj.json()
    lock.acquire()
    print("Found",json['resultcount'],"results for",pkgname)
    for res in json['results']:
        print("    Name:",res['Name'])
        print("    Version:",res['Version'])
        print("    Maintainer:",res['Maintainer'])
        print("    ID:", res['ID'])
        print("    Out of Date:",res['OutOfDate'])
        print("    License:",res['License'])
        print("    URL:",aurbase + res['URLPath'])
        print("    Description:",res['Description'])
    lock.release()

def main(args):
    threadnum = args.threads
    if threadnum < 1:
        threadnum = 1 # set the number of threads to 1 if it's less than 1


    workqueue = Queue()
    for i in range(threadnum):
        wkr = Thread(target=worker,args=[workqueue])
        wkr.daemon = True
        wkr.start()

    for pkgname in args.packages:
        workqueue.put(pkgname)

    workqueue.join() # wait for everything to finish
    sys.exit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="This program searches for packages on the Arch Linux AUR and prints out all the results it finds matching the specified package name")
    parser.add_argument('packages',metavar='packages',nargs='+',help="Package name to search for on the AUR")
    parser.add_argument('-t','--threads',type=int,default=1,help="Number of threads to use (default: 1)")
    parser.add_argument('-v','--version',action='version',version='%(prog)s 1.0')
    args = parser.parse_args()
    main(args)
