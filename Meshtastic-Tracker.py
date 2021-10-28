#---------------------------------------------------------------------------
#ToDo
#---------------------------------------------------------------------------
#add folium marker - add popup code with additional infos
#folium.Marker(
#    location=[Latitude, Longitude], # coordinates for the marker from meshtastic
#    popup='Earth Lab at CU Boulder', # pop-up label for the marker (example data)
#    icon=folium.Icon()
#    ).add_to(m)
#Save map as index.html
#m.save('index.html')

#unter https://www.python-graph-gallery.com/312-add-markers-on-folium-map gibt es ein beispiel wie mehrere Marker per Dataframe hinzugefügt werden können
#so kann die folium karte immer nur neu generiert werden, nachdem sie schon einmal bestand, d.h. es kann immer nur ein marker hinzugefügt werden, wenn man die alten nicht irgndwie speichert.

import meshtastic
import time
from datetime import datetime
import traceback
from meshtastic.mesh_pb2 import _HARDWAREMODEL
from meshtastic.node import Node
from pubsub import pub
import argparse
import collections
import sys
import os
import math
import numpy as np

#to help with debugging
import inspect

#to review logfiles
import subprocess

#for calculting distance
import geopy.distance

#map support
import folium
from folium import plugins

#for capturing ctl-c
from signal import signal, SIGINT
from sys import exit

#------------------------------------------------------------------------------
# Variable Declaration                                                       --
#------------------------------------------------------------------------------

NAME = 'MeshWatch'                   
DESCRIPTION = "Send and recieve messages to a MeshTastic device"
DEBUG = False

parser = argparse.ArgumentParser(description=DESCRIPTION)
parser.add_argument('-s', '--send',    type=str,   nargs='?', help="send a text message")
parser.add_argument('-t', '--time',    type=int, nargs='?', help="seconds to listen before exiting",default = 36000)
args = parser.parse_args('')


#process arguments and assign values to local variables
if(args.send):
  SendMessage = True
  TheMessage = args.send
else:
  SendMessage = False


TimeToSleep = args.time


global PrintSleep    #controls how fast the screens scroll
global OldPrintSleep #controls how fast the screens scroll
global IPAddress
global Interface
global DeviceStatus
global DeviceName
global DevicePort
global PacketsReceived
global PacketsSent
global LastPacketType
global BaseLat
global BaseLon

global MacAddress
global DeviceID

global PauseOutput
global PriorityOutput

global Latitude
global Longitude
global From
From=('')

global rxTime
rxTime=datetime.now().strftime("%H:%M:%S")

#Create Map
#Latitude = (52.988648999999995)
#Longitude = (13.7978729)

#m = folium.Map(location=[Latitude, Longitude])

global data

data = np.array([['','','','','']])
data = np.delete(data, (0), axis=0)


PrintSleep    = 0.1
OldPrintSleep = PrintSleep

#------------------------------------------------------------------------------
# Functions / Classes                                                        --
#------------------------------------------------------------------------------

class TextWindow(object):
  
  def ScrollPrint(self,PrintLine,Color=2,TimeStamp=True): 

    current_time = datetime.now().strftime("%H:%M:%S")

    if (TimeStamp):
      PrintLine =   current_time + ": {}".format(PrintLine)
   

    try:
      
      while (len(PrintableString) > 0):
        
        #padd with spaces
        #PrintableString = PrintableString.ljust(self.DisplayColumns,' ')
        print(PrintableString)

    except Exception as ErrorMessage:
      TraceMessage = traceback.format_exc()
      AdditionalInfo = "PrintLine: {}".format(PrintLine)

      ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)



def ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo):
  #Window2.ScrollPrint('ErrorHandler',10,TimeStamp=True)
  #Window4.ScrollPrint('** Just a moment...**',8)
  CallingFunction =  inspect.stack()[1][3]
  #FinalCleanup()
  print("")
  print("")
  print("--------------------------------------------------------------")
  print("ERROR - Function (",CallingFunction, ") has encountered an error. ")
  print(ErrorMessage)
  print("")
  print("")
  print("TRACE")
  print(TraceMessage)
  print("")
  print("")
  if (AdditionalInfo != ""):
    print("Additonal info:",AdditionalInfo)
    print("")
    print("")
  print("--------------------------------------------------------------")
  print("")
  print("")
  time.sleep(1)
  sys.exit('Good by for now...')


def fromStr(valstr):
    """try to parse as int, float or bool (and fallback to a string as last resort)
    Returns: an int, bool, float, str or byte array (for strings of hex digits)
    Args:
        valstr (string): A user provided string
    """
    if(len(valstr) == 0):  # Treat an emptystring as an empty bytes
        val = bytes()
    elif(valstr.startswith('0x')):
        # if needed convert to string with asBytes.decode('utf-8')
        val = bytes.fromhex(valstr[2:])
    elif valstr == True:
        val = True
    elif valstr == False:
        val = False
    else:
        try:
            val = int(valstr)
        except ValueError:
            try:
                val = float(valstr)
            except ValueError:
                val = valstr  # Not a float or an int, assume string

    return val



def DecodePacket(PacketParent,Packet,Filler,FillerChar,PrintSleep=0):
  global DeviceStatus
  global DeviceName
  global DevicePort
  global PacketsReceived
  global PacketsSent
  global LastPacketType
  global HardwareModel
  global DeviceID 
  global rxTime
  global From
  global Latitude
  global Longitude

  #This is a recursive funtion that will decode a packet (get key/value pairs from a dictionary )
  #if the value is itself a dictionary, recurse
  print("DecodePacket")
  #Filler = ('-' *  len(inspect.stack(0)))

  #used to indent packets
  if (PacketParent.upper() != 'MAINPACKET'):
    Filler = Filler + FillerChar
 
  print("{}".format(PacketParent).upper())
  #UpdateStatusWindow(NewLastPacketType=PacketParent)

  #adjust the input to slow down the output for that cool retro feel
  if (PrintSleep > 0):
    time.sleep(PrintSleep)

  if PriorityOutput == True:
    time.sleep(5)
  

  #if the packet is a dictionary, decode it
  if isinstance(Packet, collections.abc.Mapping):

    
    for Key in Packet.keys():
      Value = Packet.get(Key) 

      if (PrintSleep > 0):
        time.sleep(PrintSleep)
  

      #if the value paired with this key is another dictionary, keep digging
      if isinstance(Value, collections.abc.Mapping):

        #Print the name/type of the packet
        print(" ")
        LastPacketType = Key.upper()

        DecodePacket("{}/{}".format(PacketParent,Key).upper(),Value,Filler,FillerChar,PrintSleep=PrintSleep)  

      else:
        #Print KEY if not RAW (gotta decode those further, or ignore)
        if(Key == 'raw'):
          print("{}  RAW value not yet suported by DecodePacket function".format(Filler))
        
        #Save Data for Map
        if (Key == 'rxTime'):
          rxTime = int(("{}".format(Value)))
          rxTime = time.localtime(rxTime)
          rxTime = datetime.fromtimestamp(time.mktime(rxTime))
          rxTime = rxTime.strftime("%d.%m.%y %H:%M:%S")
        
        if (Key == 'from'):
          From = ("{}".format(Value))
        
        if (Key == 'latitude'):
          Latitude = ("{}".format(Value))
        
        if (Key == 'longitude'):
          Longitude = ("{}".format(Value))

        else:
          print("  {}{}: {}".format(Filler,Key,Value))
    
  else:
    print("Warning: Not a packet!")
 
