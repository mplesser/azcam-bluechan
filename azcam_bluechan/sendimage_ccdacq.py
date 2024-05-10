import socket

import azcam
import azcam.exceptions


def sendimage_ccdacq(self, localfile, remotefile=None):
    """
    Send raw image data to cccdacq (ICE) application.
    """

    # open socket to remote image server
    ccdacqsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ccdacqsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)

    try:
        ccdacqsocket.connect(
            (self.remote_imageserver_host, self.remote_imageserver_port)
        )
    except Exception as message:
        ccdacqsocket.close()
        raise azcam.exceptions.AzcamError(f"ccdacq image server not opened: {message}")

    # send header
    s1 = "%d %d\r\n" % (self.size_x, self.size_y)
    if ccdacqsocket.send(str.encode(s1)) != len(s1):
        raise azcam.exceptions.AzcamError(f"socket send error header1")

    s1 = "NoFilename NoImageType\r\n"
    if ccdacqsocket.send(str.encode(s1)) != len(s1):
        raise azcam.exceptions.AzcamError(f"socket send error header2")

    # send file data
    buff = azcam.db.tools["exposure"].image.data[0]
    numsent = ccdacqsocket.send(buff)
    if numsent != 2 * len(buff):
        raise azcam.exceptions.AzcamError(
            f"Could not send all image data to ccdacq server"
        )

    # wait before closing
    try:
        reply = ccdacqsocket.recv(1)
    except Exception as e:
        pass

    # close socket
    ccdacqsocket.close()

    return
