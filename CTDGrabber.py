#------------------------------------------------------------------------------------------
#
# CTDGrabber.py
#   Process CTD files from NMFS vessels into KKYY format, upload to NDBC's FTP server.
#
#------------------------------------------------------------------------------------------

import os, logging 
from startup import startup
from scanAndProcess import scanAndProcess

#---------------------------------------------------------------------------------------------

if __name__ == '__main__':
    #
    # Read command-line options and perform other startup tasks.
    #
    options, args, config = startup()
    #
    # Issue startup message.
    #
    pid = os.getpid()
    logging.info('CTDGrabber starting up (pid=%d).'%pid)
    #
    # If in daemon mode, write the process id to an external file.
    #
    if not options.exit_when_done:
        pidFileName = config.get('globals','pidFileName')
        logging.info('PID file is %s.'%pidFileName)
        try:
            open(pidFileName,'w').write('%d'%pid)
        except IOError, msg:
            logging.warning('Unable to write PID to file: %s'%str(msg))
    #
    # Enter the processing loop.
    #
    scanAndProcess(options, config)
