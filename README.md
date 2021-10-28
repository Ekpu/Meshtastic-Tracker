# Meshtastic-Tracker

I wanted to be able to create a map with the locations of the connected meshtastic devices.
I am not a programmer but only a hobbyist so please don't expect professional code.
As a base I used meshwatch from datagod (https://github.com/datagod/meshwatch).
I could not get curses to run properly on my windows machine, so I stripped the code related to it.
I am sure there are some remnant's left which are unnecessary.

For the map I used folium.

The program will listen for packets received on a connected meshtastic device via serial.
Packets with location will be placed as marker on a map which will be saved as HTML file map.html.
The old positions will be kept so all known positions of the devices will be displayed along with their ID and the time.
Unfortunately the packets which contain the position don't contain the name of the device which led to errors so I used the ID of the devices.
Each ID's markers will get a unique color. There are only 19 colours available so the script will only work with 19 devices.
This includes the device connected via serial if it has a known location during the start of the script.

The map will be recreated every time a packet with a location is received.
The website needs do be reloaded manually.

## Installation
A guide to use you meshtastic device with Python is found here: https://meshtastic.org/docs/software/python/python-installation


A good guide for windows is found here: https://meshtastic.discourse.group/t/tutorial-setting-up-a-windows-machine-for-use-with-meshtastic-python/2872

Please be aware, that there a different chips for the uart communication. On my TTGO T-Beam devices I had to use this Driver: https://meshtastic.discourse.group/t/t-beam-ch9201-drivers/3875

Additional packages for Python which are needed are: numpy, geopy and folium.

## Disclaimer
Please be aware that this is a hobby project. Therefore I don't have much time to resolve issues and provide support. Nevertheless I wanted to provide this little project to the community. If I have an idea for other intresting features or there is a bug which is unbearable for me I will put further work into the project. If not please take it "as is".
