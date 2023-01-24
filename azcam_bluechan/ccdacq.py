"""
Contains the ICE class for MMTO Blue Channel commands under ICE.
"""

import time

import azcam

"""
    ** Get camtemp
    ** Get dewtemp
    ** Get utc-obs (only after an exposure as reads header)
    ** Get pixelcount

    ** Set ReadOutMode wait
    ** Set ShutterState

    ** SetFormat
    ** SetConfiguration
    ** SetROI
    ** SetGainSpeed
    ** SetExposure

    ** StartExposure 0
    ** ReadExposure
    ** PauseExposure
    ** ResumeExposure
    ** AbortExposure

    ** SendImage 3
    ** ReadImage 0

    ** ClearArray
    ** CloseConnection
    ** Reset
    ** ParShift

    *** OLD ***
    setparameter
"""


class CCDACQ(object):
    """
    Class definition for MMT Blue Channel commands under ccdacq.
    These methods are called remotely thorugh the command server
    with syntax such as:
    ccdacq.expose 1.0 "zero" "/home/obs/a.001.fits" "some image title".
    """

    def __init__(self):
        """
        Creates ccdacq tool.
        """

        azcam.db.tools["ccdacq"] = self

        self.imagetype = "dark"  # shutter state for exposure
        self.status = "OK"

        return

    def expose(self, flag, exposuretime, filename):
        """
        Make a complete exposure.
        flag is ignored.
        exposuretime is the exposure time in seconds
        filename is remote filename (do not use periods)
        """

        azcam.db.parameters.set_par("imagetest", 0)
        azcam.db.parameters.set_par("imageautoname", 0)
        azcam.db.parameters.set_par("imageincludesequencenumber", 0)
        azcam.db.parameters.set_par("imageautoincrementsequencenumber", 0)

        azcam.db.tools["exposure"].set_filename(filename)
        azcam.db.tools["exposure"].expose(
            exposuretime, self.imagetype, "ccdacq image"
        )

        return self.status

    def expose1(self, flag, exposuretime, filename):
        """
        Make a complete exposure, returning immediately after start.
        flag is ignored.
        exposuretime is the exposure time in seconds
        filename is remote filename (do not use periods)
        """

        azcam.db.parameters.set_par("imagetest", 0)
        azcam.db.parameters.set_par("imageautoname", 0)
        azcam.db.parameters.set_par("imageincludesequencenumber", 0)
        azcam.db.parameters.set_par("imageautoincrementsequencenumber", 0)

        azcam.db.tools["exposure"].set_filename(filename)
        azcam.db.tools["exposure"].expose1(
            exposuretime, self.imagetype, "ccdacq image"
        )

        return self.status

    def reset(self):
        azcam.db.tools["exposure"].reset()
        return self.status

    def readimage(self,flag=-1):
        azcam.db.tools["exposure"].dark_time = time.time() - azcam.db.tools["exposure"].dark_time_start
        azcam.db.tools["exposure"].readout()
        azcam.db.tools["exposure"].end()
        return self.status

    def abortexposure(self):
        azcam.db.tools["exposure"].abort()
        return self.status

    def pauseexposure(self):
        azcam.db.tools["exposure"].pause()
        return self.status

    def resumeexposure(self):
        azcam.db.tools["exposure"].resume()
        return self.status

    def cleararray(self):
        azcam.db.tools["exposure"].flush()
        return self.status

    def parshift(self, rows):
        rows = int(rows)
        azcam.db.tools["exposure"].parshift(rows)
        return self.status

    def get(self, attribute):

        if attribute == "camtemp":
            temp = azcam.db.tools["tempcon"].get_temperatures()[0]
            reply = temp
        elif attribute == "dewtemp":
            temp = azcam.db.tools["tempcon"].get_temperatures()[1]
            reply = temp
        elif attribute == "pixelcount":
            count = azcam.db.tools["exposure"].get_pixels_remaining()
            reply = azcam.db.tools["exposure"].image.focalplane.numpix_image - count
        elif attribute == "utc-obs":
            reply = azcam.db.tools["exposure"].header.get_keyword("UTC-OBS")[0]
        else:
            reply = self.status

        return reply

    def set(self, attribute, value):

        if attribute == "readoutmode":  # ignored
            pass
        elif attribute == "shutterstate":
            if value == "open":
                self.imagetype = "object"
            else:
                self.imagetype = "dark"
        return self.status

    def setexposure(self, exposure_time):
        et = float(exposure_time) / 1000.0  #  msec to sec
        azcam.db.tools["exposure"].set_exposuretime(et)
        return self.status

    def readexposure(self):
        etr = azcam.db.tools["exposure"].get_exposuretime_remaining()
        et = max(0, int(etr * 1000) - 3)  #  sec to msec
        reply =  int(azcam.db.tools["exposure"].exposure_time*1000.) - et
        return reply

    def setformat(
        self,
        ns_total=-1,
        ns_predark=-1,
        ns_underscan=-1,
        ns_overscan=-1,
        np_total=-1,
        np_predark=-1,
        np_underscan=-1,
        np_overscan=-1,
        np_frametransfer=-1,
    ):

        azcam.db.tools["exposure"].set_format(
            int(ns_total),
            int(ns_predark),
            int(ns_underscan),
            int(ns_overscan),
            int(np_total),
            int(np_predark),
            int(np_underscan),
            int(np_overscan),
            int(np_frametransfer),
        )

        return self.status

    def setconfiguration(
        self, numdet_x=-1, numdet_y=-1, numamps_x=-1, numamps_y=-1, amp_config=""
    ):

        azcam.db.tools["exposure"].set_focalplane(
            1, 1, 1, 1, "0"
        )

        return self.status

    def setroi(
        self,
        first_col=-1,
        last_col=-1,
        first_row=-1,
        last_row=-1,
        col_bin=-1,
        row_bin=-1,
    ):

        azcam.db.tools["exposure"].set_roi(
            int(first_col),
            int(last_col),
            int(first_row),
            int(last_row),
            int(col_bin),
            int(row_bin),
        )

        return self.status

    def setgainspeed(self, gain, speed):
        gain = int(gain)
        azcam.db.tools["controller"].set_video_gain(gain)
        # azcam.db.tools["controller"].set_video_speed(speed)
        return self.status

    def closeconnection(self):
        """not supported"""
        azcam.log("closeconnection command not supported")
        return self.status

    def sendimage(self, flag, host, port):
        azcam.db.tools["sendimage"].set_remote_imageserver(host, int(port),"ccdacq")
        localfile = azcam.db.tools["exposure"].get_filename()
        azcam.db.tools["sendimage"].send_image(localfile)
        return self.status

    def setparameter(self, keyword, value, comment):
        azcam.db.tools["exposure"].set_keyword(keyword, value, comment)
        return self.status

    def startexposure_wait(self,flag=-1):
        azcam.db.tools["exposure"].test_image=1
        azcam.db.tools["exposure"].begin(-1,self.imagetype)
        azcam.db.tools["exposure"].integrate()
        return self.status

    def startexposure(self,flag=-1):
        exposure = azcam.db.tools["exposure"]

        exposure.test_image=1
        exposure.begin(-1,self.imagetype)

        # below is for immediate return
        exposure.exposure_flag = exposure.exposureflags["EXPOSING"]
        exposure.dark_time_start = time.time()
        azcam.db.tools["controller"].start_exposure()

        return self.status
