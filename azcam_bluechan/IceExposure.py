# Exposure class for ARC controllers using Skip Schaller's ICE package.
# A controller object must be defined before loading this module.
# Commands followed by '1' return immediately after starting the base command in a new thread.
# 01Oct13 last change MPL

import string,threading,socket,numpy
from AzCamServerCommands import *
import ExposureClass

class Exposure(ExposureClass.ExposureClass):
    """
    Defines the exposure class for ARC controllers using ICE/ccdacw to make an exposure.
    """

    def __init__(self):
        """
        Create exposure object.
        """

	# initialize Exposure
	ExposureClass.ExposureClass.__init__(self)
    
        ## exposure flag defining state of current exposure
        self.ExposureFlag=self.EF_NONE
        
    # ******************************************************************************
    #   exposure control
    # ******************************************************************************

    def Expose(self,ExposureTime=-1,ImageType='',Title=''):
        """
        Make a complete exposure.
        ExposureTime is the exposure time in seconds
        ImageType is the type of exposure ('zero', 'object', 'flat', ...)
        Title is the image title.
        """	

        # for Expose1
        x=ExposureTime
        if type(x)==tuple:
            if len(x)==3:
                ExposureTime=x[0]
                ImageType=x[1]
                Title=x[2]
            elif len(x)==2:
                ExposureTime=x[0]
                ImageType=x[1]
                Title=''
            elif len(x)==1:
                ExposureTime=x[0]
                ImageType=''
                Title=''
            else:
                ExposureTime=-1
                ImageType=''
                Title=''
            
        # allow custom operations
        reply=self.Start()
        if CheckReply(reply):
            return reply

        Print('Exposure started')

        # if last exposure was aborted, clear flag and continue
        if self.ExposureFlag==self.EF_ABORT:
            Print('WARNING: previous exposure was aborted')

        # reset error at start of exposure
        SetErrorStatus()

	# system must be reset once before an exposure can be made
	x=self.isExposureSequence               # save this falg which is lost by Reset()
	if not GetObject('controller').isReset:
	    reply=GetObject('controller').Reset()
	    if CheckReply(reply):
		return reply
	    self.isExposureSequence=x

        # begin
        if self.ExposureFlag!=self.EF_ABORT:
            reply=self.Begin(ExposureTime,ImageType,Title)
            if CheckReply(reply):
                self.ExposureFlag=self.EF_NONE
                if reply[0]==Globals.ABORTED:
                    return [Globals.OK]
                return reply

        # integrate
        if self.ExposureFlag!=self.EF_ABORT:
            reply=self.Integrate()
            if CheckReply(reply):
                self.ExposureFlag=self.EF_NONE
                if reply[0]==Globals.ABORTED:
                    return [Globals.OK]
                return reply

        # readout
        if self.ExposureFlag!=self.EF_ABORT:
            if self.ExposureFlag==self.EF_READ:
                reply=self.Readout()
                if CheckReply(reply):
                    self.ExposureFlag=self.EF_NONE
                    if reply[0]==Globals.ABORTED:
                        return [Globals.OK]
                    return reply

        # end
        if self.ExposureFlag!=self.EF_ABORT:
            reply=self.End()
            if CheckReply(reply):
                self.ExposureFlag=self.EF_NONE
                if reply[0]==Globals.ABORTED:
                    return [Globals.OK]
                return reply

        self.ExposureFlag=self.EF_NONE
        Print('Exposure finished')
        
        # allow custom operations
        reply=self.Finish()
        if CheckReply(reply):
            return reply

        return [Globals.OK]

    def Guide(self,NumberExposures=1,GuideMode=1):
        """
        Make a complete guider exposure sequence.
        NumberExposures is the number of exposures to make, -1 loop forever
        GuideMode is type of guiding, 1=LBT, 2=SOguider, 2=ITLguider
        """

        AbortFlag=0

        # for Guide1
        x=NumberExposures
        if type(x)==tuple:
            NumberExposures=x[0]
            GuideMode=x[1]

        self.GuideMode=GuideMode

        # system must be reset once before an exposure can be made
        if not GetObject('controller').isReset:
            GetObject('controller').Reset()

        # setup and flush
        SetErrorStatus()

        # parameters for faster operation
        flushArray=self.FlushArray
        saveKeywords=self.SaveKeywords
        Print('Guide started')

        # this loop continues even for errors since data is sent to a seperate client receiving images
        LoopCount=0
        while(True):

            reply=self.Begin(ExposureTime=-1,ImageType='object',Title='guide image')
            if CheckReply(reply):
                self.ExposureFlag=self.EF_NONE
                if reply[0]==Globals.ABORTED:
                    return [Globals.OK]
                else:
                    return reply

            # integrate
            reply=self.Integrate()
            if CheckReply(reply):
                self.ExposureFlag=self.EF_NONE
                if reply[0]==Globals.ABORTED:
                    return [Globals.OK]
                else:
                    return reply

            # readout
            if self.ExposureFlag==self.EF_READ:
                reply=self.Readout()
                self.ExposureFlag=self.EF_NONE
                if CheckReply(reply):
                    if reply[0]==Globals.ABORTED:
                        return [Globals.OK]
                    else:
                        return reply

            # image writing
            reply=self.End()
            self.ExposureFlag=self.EF_NONE
            if CheckReply(reply):
                if reply[0]==Globals.ABORTED:
                    return [Globals.OK]
                else:
                    return reply

            self.ExposureFlag=self.EF_NONE

            AbortFlag=CheckAbort()
            if AbortFlag:
                break

            if NumberExposures==-1:
                pass
            else:
                LoopCount+=1

            if LoopCount>=NumberExposures:
                break

        # finish	
        self.GuideMode=0
        self.FlushArray=flushArray
        self.SaveKeywords=saveKeywords

        if AbortFlag:
            Print('Guide aborted')
            return [Globals.ABORTED]
        else:
            Print('Guide finished')
            return [Globals.OK]

    def Begin(self,ExposureTime=-1,ImageType='',Title=''):
        """
        Initiates the first part of an exposure, through image flushing.
        ExposureTime in seconds.
        ImageType:
        zero
        object
        flat
        dark     
        ramp      - normal exposure then readout with shutter open
        tdi
        """

        # set exposure flag
        self.ExposureFlag=self.EF_SETUP
        
        # reset flags as new data coming
        self.image.isValid=0
        self.image.isWritten=0
        self.image.Toggle=0
        self.image.isAssembled=0

        # update controller shifting parameters
        if Globals.newroi:
            reply=GetObject('controller').SetRoi()
            if CheckReply(reply):
                return reply

        # clear the image header
        self.image.header.DeleteAllItems()
        self.image.header.DeleteAllKeywords()

        # update image size
        self.image.SizeX = GetObject('focalplane').NumColsImage
        self.image.SizeY = GetObject('focalplane').NumRowsImage
        
        # create self.image.Data buffer of correct size, unsigned shorts
        #    first index is number of extensions (0->NumAmpsImage-1), second is number pixels per extension)
        if Globals.newroi:
            self.image.Data = numpy.empty(shape=[GetObject('focalplane').NumAmpsImage,GetObject('focalplane').NumPixAmp],dtype='<u2')    

            # initialize real-time deinterlace
            reply = self.receivedata.InitDeinterlace(self.DeinterlaceMode)

            Globals.newroi=0  # reset

        # ImageType
        if ImageType=='':
            ImageType=self.ImageType                     # if not specified use previous
        else:
            self.ImageType=ImageType
        self.image.ImageType=self.ImageType
        imagetype=ImageType.lower()

        # times
        if ExposureTime==-1:                             # if not specified use previous
            ExposureTime=self.ExposureTime
        else:
            self.ExposureTime=float(ExposureTime)
        self.ExposureTimeSaved=self.ExposureTime

        if imagetype=='zero':
            self.ExposureTime=0.0
            ExposureTime=0.0

        self.PausedTime=0.0                              # reset paused time
        self.PausedTimeStart=0.0                         # reset paused start time
        self.ExposureTimeRemaining=ExposureTime          # reset remaining time to exposure time

        # set OBJECT keyword using Title
        if self.AutoTitle:
            Title=self.ImageType.lower()
            self.Title=Title
        
        if Title=='':                                    # not specified	
            if len(self.Title)>0:                            # use previous if non-blank
                GetObject('controller').header.SetKeyword('OBJECT',self.Title,'',str)
            else:			
                GetObject('controller').header.SetKeyword('OBJECT','','',str)
        else:
            self.Title=Title                          # save for next time
            GetObject('controller').header.SetKeyword('OBJECT',Title,'',str)

        # send exposure time to controller
        # this is the first hardware command in a loop, so allow extra time of the controller is busy
        reply=self.SetExposureTime(ExposureTime)
        if reply[0]!=Globals.OK:
            for i in range(30):   # 3 seconds
                time.sleep(0.1)
                reply=self.SetExposureTime(ExposureTime)
                if reply[0]==Globals.OK:
                    break
            if CheckReply(reply):		
                return reply

        # set total number of pixels to readout
        self.PixelsRemaining=GetObject('focalplane').NumPixImage
        self.PixelsRemaining=GetObject('focalplane').NumPixImage

        if not self.GuideMode:   # for speed
            # select current video output
            reply=GetObject('controller').SelectVideoOutputs()
            if CheckReply(reply):
                return reply

            # set shutter state
            try:
                shutterstate=self.ShutterDict[imagetype]
            except KeyError:
                shutterstate='open'   # other types are comps, so open shutter
            reply=GetObject('controller').SetShutterState(shutterstate)
            if CheckReply(reply):
                return reply

        # set CompExposure flag for any undefined image types (comp names)
        if imagetype in self.ImageTypes:
            self.CompExposure=0
        else:
            self.CompExposure=1

        # set comp lamps, turn on, set keyword
        GetObject('controller').header.DeleteKeyword('COMPLAMP')
        if self.CompExposure and GetObject('instrument').Enabled:
            if self.CompSequence:
                lampnames = string.join(GetObject('instrument').GetActiveComps()[1:],' ')
                GetObject('controller').header.SetKeyword('COMPLAMP',lampnames,'Comp lamp names',str)
                GetObject('controller').header.SetKeyword('IMAGETYP','comp','Image type',str)
            else:
                GetObject('instrument').SetActiveComps(ImageType)
                if GetObject('instrument').ShutterStrobeInstrument:
                    pass     # these instruments use shutter to turn on comps
                else:
                    GetObject('instrument').CompsOn()
                lampnames = string.join(GetObject('instrument').GetActiveComps()[1:],' ')
                GetObject('controller').header.SetKeyword('COMPLAMP',lampnames,'Comp lamp names',str)
                GetObject('controller').header.SetKeyword('IMAGETYP','comp','Image type',str)
                GetObject('instrument').CompsDelay()                              # delay for lamp warmup
        else:
            if not self.GuideMode:
                GetObject('controller').header.SetKeyword('IMAGETYP',imagetype,'Image type',str)

        # record current time and date in header
        reply=self.RecordCurrentTimes()
        if CheckReply(reply):
            return reply

        # update all headers with current data
        reply=self.UpdateHeaders(self.SaveKeywords)
        if CheckReply(reply):
            return reply

        # flush detector
        if self.FlushArray:
            Print('Flushing')
            reply=self.Flush()
            if CheckReply(reply):
                return reply
        else:
            reply=GetObject('controller').StopIdle()
            if CheckReply(reply):
                return reply

        return [Globals.OK]

    def Integrate(self):
        """
        Integration.
        """

        # start integration
        self.ExposureFlag=self.EF_EXPOSING
        imagetype=self.ImageType.lower()

        # flag to change OD voltages during integration
        CHANGEVOLTAGES=self.ImageType.lower()!='zero' and GetObject('controller').LowerVoltages

        if CHANGEVOLTAGES:
            # lower OD's
            reply=GetObject('controller').BoardCommand('RMP',GetObject('controller').TIMINGBOARD,0)
            if CheckReply(reply):
                return reply

        # start exposure
        if imagetype!='zero':
            Print('Integration started')
        reply=GetObject('controller').StartExposure()
        if CheckReply(reply):
            if CHANGEVOLTAGES:  # return OD volatges
                GetObject('controller').BoardCommand('RMP',GetObject('controller').TIMINGBOARD,1)
            return reply
        self.DarkTimeStart=time.time()

	reply=self.GetExposureTimeRemaining()
	if CheckReply(reply):
	    return reply
	remtime=reply[1]
        lasttime=remtime

        # countdown and check for async. ExposureFlag changes
        loopcount=0
        if GetObject('controller').DemoMode:
            remtime=0.0

        while remtime > 0.1:
            if self.ExposureFlag==self.EF_EXPOSING:    # no EF changes
                time.sleep(min(remtime,0.5))
		reply=self.GetExposureTimeRemaining()
		if CheckReply(reply):
		    return reply
		remtime=reply[1]
                if remtime==lasttime:
                    loopcount+=1
                else:
                    loopcount=0
                    lasttime=remtime

            if loopcount>20:
                Print('ERROR Integration time stuck')
                self.ExposureFlag=self.EF_ABORT
                GetObject('controller').ExposureAbort()
                break
            elif self.ExposureFlag==self.EF_ABORT:     # AbortExposure received
                GetObject('controller').ExposureAbort()
                break
            elif self.ExposureFlag==self.EF_PAUSE:     # PauseExposure received
                GetObject('controller').ExposurePause()
                self.ExposureFlag=self.EF_PAUSED
                Print('Integration paused')
            elif self.ExposureFlag==self.EF_RESUME:    # ResumeExposure received
                GetObject('controller').ExposureResume()
                self.ExposureFlag=self.EF_EXPOSING
		reply=self.GetExposureTimeRemaining()
		if CheckReply(reply):
		    return reply
		remtime=reply[1]
                Print('Integration resumed')
            elif self.ExposureFlag==self.EF_READ:      # ReadExposure received
                remtime=0.0
                self.ExposureTimeActual=self.ExposureTime-self.ExposureTimeRemaining
                break
            elif self.ExposureFlag==self.EF_PAUSED:    # already paused so just loop
                time.sleep(0.5)

        if self.ExposureFlag==self.EF_ABORT:           # abort in remaining time
            Print('Exposure aborted')
        else:
            time.sleep(remtime)
            self.ExposureFlag=self.EF_READ             # set to readout

        self.DarkTime=time.time()-self.DarkTimeStart

        # return OD volatges
        if CHANGEVOLTAGES:
            GetObject('controller').BoardCommand('RMP',GetObject('controller').TIMINGBOARD,1)
            if CheckReply(reply):
                return reply
            time.sleep(.5)  # delay for voltages to come up

        # reset comp lamps
        if self.CompExposure and GetObject('instrument').Enabled and not self.CompSequence:
            if GetObject('instrument').ShutterStrobeInstrument:
                if self.ImageType.lower()=='fe55':
                    time.sleep(3)
                GetObject('instrument').SetActiveComps('shutter')
            else:
                GetObject('instrument').CompsOff()
            if self.ExposureFlag==self.EF_ABORT:
                GetObject('controller').header.DeleteKeyword('COMPLAMP')

        # set times
        self.ExposureTimeRemaining=0
        if imagetype=='zero':
            self.ExposureTime=self.ExposureTimeSaved
        else:
            Print('Integration finished')

        if self.ExposureFlag==self.EF_ABORT:
            return [Globals.ABORTED,'Integration aborted']
        else:		
            return [Globals.OK]

    def Readout(self):
        """
        Exposure readout.
        """

        self.ExposureFlag=self.EF_READOUT

        imagetype=self.ImageType.lower()

        if imagetype=='ramp':
            GetObject('controller').OpenShutter()
            
        if self.TdiMode:
            self.SetTdiDelay(True)

        # start readout
        Print('Readout started')
        reply=GetObject('controller').StartReadout()
        if CheckReply(reply):
            return reply

        # loop over pixel count, counting down
        self.GetPixelsRemaining()
        counter=0
        oldcount=self.PixelsRemaining
        totpixels=float(GetObject('focalplane').NumPixImage)
        
        if GetObject('controller').DemoMode:
            self.PixelsRemaining=0
            self.image.isValid=1
            self.image.isAssembled=1
            status,ix,iy=self.GetImageSize()            
            # make ramp image in Buffer
            self.image.Buffer=numpy.zeros((iy,ix))
            k=0
            for j in range(iy):
                for i in range(ix):
                    self.image.Buffer[j,i]=k
                    k+=1
                    k=k%65355
                    
        else:            
            # start data transfer, returns when all data is received
            reply = self.receivedata.ReceiveImageData(GetObject('focalplane').NumPixImage * 2)            
            if CheckReply(reply):
                self.ExposureFlag=self.EF_ABORT
                GetObject('controller').ReadoutAbort()                

        if imagetype=='ramp':
            GetObject('controller').CloseShutter()

        if self.TdiMode:
            self.SetTdiDelay(False)

        if self.ExposureFlag==self.EF_ABORT:
            Print('Readout aborted')
            return [Globals.ABORTED,'Readout aborted']
        else:
            Print('Readout finished')
            self.ExposureFlag=self.EF_NONE
            return [Globals.OK]

    def End(self):
        """
        Completes an exposure by writing file and displaying image.
        """

        self.ExposureFlag=self.EF_WRITING

        if self.RemoteImageServer:
            CurrentFile=self.TempImageFile+'.'+self.image.filename.GetExtension(self.image.FileType)[1]
            try:
                os.remove(CurrentFile)
            except:
                pass
        else:
            CurrentFile=self.image.filename.GetName()[1]

        # wait for image data to be received
        if  not GetObject('controller').DemoMode:
            loop=0
            while not self.image.isValid and loop<100:
                loop=+1
                time.sleep(.050)
                if loop>=100:
                    Print('ERROR image data not received in time')

        # update controller header with keywords which might have changed
        et = float(int(self.ExposureTimeActual*1000.)/1000.)
        dt = float(int(self.DarkTime*1000.)/1000.)
        GetObject('controller').header.SetKeyword('EXPTIME',et,'Exposure time (seconds)',float)
        GetObject('controller').header.SetKeyword('DARKTIME',dt,'Dark time (seconds)',float)

        if GetObject('controller') !=0: 
            if GetObject('controller').Enabled:
                self.image.header.CopyAllItems(GetObject('controller'))

        # copy all header items
        if not self.GuideMode:   # for speed

            GetObject('focalplane').UpdateHeaderKeywords()
            self.image.header.CopyAllItems(GetObject('focalplane'))        
            
            try:
                if GetObject('instrument').Enabled:
                    self.image.header.CopyAllItems(GetObject('instrument'))
            except Exception,message:
                pass

            try:
                if GetObject('telescope').Enabled:
                    self.image.header.CopyAllItems(GetObject('telescope'))
            except Exception,message:
                pass

            try:
                if GetObject('tempcon').Enabled:
                    self.image.header.CopyAllItems(GetObject('tempcon'))      
            except Exception,message:
                pass

        # write file(s) to disk
        if self.SaveFile:
            Print('Writing %s' % CurrentFile)

            # if this is a binary file then must assemble so flips work properly
            if self.image.FileType==self.image.BIN:
                self.image.AssembleImage=1

            # write the file to disk
            reply=self.image.WriteFile(CurrentFile,self.image.FileType)
            if CheckReply(reply):
                return reply		
            Print('Writing finished')

            # set flag that image now written to disk
            self.image.isWritten=1

            # send image to ICE
            if self.RemoteImageServer:
                reply=self.SendImage(CurrentFile,'ccdacq')
                if CheckReply(reply):
                    return reply

        # image data and file are now ready
        self.image.Toggle=1

        # display image
        if self.DisplayImage:
            try:
                Print('Displaying image')
                reply=GetObject('display').Display(self.image)
                CheckReply(reply,True)
            except:
                pass

        # analyze image
        if self.AnalyzeImage:
            try:
                reply=GetObject('analyze').Analyze(self.image)
                CheckReply(reply,True)
            except:
                pass

        # update web status server info
        if self.WebUpdate:
            try:
                reply=GetObject('statusweb').UpdateWebStatus()
                CheckReply(reply,True)
            except:
                pass
            
        # increment file sequence number if image was written
        if self.SaveFile:
            self.image.filename.Increment()			

        self.ExposureFlag=self.EF_NONE

        return [Globals.OK]
    
    # *******************************************************************************        
    # CCDACQ mode for MMT
    # *******************************************************************************
    def BeginCcdacq(self):
        """
        Initiates the first part of an exposure.
        """
        
        imagetype=self.ImageType.lower()
        
        # reset flags as new data coming
        self.image.isValid=0
        self.image.isWritten=0
        self.image.Toggle=0
        self.image.isAssembled=0

        # update controller shifting parameters
        if Globals.newroi:
            reply=GetObject('controller').SetRoi()
            if CheckReply(reply):
                return reply

        # clear the image header
        self.image.header.DeleteAllItems()
        self.image.header.DeleteAllKeywords()

        # update image size
        self.image.SizeX = GetObject('focalplane').NumColsImage
        self.image.SizeY = GetObject('focalplane').NumRowsImage
        
        # create self.image.Data buffer of correct size, unsigned shorts
        #    first index is number of extensions (0->NumAmpsImage-1), second is number pixels per extension)
        if Globals.newroi:
            self.image.Data = numpy.empty(shape=[GetObject('focalplane').NumAmpsImage,GetObject('focalplane').NumPixAmp],dtype='<u2')    

	    # initialize real-time deinterlace
	    reply = self.receivedata.InitDeinterlace(self.DeinterlaceMode)
	    
	    Globals.newroi=0  # reset

        self.PausedTime=0.0                              # reset paused time
        self.PausedTimeStart=0.0                         # reset paused start time
        self.ExposureTimeRemaining=self.ExposureTime          # reset remaining time to exposure time

        # set total number of pixels to readout
        self.PixelsRemaining=GetObject('focalplane').NumPixImage
        self.PixelsRemaining=GetObject('focalplane').NumPixImage

        # set shutter state
        try:
            shutterstate=self.ShutterDict[imagetype]
        except KeyError:
            shutterstate='open'   # other types are comps, so open shutter
        reply=GetObject('controller').SetShutterState(shutterstate)
        if CheckReply(reply):
            return reply

        self.CompExposure=0

        # record current time and date in header
        reply=self.RecordCurrentTimes()
        if CheckReply(reply):
            return reply

        # update all headers with current data
        reply=self.UpdateHeaders(self.SaveKeywords)
        if CheckReply(reply):
            return reply
        
        return [Globals.OK]

    def IntegrateCcdacq(self):
        """
        Integration.
        """

        Print('Integration started')
        
        # start integration
        imagetype=self.ImageType.lower()

        # get current time and date
        self.time.Update(0)
        GetObject('controller').header.SetKeyword('UTC-OBS',self.time.UT[0],'UTC at start of exposure',str)

        reply=GetObject('controller').StartExposure()
        if CheckReply(reply):
            return reply
        self.DarkTimeStart=time.time()

        return [Globals.OK]

    def ReadoutCcdacq(self):
        """
        Exposure readout.
        """

        imagetype=self.ImageType.lower()

        # start readout
        Print('Readout started')
        reply=GetObject('controller').StartReadout()
        if CheckReply(reply):
            return reply

        # start data transfer, returns when all data is received
        reply = self.receivedata.ReceiveImageData(GetObject('focalplane').NumPixImage * 2)            
        if CheckReply(reply):
            self.ExposureFlag=self.EF_ABORT
            GetObject('controller').ReadoutAbort()  
            
        return [Globals.OK]

# create instance
exposure=Exposure()
SetObject('exposure',exposure)
