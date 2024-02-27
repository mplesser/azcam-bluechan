# azcamserver config file for bluechan

import os
import sys

import azcam
import azcam_server.server
import azcam_server.shortcuts
from azcam_server.cmdserver import CommandServer
from azcam.header import System
from azcam_server.tools.arc.controller_arc import ControllerArc
from azcam_server.tools.arc.exposure_arc import ExposureArc
from azcam_server.tools.arc.tempcon_arc import TempConArc
from azcam_server.tools.ds9display import Ds9Display
from azcam_server.tools.sendimage import SendImage
from azcam_server.tools.instrument import Instrument
from azcam_server.tools.telescope import Telescope
from azcam_server.tools.webserver.fastapi_server import WebServer
from azcam_server.tools.webtools.status.status import Status

from azcam_server.monitor.monitorinterface import AzCamMonitorInterface
from azcam_bluechan.ccdacq import CCDACQ

# ****************************************************************
# parse command line arguments
# ****************************************************************
try:
    i = sys.argv.index("-system")
    option = sys.argv[i + 1]
except ValueError:
    option = "menu"
try:
    i = sys.argv.index("-datafolder")
    datafolder = sys.argv[i + 1]
except ValueError:
    datafolder = None
try:
    i = sys.argv.index("-lab")
    lab = 1
except ValueError:
    lab = 0

# ****************************************************************
# configuration menu
# ****************************************************************
menu_options = {
    "bluechan standard mode": "bluechan",
}
if option == "menu":
    option = azcam.utils.show_menu(menu_options)

# ****************************************************************
# define folders for system
# ****************************************************************
azcam.db.systemname = "bluechan"

azcam.db.systemfolder = os.path.dirname(__file__)
azcam.db.systemfolder = azcam.utils.fix_path(azcam.db.systemfolder)

if datafolder is None:
    droot = os.environ.get("AZCAM_DATAROOT")
    if droot is None:
        droot = "/data"
    azcam.db.datafolder = os.path.join(droot, azcam.db.systemname)
else:
    azcam.db.datafolder = datafolder
azcam.db.datafolder = azcam.utils.fix_path(azcam.db.datafolder)

parfile = os.path.join(
    azcam.db.datafolder, "parameters", f"parameters_server_{azcam.db.systemname}.ini"
)

# ****************************************************************
# enable logging
# ****************************************************************
logfile = os.path.join(azcam.db.datafolder, "logs", "server.log")
azcam.db.logger.start_logging(logfile=logfile)
azcam.log(f"Configuring for {option}")

# ****************************************************************
# configure system options
# ****************************************************************
CSS = 0
RTS2 = 0
NORMAL = 0
template = os.path.join(azcam.db.datafolder, "templates", "fits_template_bluechan.txt")
parfile = os.path.join(
    azcam.db.datafolder, "parameters", "parameters_server_bluechan.ini"
)
NORMAL = 1
cmdport = 2402
azcam.db.servermode = "bluechan"

# ****************************************************************
# controller
# ****************************************************************
controller = ControllerArc()
controller.timing_board = "gen1"
controller.clock_boards = ["gen1"]
controller.video_boards = ["gen1"]
controller.utility_board = "gen1"
controller.set_boards()
controller.pci_file = os.path.join(azcam.db.datafolder, "dspcode", "dsppci", "pci1.lod")
controller.timing_file = os.path.join(
    azcam.db.datafolder, "dspcode", "dsptiming", "tim1_config3.lod"
)
controller.utility_file = os.path.join(
    azcam.db.datafolder, "dspcode", "dsputility/util1.lod"
)
controller.video_gain = 1
controller.video_speed = 1
if lab:
    controller.camserver.set_server("localhost", 2405)
    # controller.camserver.set_server("conserver7", 2405)
else:
    controller.camserver.set_server("localhost", 2405)

# ****************************************************************
# temperature controller
# ****************************************************************
tempcon = TempConArc()
tempcon.control_temperature = -135.0
tempcon.set_calibrations([1, 1, 3])

# ****************************************************************
# exposure
# ****************************************************************
exposure = ExposureArc()
remote_imageserver_port = 6543
sendimage = SendImage()
exposure.send_image = 1
remote_imageserver_host = "pixel2"
imagefolder = "/data/bluechan"
azcam.db.servermode = "bluechan"
sendimage.set_remote_imageserver(
    remote_imageserver_host, remote_imageserver_port, "ccdacq"
)
exposure.filetype = exposure.filetypes["FITS"]
exposure.image.filetype = exposure.filetypes["FITS"]
exposure.display_image = 0
exposure.folder = imagefolder
exposure.send_image = 0

# ****************************************************************
# detector
# ****************************************************************
detector_bluechan = {
    "name": "STA0520",
    "description": "STA0520A CCD",
    "ref_pixel": [1344, 256],
    "format": [2688, 16, 0, 20, 512, 0, 0, 0, 0],
    "focalplane": [1, 1, 1, 1, "0"],
    "roi": [1, 2688, 1, 512, 1, 1],
    "extension_position": [[1, 1]],
    "jpg_order": [1],
    "extname": ["im1"],
    "extnum": [1],
    "detnum": [1],
    "detpos": [[1, 1]],
    "detgap": [[0.0, 0.0]],
    "amp_position": [[1, 1]],
    "amp_pixel_position": [[1, 1]],
    "ctype": ["LINEAR", "LINEAR"],
}
exposure.set_detpars(detector_bluechan)

# ****************************************************************
# instrument
# ****************************************************************
instrument = Instrument()
instrument.enabled = 0

# ****************************************************************
# telescope
# ****************************************************************
telescope = Telescope()
telescope.enabled = 0

# ****************************************************************
# system header template
# ****************************************************************
system = System("bluechan", template)
system.set_keyword("DEWAR", "BlueChanDewar", "Dewar name")

# ****************************************************************
# display
# ****************************************************************
display = Ds9Display()

# ****************************************************************
# ccdacq commands
# ****************************************************************
ccdacq = CCDACQ()
azcam.db.tools["ccdacq"] = ccdacq

# ****************************************************************
# read par file
# ****************************************************************
azcam.db.parameters.read_parfile(parfile)
azcam.db.parameters.update_pars("azcamserver")

# ****************************************************************
# define and start command server
# ****************************************************************
cmdserver = CommandServer()
cmdserver.port = cmdport
cmdserver.case_insensitive = 1
azcam.log(f"Starting cmdserver - listening on port {cmdserver.port}")
# cmdserver.welcome_message = "Welcome - azcam-itl server"
cmdserver.start()
azcam.db.default_tool = "ccdacq"

# ****************************************************************
# web server
# ****************************************************************
webserver = WebServer()
webserver.port = 2403  # common port for all configurations
webserver.index = os.path.join(azcam.db.systemfolder, "index_bluechan.html")
webserver.start()
webstatus = Status()
webstatus.initialize()

# ****************************************************************
# GUIs
# ****************************************************************
if 1:
    import azcam_bluechan.start_azcamtool

# ****************************************************************
# finish
# ****************************************************************
azcam.log("Configuration complete")
