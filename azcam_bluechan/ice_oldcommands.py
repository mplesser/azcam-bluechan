"""
Contains the ICE class for MMTO Blue Channel commands under ICE.
"""

import azcam

"""
    reset
    resetcontroller
    abort
    cleararray
    abortexposure
    getdetpars
    get version
    get cameratype
    get servername
    get vispixels
    setexposure
    setroi
    getpixelcount
    gettemp
    readtemperature
    closeconnection
    setsocket
    setsyntheticimage
    setparameter
    guide
    expose
    expose1
    resetserver
    readexposure
"""


class ICE(object):
    """
    Class definition for MMT Blue Channel commands under ICE.
    These methods are called remotely thorugh the command server
    with syntax such as:
    ice.expose 1.0 "zero" "/home/obs/a.001.fits" "some image title".
    """

    def __init__(self):
        """
        Creates ice tool.
        """

        azcam.db.tools["ice"] = self

        self.status = "OK"

        return

    def expose(self, flag, exposuretime, filename):
        """
        Make a complete exposure.
        flag is ignored.
        exposuretime is the exposure time in seconds
        filename is remote filename (do not use periods)
        """

        azcam.db.tools["parameters"].set_par("imagetest", 0)
        azcam.db.tools["parameters"].set_par("imageautoname", 0)
        azcam.db.tools["parameters"].set_par("imageincludesequencenumber", 0)
        azcam.db.tools["parameters"].set_par("imageautoincrementsequencenumber", 0)

        azcam.db.tools["exposure"].set_filename(filename)
        azcam.db.tools["exposure"].expose(exposuretime, "object", "ICE image")

        return self.status

    def expose1(self, flag, exposuretime, filename):
        """
        Make a complete exposure, returning immediately after start.
        flag is ignored.
        exposuretime is the exposure time in seconds
        filename is remote filename (do not use periods)
        """

        azcam.db.tools["parameters"].set_par("imagetest", 0)
        azcam.db.tools["parameters"].set_par("imageautoname", 0)
        azcam.db.tools["parameters"].set_par("imageincludesequencenumber", 0)
        azcam.db.tools["parameters"].set_par("imageautoincrementsequencenumber", 0)

        azcam.db.tools["exposure"].set_filename(filename)
        azcam.db.tools["exposure"].expose1(exposuretime, "object", "ICE image")

        return self.status

    def guide(self, flag, number_exposures=1):
        azcam.db.tools["exposure"].guide(number_exposures)
        return self.status

    def reset(self):

        azcam.db.tools["exposure"].reset()

        return self.status

    def resetcontroller(self):
        azcam.db.tools["controller"].reset()
        return self.status

    def abort(self):
        azcam.db.tools["exposure"].abort()
        return self.status

    def abortexposure(self):
        azcam.db.tools["exposure"].abort()
        return self.status

    def cleararray(self):
        azcam.db.tools["exposure"].flush()
        return self.status

    def getdetpars(self):
        nc = azcam.db.tools["exposure"].image.focalplane.numcols_image
        nr = azcam.db.tools["exposure"].image.focalplane.numrows_image
        return self.status, nc, nr

    def get(self, attribute):

        if attribute == "version":
            reply = self.status, azcam.__version__
        elif attribute == "cameratype":
            reply = self.status, azcam.db.tools["controller"].controller_type
        elif attribute == "servername":
            reply = self.status, azcam.db.hostname
        elif attribute == "vispixels":
            nc = azcam.db.tools["exposure"].image.focalplane.numcols_image
            nr = azcam.db.tools["exposure"].image.focalplane.numrows_image
            reply = self.status, nc, nr
        else:
            reply = self.status

        return reply

    def setexposure(self, exposure_time):
        et = exposure_time / 1000.  #  msec to sec
        azcam.db.tools["exposure"].set_exposuretime(et)
        return self.status

    def readexposure(self):
        etr = azcam.db.tools["exposure"].get_exposuretime_remaining()
        et = int(etr * 1000)  #  sec to msec
        return self.status, et

    def set_roi(
        self,
        first_col=-1,
        last_col=-1,
        first_row=-1,
        last_row=-1,
        col_bin=-1,
        row_bin=-1,
    ):

        azcam.db.tools["exposure"].set_roi(
            first_col,
            last_col,
            first_row,
            last_row,
            col_bin,
            row_bin,
        )

        return self.status

    def getpixelcount(self):
        count = azcam.db.tools["exposure"].get_pixels_remaining()
        return self.status, count

    def gettemp(self):
        temp = azcam.db.tools["tempcon"].get_temperatures()[0]
        return self.status, temp

    def readtemperature(self):
        temps = azcam.db.tools["tempcon"].get_temperatures()
        return self.status, temps[0], temps[1]

    def closeconnection(self):
        """not supported"""
        azcam.log("closeconnection command not supported")
        return self.status

    def setsocket(self, flag, host, port=6543):

        if flag == -1:
            azcam.db.tools["sendimage"].set_remote_imageserver()
        else:
            azcam.db.tools["sendimage"].set_remote_imageserver(host, port)
        return self.status

    def setsyntheticimage(self):
        """not supported"""
        azcam.log("setsyntheticimage command not supported")
        return self.status

    def setmode(self):
        """not supported"""
        azcam.log("setmode command not supported")
        return self.status

    def setparameter(self, keyword, value, comment):
        azcam.db.tools["exposure"].set_keyword(keyword, value, comment)
        return self.status

    def resetserver(self):
        azcam.db.tools["controller"].camserver.reset_server()

        return self.status
