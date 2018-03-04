"""
Listener.py

Main application for FocusFriend, created for RevolutionUC 2018 hackathon.

Requires OSC broadcast from Muse Headband (2014 version) 
through either Muse Direct (Windows) or muse-io CLI (MacOS, Linux).
"""

import argparse
import math

from pythonosc import dispatcher
from pythonosc import osc_server

# Required for FFT
import numpy as np
from numpy import *

# Graphical output of program
from graphics import *

# Required to do GUI at the same time as input processing
import threading
import time

# Display window
win = None

# Display bar with focus value
bar = None

# Constants
past500samples = [0 for _ in range(501)]     # Updated every time we get a new value
concentrationLevel = 0

# Event listener for new EEG data from Muse
def eeg_handler(unused_addr, args, ch1, ch2, ch3, ch4):
   # This caused lots of frustration.
   global concentrationLevel
   global past500samples

   # Remove first element, add current EEG value to end of list
   past500samples.pop(1)
   past500samples.append(ch1)

   # Stored as first value of array. Will not refactor.
   samplesThisBatch = past500samples[0]

   samplesThisBatch += 1

   #print(samplesThisBatch)

   if samplesThisBatch == 50:
       samplesThisBatch = 0

       # Convert to numPy array
       reals = np.array(past500samples[1:])
       
       fftResult = [abs(x) for x in np.fft.rfft(reals)]    # abs to get rid of complex nums

       concentrationLevel = 0
       
       # We need the average of the gamma range (around 10-30 Hz ish)
       for i in range(10,30):
           concentrationLevel += fftResult[i]
       
       concentrationLevel /= 2000

   past500samples[0] = samplesThisBatch


args = None

# Hosts the listener. In OSC, apparently "Server" is the receiver and "Client" is the broadcaster :/
def server():
   global args

   _dispatcher = dispatcher.Dispatcher()
   _dispatcher.map("/debug", print)
   _dispatcher.map("/muse/eeg", eeg_handler, "EEG")

   server = osc_server.ThreadingOSCUDPServer(
       (args.ip, args.port), _dispatcher)
   print("Serving on {}".format(server.server_address))
   
   # This blocks the current thread. That's why this is not in the main thread :)
   server.serve_forever()

def main():
   global win
   global bar
   global args

   #print('Starting')

   # Can run with command line arguments
   parser = argparse.ArgumentParser()
   parser.add_argument("--ip",
                       default="127.0.0.1",
                       help="The ip to listen on")
   parser.add_argument("--port",
                       type=int,
                       default=5001,  #! Change this based on your system
                       help="The port to listen on")
   args = parser.parse_args()
   
   # Can only do GUI from main thread, so we can't block the main thread. Therefore, we need to do this
   # to have the server (listener) on a separate thread.
   serverThread = threading.Thread(target=server)
   serverThread.start()

   # Dead simple GUI library
   win = GraphWin('Output', 1000, 100)
   win.setCoords(0, 0, 100, 10)

   # Clear screen by drawing white everywhere
   bar = Rectangle(Point(1, 1), Point(9, 9))
   bar.setFill('white')
   bar.draw(win)

   while True:
       # Clear only what needs to be cleared, to avoid nasty flicker
       bar = Rectangle(Point(round(concentrationLevel),1), Point(99,9))
       bar.setFill('white')
       bar.draw(win)

       bar = Rectangle(Point(1, 1), Point(round(concentrationLevel), 9))

       # Color coding for more friendly interface
       if concentrationLevel < 15:
           bar.setFill('red')
       elif concentrationLevel < 40:
           bar.setFill('blue')
       else:
           bar.setFill('green')

       bar.draw(win)

       #* Draw threshold bars to show cutoff points for colors
       bar = Rectangle(Point(15, 0), Point(15.1, 10))
       bar.setFill('black')
       bar.draw(win)

       bar = Rectangle(Point(40, 0), Point(40.1, 10))
       bar.draw(win)

       time.sleep(0.001)

if __name__ == '__main__':
   main()
