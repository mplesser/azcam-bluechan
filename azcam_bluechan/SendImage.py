# Contains SendImage class to send local image to remote server.
# 17May13 last change MPL

import os,pyfits,numpy,threading,shutil,time,subprocess,socket
from AzCamServerCommands import *

class SendImage(object):
    """
    SendImage class to send local image to a remote ImageServer.
    """

    def __init__(self):
        """
        Initialize sendimage object.
        """
        
        self.RemoteImageServerHost=''
        self.RemoteImageServerPort=0
        self.RemoteImageFileName=''
        
        # lbtguider,dataserver,ccdacq,azcam,mmtguider
        self.ServerType='azcam'
                
    def SetRemoteImage(self,RemoteServerHost='',RemoteServerPort=0):
        """
        Set parameters so image files are sent to a remote image server.
        If no host is provided then reset to local image file.
        """
    
        if RemoteServerHost=='':
            self.RemoteImageServer=0
        else:
            self.RemoteImageServer=1
            
        self.RemoteImageServerHost=int(RemoteServerHost)
        self.RemoteImageServerPort=int(RemoteServerPort)
        
        return [Globals.OK]
    
    def SendImage(self,Filename,ServerType=''):
        """
        Send image to a remote ImageServer using remote Filename.
        """
        
        if ServerType=='':
            ServerType=self.ServerType
            
        if ServerType=='azcam':
            reply=self.SendImageFileToAzCamImageServer(Filename,self.RemoteImageServerHost,self.RemoteImageServerPort)
        elif ServerType=='lbtguider':
            reply=self.SendImageFileToLBTGuider(Filename,self.RemoteImageServerHost,self.RemoteImageServerPort)
        elif ServerType=='mmtguider':
            reply=self.SendImageFileToMMTGuider(Filename,self.RemoteImageServerHost,self.RemoteImageServerPort)
        elif ServerType=='ccdacq':
            reply=self.SendImageFileToCCDacq(self.RemoteImageServerHost,self.RemoteImageServerPort)
        elif ServerType=='dataserver':
            reply=self.SendImageFileToDataServer(Filename,self.RemoteImageServerHost,self.RemoteImageServerPort)
        else:
            reply=[Globals.ERROR,'unknown remote image server type']

        return reply
    
    def SendImageFileToAzCamImageServer(self,Filename,RemoteImageServerHost,RemoteImageServerPort):
        """
        Send image to AzCam image server.    
        """

        # open image file on disk
        dfile = open(Filename,'rb')	
        if not dfile:
            return [Globals.ERROR,'could not open image file']

        # get file size
        lSize=os.path.getsize(Filename)

        # read the file into the buffer
        buff=dfile.read()

        # close the file
        dfile.close()

        # open socket to DataServer
        DataServerSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        DataServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,0)
        DataServerSocket.settimeout(10.)
        try:
            DataServerSocket.connect((RemoteImageServerHost,int(RemoteImageServerPort)))
        except Exception,message:
            DataServerSocket.close()
            return [Globals.ERROR,'remote ImageServer socket not opened: %s' % message]	

        if self.RemoteImageFileName!='':
            remotefile=self.RemoteImageFileName
        else:
            remotefile=self.image.filename.GetName()[1]
            if self.image.filename.Overwrite or self.image.filename.TestImage:
                remotefile='!'+remotefile
        Print('Sending image to %s as %s' % (RemoteImageServerHost,remotefile))

        # send header
        # file types: 0 FITS, 1 MEF, 2 binary
        s1='%16d %s %d %d %d %d' % (lSize,remotefile,self.image.FileType,
                                    self.image.SizeX,self.image.SizeY,self.DisplayImage)
        s1='%-256s' % s1
        status=DataServerSocket.send(s1)
        if status != 256:
            return[Globals.ERROR,'could not send image header to remote ImageServer']

        # get 16 char ASCII header return status from image server
        #reply = DataServerSocket.recv(16)
        #if len(reply) != 16:
        #    return [Globals.ERROR,'did not receive header return status from remote ImageServer']
        #retstat=int(reply[:1])
        #retstat=int(reply)
        retstat=0

        # check header return status codes
        if retstat != 0:
            if retstat==-1:
                return [Globals.ERROR,'bad reply from remote ImageServer']
            elif retstat==-2:
                return [Globals.ERROR,'remote ImageServer not create image filename']
            elif retstat==-3:  # 
                return [Globals.ERROR,'folder does not exist on remote machine']
            else:
                return [Globals.ERROR,'unknown error from remote ImageServer']

        # send file data
        try:
            reply=DataServerSocket.send(buff)
        except:
            return [Globals.ERROR,'did not send image file data to remote ImageServer']

        if reply!=len(buff):
            return [Globals.ERROR,'did not send entire image file data to remote ImageServer']

        # get 16 char ASCII final return status from image server
        try:
            reply = DataServerSocket.recv(16)
        except:
            return [Globals.ERROR,'did not receive return status from remote ImageServer']

        if len(reply)!=2:
            return [Globals.ERROR,'did not receive entire return status from remote ImageServer']

        retstat=int(reply[:1])

        # check final return status error codes
        if retstat != 0:
            return [Globals.ERROR,'bad final return status from remote ImageServer']

        # close socket
        #time.sleep()
        DataServerSocket.close()

        Print('Finished sending image')

        return [Globals.OK]

    def SendImageFileToDataServer(self,Filename,RemoteImageServerHost,RemoteImageServerPort):
        """
        Send image to Jeff Fookson's data server.    
        """

        # open image file on disk
        dfile = open(Filename,'rb')	
        if not dfile:
            return [Globals.ERROR,'could not open local image file']

        # get file size
        lSize=os.path.getsize(Filename)

        # read the file into the buffer
        buff=dfile.read()

        # close the file
        dfile.close()

        # open socket to DataServer
        DataServerSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        DataServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,0)
        DataServerSocket.settimeout(10.)
        try:
            DataServerSocket.connect((RemoteImageServerHost,RemoteImageServerPort))
        except Exception,message:
            DataServerSocket.close()
            return [Globals.ERROR,'remote DataServer socket not opened: %s' % message]	

        if self.RemoteImageFileName!='':
            remotefile=self.RemoteImageFileName
        else:
            remotefile=self.image.filename.GetName()[1]
            if self.image.filename.Overwrite or self.image.filename.TestImage:
                remotefile='!'+remotefile
        Print('Sending image to %s as %s' % (RemoteImageServerHost,remotefile))

        # send header
        # file types: 0 FITS, 1 MEF, 2 binary
        s1='%16d %s %d %d %d %d' % (lSize,remotefile,self.image.FileType,
                                    self.image.SizeX,self.image.SizeY,self.DisplayImage)
        s1='%-256s' % s1
        status=DataServerSocket.send(s1)
        if status != 256:
            return[Globals.ERROR,'could not send image header to remote DataServer']

        # get 16 char ASCII header return status from image server
        #reply = DataServerSocket.recv(16)
        #if len(reply) != 16:
        #    return [Globals.ERROR,'did not receive header return status from remote DataServer']
        #retstat=int(reply[:1])
        #retstat=int(reply)
        retstat=0

        # check header return status codes (updated 14jul11)
        if retstat != 0:
            if retstat==1:    # overwrite existing name wihtout flag
                return [Globals.ERROR,'remote DataServer could not create image filename']
            elif retstat==2:  # not enough space
                return [Globals.ERROR,'remote DataServer does not have enough disk space']
            elif retstat==3:  # 
                return [Globals.ERROR,'remote DataServer reports folder does not exist']
            else:
                return [Globals.ERROR,'unknown error from remote DataServer']

        # send file data
        try:
            reply=DataServerSocket.send(buff)
        except:
            return [Globals.ERROR,'did not send image file data to remote DataServer']

        if reply!=len(buff):
            return [Globals.ERROR,'did not send entire image file data to remote DataServer']

        # get 16 char ASCII final return status from image server
        """
        try:
            reply = DataServerSocket.recv(16)
        except:
            return [Globals.ERROR,'did not receive return status from remote ImageServer']

        if len(reply)!=2:
            return [Globals.ERROR,'did not receive entire return status from remote ImageServer']

        retstat=int(reply[:1])

        # check final return status error codes
        if retstat != 0:
            return [Globals.ERROR,'bad final return status from remote ImageServer']
        """

        # close socket
        time.sleep(3)
        DataServerSocket.close()

        Print('Finished sending image')

        return [Globals.OK]

    def SendImageFileToLBTGuider(self,Filename,GuideHost,GuidePort):
        """
        Send image to an LBT guider image server.
        """

        # open image file on disk
        gfile = open(Filename,'rb')	
        if not gfile:
            return [Globals.ERROR,'could not open local image file']

        # get file size
        lSize=os.path.getsize(Filename)

        # read the file into the buffer and close
        buff=gfile.read()
        gfile.close()

        # open socket to LBT image server
        GuideSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        GuideSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,0)

        try:
            GuideSocket.connect((GuideHost,GuidePort))
        except Exception,message:
            GuideSocket.close()
            return [Globals.ERROR,'LBT guider ImageServer not opened: %s' % message]	

        # send filesize in bytes, \r\n terminated
        sockBuf="%d\r\n" % lSize
        l=len(sockBuf)
        if GuideSocket.send(sockBuf) != len(sockBuf):
            return [Globals.ERROR,'GuideSocket send error']

        # send file data
        if GuideSocket.send(buff) != len(buff):
            return [Globals.ERROR,'could not send all image file data to LBT ImageServer']

        # close socket
        GuideSocket.close()

        return [Globals.OK]    

    def SendImageFileToCCDacq(self,RemoteImageServerHost,RemoteImageServerPort):
        """
        Send raw image data to Skip's ccdacq program.    
        """
        
        # make sure data is valid
        loop=0
        while not self.image.isValid and loop<100:
            loop=+1
            time.sleep(.1)
            if loop>=100:
                Print('ERROR image data not received in time')
        
        # open socket to remote ImageServer
        ImageServerSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        ImageServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,0)
        #ImageServerSocket.settimeout(10.)  # comment this out
        try:
            ImageServerSocket.connect((RemoteImageServerHost,RemoteImageServerPort))
        except Exception,message:
            ImageServerSocket.close()
            return [Globals.ERROR,'remote ImageServer socket not opened: %s' % message]	

        Print('Sending image to %s' % (RemoteImageServerHost))

        # send header
        s1='%d %d\r\n' % (self.image.SizeX,self.image.SizeY)
        status=ImageServerSocket.send(s1)
        if status <=0:
            return[Globals.ERROR,'could not send image header to remote ImageServer']
        
        s1='NoFilename NoImageType\r\n'
        status=ImageServerSocket.send(s1)
        if status <=0:
            return[Globals.ERROR,'could not send image header to remote ImageServer']
        
        # send image data
        if GetObject('focalplane').NumAmpsImage>1:
            self.image.isValid=1   #MIKE
            #reply=self.image.WriteFile('/azcam/systems/maestro/image.fits',1)
            reply=self.image.Assemble(0)
            try:
                reply=ImageServerSocket.send(self.image.Buffer)
            except Exception,Message:
                return [Globals.ERROR,'could not send image data to remote ImageServer:%s' % Message]
        else:
            try:
                reply=ImageServerSocket.send(self.image.Data[0])
            except Exception,Message:
                return [Globals.ERROR,'could not send image data to remote ImageServer:%s' % Message]

        if reply!=(self.image.SizeX*self.image.SizeY)*2:
            return [Globals.ERROR,'did not send entire image to remote ImageServer']
        
        # wait before closing
        try:
            reply = ImageServerSocket.recv(1)
        except Exception,message:
            pass
        
        # close socket
        ImageServerSocket.close()

        Print('Finished sending image')

        return [Globals.OK]
    
    def SendImageFileToMMTGuider(self,Filename,GuideHost,GuidePort):
        """
        Send image to an MMTO guider image server.
        """
        
        # open image file on disk
        gfile = open(Filename,'rb')	
        if not gfile:
            return [Globals.ERROR,'could not open local image file']

        # get file size
        lSize=os.path.getsize(Filename)

        # read the file into the buffer and close
        buff=gfile.read()
        gfile.close()

        # open socket to LBT image server
        GuideSocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        GuideSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,0)

        try:
            GuideSocket.connect((GuideHost,GuidePort))
        except Exception,message:
            GuideSocket.close()
            return [Globals.ERROR,'MMT guider ImageServer not opened: %s' % message]	

        # send filesize in bytes, \r\n terminated
        sockBuf="%d\r\n" % lSize
        l=len(sockBuf)
        if GuideSocket.send(sockBuf) != len(sockBuf):
            return [Globals.ERROR,'GuideSocket send error']

        # send file data
        if GuideSocket.send(buff) != len(buff):
            return [Globals.ERROR,'could not send all image file data to MMT ImageServer']

        # close socket
        GuideSocket.close()

        return [Globals.OK]  
    