def createMap (Latitude, Longitude, From, rxTime):            #ein positional packet enthält leider nicht den Longname, daher werden die Namen durcheinander gebracht. Eine Lösung wäre das "from" Feld zu verwenden, dann bekommt man aber nur die id und nicht den Namen.
    #data frame for storage of coordinates and data
    global data
    new_row = np.array([Latitude, Longitude, From, rxTime,""])
    data = np.vstack([data, new_row])
    #assign Color
    unID, indices = np.unique(data[:,2], return_inverse=True)
    colors=["red", "blue", "green", "purple", "orange", "darkred", "lightred", "beige", "darkblue", "darkgreen", "cadetblue", "darkpurple", "white", "pink", "lightblue", "lightgreen", "gray", "black", "lightgray"]
    unID=np.array(unID,dtype=str)
    
    for i in range(len(unID)):
       unID[i]=colors[i]
    unColors=unID[indices]
    unColors=[unColors]

    for i in range(len(unColors)):
       data[:,4]=unColors[i]
  
    #create the map
    m = folium.Map(location=[Latitude, Longitude])
    #add map markers
    for x in data:          #convert array elements to float 8-(
      Striplat=x[0].split()
      Striplong=x[1].split()
      Latitude=float(Striplat[0])
      Longitude=float(Striplong[0])
      folium.Marker(
        location=[Latitude, Longitude], # coordinates for the marker from meshtastic
        popup=(x[2], x[3]), # pop-up label for the marker Logname, txTime
        icon=folium.Icon(color=x[4])
      ).add_to(m)      
      m.save('map.html')
    print("--------------------------------------------------------------")
    print ('Map created')
    print("--------------------------------------------------------------")
 

def onReceive(packet, interface): # called when a packet arrives
    global PacketsReceived
    global PacketsSent
    
    PacketsReceived = PacketsReceived + 1
    

    print("onReceive")
    print(" ")    
    print("==Packet RECEIVED======================================")

    Decoded  = packet.get('decoded')
    Message  = Decoded.get('text')
    To       = packet.get('to')
    From     = packet.get('from')

    #Even better method, use this recursively to decode all the packets of packets
    DecodePacket('MainPacket',packet,Filler='',FillerChar='',PrintSleep=PrintSleep)
    
    #create updated map
    try:                                               #only create the Map if we get valid coordinates
      createMap (Latitude, Longitude, From, rxTime)
    except NameError:
      print("No Coordinates received.")
    else:
      createMap (Latitude, Longitude, From, rxTime)   
    
    if(Message):
      print("From: {} - {}".format(From,Message))
    print("=======================================================")
    print(" ")    

    

def onConnectionEstablished(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
  global PriorityOutput

  if(PriorityOutput == False):
    
    From = "BaseStation"
    To   = "All"
    current_time = datetime.now().strftime("%H:%M:%S")
    Message = "MeshWatch active,  please respond. [{}]".format(current_time)
    print("From: {} - {}".format(From,Message,To))
    
    try:
      interface.sendText(Message, wantAck=True)
      print("")    
      print("==Packet SENT==========================================")
      print("To:     {}:".format(To))
      print("From    {}:".format(From))
      print("Message {}:".format(Message))
      print("=======================================================")
      print("")    

    except Exception as ErrorMessage:
      TraceMessage = traceback.format_exc()
      AdditionalInfo = "Sending text message ({})".format(Message)
      ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)


