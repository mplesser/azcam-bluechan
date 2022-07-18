# MMTCommandParser for ccdacq
# 21Jul14 last change MPL

import shlex
from AzCamServerCommands import *

def MMTCommandParser(Command):
    """
    Alternate command parser for MMT ICE syntax.
    Command replies are not in a list, but a single string, as per AzCam 2.x.
    """
    
    """
    Below are the ccdacq commands to be supported:
    
    * Get camtemp
    * Get dewtemp
    * Get utc-obs
    * ReadExposure
    * PauseExposure
    * ResumeExposure
    * AbortExposure
    * ClearArray
    * CloseConnection
    * Reset
    * Set ReadOutMode wait
    * Set ShutterState
    * StartExposure 0
    * ReadImage 0
    * Get pixelcount
    * ParShift
    * SetFormat
    * SetConfiguration
    * SetROI
    * SetGainSpeed
    * SetExposure
    * SendImage 3
    """

    # load all defined objects
    for name in Globals.Objects.keys(): 
	globals()[name] = Globals.Objects[name]

    # if command is a python method, return None to process normally later
    if Command.endswith(')'):
        return None

    # tokenize
    #tokens=shlex.shlex(Command)
    tokens=shlex.split(Command)   # this is messing with slashes
    token=[]
    for t in tokens:
        token.append(str(t))
    cmd=token[0].lower()
    
    if cmd=='reset':
        reply=controller.Reset()
	
    elif cmd=='abortexposure':
        reply=controller.ExposureAbort()
    elif cmd=='pauseexposure':
        reply=controller.ExposurePause()
    elif cmd=='resumeexposure':
        reply=controller.ExposureResume()
    elif cmd=='get' and token[1].lower()=='pixelcount':
	count=controller.GetPixelsRemaining()[1] # counts down
        reply=[Globals.OK,str(focalplane.NumPixImage-count)]
    elif cmd=='get' and token[1].lower()=='camtemp':
        rep=tempcon.GetTemperatures()
	camtemp = str(int(float(rep[1])*1000.)/1000.)
	reply=[rep[0],camtemp]        
    elif cmd=='get' and token[1].lower()=='dewtemp':
        rep=tempcon.GetTemperatures()
	dewtemp = str(int(float(rep[2])*1000.)/1000.)
	reply=[rep[0],dewtemp]        
    elif cmd=='get' and token[1].lower()=='utc-obs':
	reply=controller.header.GetKeyword('UTC-OBS')
	reply=[Globals.OK,reply[1]]
    elif cmd=='parshift':
	rows=int(token[1])
        reply=controller.Parshift(rows)
    elif cmd=='setroi':
        reply=focalplane.SetRoi(int(token[1]),int(token[2]),int(token[3]),int(token[4]),
	    int(token[5]),int(token[6]))
    elif cmd=='setformat':
        reply=focalplane.SetFormat(int(token[1]),int(token[2]),int(token[3]),int(token[4]),
	    int(token[5]),int(token[6]),int(token[7]),int(token[8]),int(token[9]))
    elif cmd=='setconfiguration':  # Flag Splits NumDetX NumDetY AmpConfig
	Flag=int(token[1])     # ignored
	Splits=int(token[2])   # ignored
	NumDetX=int(token[3])  # ignored
	NumDetY=int(token[4])  # ignored
	AmpConfig=token[5]     # string
        reply=focalplane.SetFocalPlane(1,1,1,1,AmpConfig)
    elif cmd=='setgainspeed':  # gain speed
	vg=int(token[1])
	vs=int(token[2])       # speed ignored for gen1
        reply=controller.SetVideoGain(vg)
        reply=controller.SetVideoSpeed(vs)
    elif cmd=='set' and token[1].lower()=='readoutmode':   # ignored as always 'wait' for MMT
	reply=[Globals.OK]
	
    # exposure time
    elif cmd=='setexposure':
	et=int(token[1])/1000.  # millisecs to seconds
        reply=exposure.SetExposureTime(et)
    elif cmd=='readexposure':
        reply=controller.UpdateExposureTimeRemaining()
        etr=float(reply[1])
	et=exposure.ExposureTime-etr
	reply=[reply[0],str(int(et*1000))]        
	
    # set shutter to open or close
    elif cmd=='set' and token[1].lower()=='shutterstate':   # set shutterstate open/close
	state=token[2]
	if state=='open':
	    imagetype='object'        # open shutter
	else:
	    imagetype='dark'
        exposure.ImageType=imagetype  # close shutter
	reply=[Globals.OK]
	
    # flush/clear device
    elif cmd=='cleararray':
	exposure.ExposureFlag=exposure.EF_SETUP
        reply=exposure.Flush()
    # start integration
    elif cmd=='startexposure': # StartExposure 0 (flag ignored)
	exposure.ExposureFlag=exposure.EF_EXPOSING
	reply=exposure.BeginCcdacq()
	reply=exposure.IntegrateCcdacq()
    # start readout
    elif cmd=='readimage':     # ReadImage Flag
	exposure.ExposureFlag=exposure.EF_READOUT
	reply=exposure.ReadoutCcdacq()
    # send image to ccdacq
    elif cmd=='sendimage':     # SendImage 3 Host Port
	exposure.ExposureFlag=exposure.EF_NONE
	Flag=int(token[1])     # ignored
	Host=token[2]
	Port=int(token[3])
	reply=exposure.SendImageFileToCCDacq(Host,Port)
	
    elif cmd=='closeconnection':  # read by CommandServer
        reply=[Globals.OK]
    else:
        return None
    
    # make reply string
    s=' '.join(reply)
    
    return s