def onConnectionLost(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
  global PriorityOutput
  if(PriorityOutput == False):
    print('onConnectionLost')
    #UpdateStatusWindow(NewDeviceStatus = "DISCONNECTED",Color=1)


def onNodeUpdated(interface, topic=pub.AUTO_TOPIC): # called when we (re)connect to the radio
  global PriorityOutput
  if(PriorityOutput == False):
    print('onNodeUpdated')
    print('UPDATE RECEIVED')
    print("")    


def SIGINT_handler(signal_received, frame):
  # Handle any cleanup here
  print('WARNING: Somethign bad happened.  SIGINT detected.')
  #FinalCleanup()  
  print('** END OF LINE')
  sys.exit('Good by for now...')

def GetMyNodeInfo(interface):


    Distance   = 0
    DeviceName = ''
    BaseLat    = 0
    BaseLon    = 0

    print(" ")
    print("==MyNodeInfo===================================")
    TheNode = interface.getMyNodeInfo()
    DecodePacket('MYNODE',TheNode,'','',PrintSleep =PrintSleep)
    print("===============================================")
    print(" ")

    if 'latitude' in TheNode['position'] and 'longitude' in TheNode['position']:
      BaseLat = TheNode['position']['latitude']
      BaseLon = TheNode['position']['longitude']
      #UpdateStatusWindow(NewLon=BaseLon,NewLat=BaseLat,Color=2)
      createMap (Latitude, Longitude, 'MyNode', rxTime)                                #wenn ein location packet vor einem ident packet kommt wird leider noch der falsche Node Name in createMap verwendet
    else:
      print('No positional information available.')
      print("===============================================")

def GoToSleep(TimeToSleep):
  print("GoToSleep({})".format(TimeToSleep))
  for i in range (0,(TimeToSleep * 10)):
    #Check for keyboard input      --
    #PollKeyboard()
    time.sleep(0.1)



#--------------------------------------
# Main (function)                    --
#--------------------------------------

def main():
  global interface
  global DeviceStatus
  global DeviceName
  global DevicePort
  global PacketsSent
  global PacketsReceived
  global LastPacketType
  global HardwareModel
  global MacAddress
  global DeviceID
  global PauseOutput
  global HardwareModel
  global PriorityOutput
  global BaseLat
  global BaseLon

  try:




    DeviceName      = '??'
    DeviceStatus    = '??'
    DevicePort      = '??'
    PacketsReceived = 0
    PacketsSent     = 0
    LastPacketType  = ''
    HardwareModel   = ''
    MacAddress      = ''
    DeviceName      = ''
    DeviceID        = ''
    PauseOutput     = False
    HardwareModel   = '??'
    PriorityOutput  = False,
    BaseLat         = 0
    BaseLon         = 0

    
    #CreateTextWindows()
    print("System initiated")
    print("Priorityoutput: {}".format(PriorityOutput))
    
    
    #Instanciate a meshtastic object
    #By default will try to find a meshtastic device, otherwise provide a device path like /dev/ttyUSB0
    print("Finding Meshtastic device")
    
    interface = meshtastic.SerialInterface()

    #subscribe to connection and receive channels
    print("Subscribe to publications")
    pub.subscribe(onConnectionEstablished, "meshtastic.connection.established")
    pub.subscribe(onConnectionLost,        "meshtastic.connection.lost")
    
    #does not seem to work
    #pub.subscribe(onNodeUpdated,           "meshtastic.node.updated")
    time.sleep(2)
    #Get node info for connected device
    print("Requesting device info")
    GetMyNodeInfo(interface)

    #Check for message to be sent (command line option)
    if(SendMessage):
       interface.sendText(TheMessage, wantAck=True)

    #Go into listening mode
    print("Listening for: {} seconds".format(TimeToSleep))
    print("Subscribing to interface channels...")
    pub.subscribe(onReceive, "meshtastic.receive")

    while (1==1):
      GoToSleep(5)

    interface.close()  
    print("--End of Line------------")
    print("")
    
  except Exception as ErrorMessage:
    time.sleep(2)
    TraceMessage = traceback.format_exc()
    AdditionalInfo = "Main function "
    ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)


#--------------------------------------
# Main (pre-amble                    --
#--------------------------------------

  #if SIGINT or CTL-C detected, run SIGINT_handler to exit gracefully
  signal(SIGINT, SIGINT_handler)


#only execute if we are in main
if __name__=='__main__':
  try:

      main()                    # Enter the main loop

  except Exception as ErrorMessage:
      # In event of error, restore terminal to sane state.
      TraceMessage = traceback.format_exc()
      AdditionalInfo = "Main pre-amble"
      ErrorHandler(ErrorMessage,TraceMessage,AdditionalInfo)


# %%
