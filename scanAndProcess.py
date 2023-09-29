#------------------------------------------------------------------------------------------
#
# scanAndProcess.py
#
# Main processing loop for the CTD processor, and associated methods.
#
#------------------------------------------------------------------------------------------

import sys, ftplib, os, logging, time, socket, pysftp
from ctd2kkyy import ctd2kkyy
from regexes import *
from bottomDO import writeBottomDO

MAX_RETRIES = 5  #  Maximum number of times to re-attempt interactions with the FTP servers on error
lines = None

#------------------------------------------------------------------------------------------

def getSleepInterval(collectionInterval, offset=0):
    """
    Description:  Based on some collection interval and (optional) offset, calculate the
                  amount of time to sleep until the next collection run.  Used when running
                  in daemon mode.
    Input:        collectionInterval:  <int>  the collection interval, expressed in seconds.  Typically one hour.
                  offset:              <int>  (optional) offset from 'collectionInterval' when the application should
                                              run, expressed in seconds.
    Return Value: A 2-tuple, (next scheduled awakening, number of seconds the application will sleep).
    """

    now = time.time()
    then = now - (now % collectionInterval) + collectionInterval + offset
    while then - now < 0.0:
       then += collectionInterval

    return then, then - now

#------------------------------------------------------------------------------------------

def readTheCredentialsFile(credFile):
    """ 
    Description:   Read FTP credentials from the vaulted credentials file.  The file is a
                   plain text file containing colon-delimited key-value pairs.
    Input:         credFile:  <str>  Full path to the credentials file.
    Return Value:  A Dictionary containing the key-value pairs from the credentials file.
    """

    retval = {}
    try:
        fp = open(credFile, 'r')
        for line in fp:
            tokens = [x.strip() for x in line.split(':')]
            retval[tokens[0]] = tokens[1]
        fp.close()
    except IOError, msg:
        logging.critical('Unable to open credentials file: %s Exiting...'%str(msg))
        sys.exit(-1)

    return retval

#---------------------------------------------------------------------------------------------

def ftp_retrlines_callback(line):
    """
    Description:  Callback method for ftplib.retlines()
    """

    global lines
    if len(line.strip()) > 1:
        lines.append(line)

#---------------------------------------------------------------------------------------------

def getFTPInfo(options, config):
    """
    Description:    Build a dictionary of FTP connection parameters from the config file.
    Input:          config: <ConfigParser object>
    Return Value:   Dictionary with keys 'NCDDC' and 'NDBC'
    """

    retval = {'NCDDC':dict(config.items('NCDDC-ftp')), 'NDBC':dict(config.items('NDBC-ftp'))}
    if not options.dry_run:
        creds = readTheCredentialsFile(retval['NDBC']['credFile'])
        retval['NDBC'].update({'user':creds['NDBC-FTP-Username'], 'pw':creds['NDBC-FTP-Password']})

    return retval
    
#---------------------------------------------------------------------------------------------

def scanForNewFiles(ftpSrvr, ftpRootDir, processedFiles):
    """
    Description:    Scan the STP server for any new files deposited since the last run.
    Input:          ftpSrvr:         <obj>    pysftp.Connection object.
                    ftpRootDir:      <string> Folder to begin scanning.
                    processedFiles:  <list>   List of files already processed.
    Return Value:   List of new files (full path).
    """

    retval = []

    if ftpRootDir:
        logging.debug('Changing directory to %s.'%ftpRootDir)
        ftpSrvr.cwd(ftpRootDir)
    #for fileName in ftpSrvr.listdir():
    for fileName in ftpSrvr.nlst():
        logging.debug(' %s'%fileName)
        if 'do_not_use' not in fileName.lower() and \
           ctdFilenamePattern.match(fileName) and \
           fileName not in processedFiles:
               retval.append(fileName)
    return retval

#---------------------------------------------------------------------------------------------

def scanAndProcess(options, config):
    """
    Description:  Scan the SFTP server for new files and process them.
    Input:        options:  <obj>  A Python OptionParser object.
                  config:   <obj>  A Python ConfigParser object.
    Return Value: None.
    """

    global lines
    #
    # Collect and log some config parameters.
    #
    offset = int(config.get('globals','offset'))
    collectionInterval = int(config.get('globals','collectionInterval'))
    boundingBox = [float(x.strip()) for x in config.get('globals','boundingBox').split(',')]
    dataFileDir = config.get('globals','dataFileDir')

    logging.info('Collection interval is %d seconds.'%collectionInterval)
    logging.info('Offset is %d seconds.'%offset)
    logging.info('Bounding box is %s'%`boundingBox`)
    #
    # Create our local data directory if necessary.
    #
    if not os.path.exists(dataFileDir):
        logging.info('Creating data directory %s.'%dataFileDir)
        os.mkdir(dataFileDir)
    #
    # Get FTP/SFTP connection info.
    #
    ftpInfo = getFTPInfo(options, config)
    logging.info('Data source is %s.'%ftpInfo['NCDDC']['host'])
    logging.info('Data destination is %s.'%ftpInfo['NDBC']['host'])
    #
    # Repeat until spanked.  If 'exit_when_done' is set, we'll break out of this loop
    # at the bottom.
    #
    while True:
        #
        # Read list of previously-processed files (if any)
        #
        try:
            processedFiles = [x.strip() for x in open('%s/processedFiles.txt'%dataFileDir,'r').readlines()]
        except IOError:
            processedFiles = []

        ftpError = True
        loopCtr = 0
        while ftpError and loopCtr < MAX_RETRIES:
            loopCtr += 1
            ftpError = False
            try:
                #
                #ftpNCDDC = pysftp.Connection(ftpInfo['NCDDC']['host'],
                #                             ftpInfo['NCDDC']['user'],
                #                             ftpInfo['NCDDC']['keyfile'])
                #
                ftpNCDDC = ftplib.FTP(ftpInfo['NCDDC']['host'],
                                      ftpInfo['NCDDC']['user'],
                                      ftpInfo['NCDDC']['pw'])
                ftpRootDir = ftpInfo['NCDDC']['dir']
                #
                # Look for any new files since last run
                #
                newFileNames = scanForNewFiles(ftpNCDDC, ftpRootDir, processedFiles)
                if newFileNames:
                    try:
                        if not options.dry_run:
                            ftpNDBC = ftplib.FTP(ftpInfo['NDBC']['host'],
                                                 ftpInfo['NDBC']['user'],
                                                 ftpInfo['NDBC']['pw'])
                        for fileName in newFileNames:
                            logging.info('Downloading file %s.'%fileName)
                            #
                            # Extract the callsign and DTG from the filename, use those to create a
                            # folder structure for this file
                            # 
                            callSign = ctdCallsignPattern.match(fileName).group()
                            dtg = ctdDateTimeGroupPattern.search(fileName).group()
                            ctdFileDir = os.path.join(dataFileDir, callSign, dtg[:8])
                            if not os.path.exists(ctdFileDir):
                                os.makedirs(ctdFileDir)
                            ctdFilePath = os.path.join(ctdFileDir, fileName)
                            #
                            # Get the file from NCEI's SFTP server and write it to disk
                            #
                            #ftpNCDDC.get(fileName, ctdFilePath, preserve_mtime=True)
                            
                            lines = []
                            ftpNCDDC.retrlines('RETR %s'%fileName, ftp_retrlines_callback)
                            open(ctdFilePath, 'w').write('\n'.join(lines))
                            #
                            # Convert to KKYY
                            #
                            kkyyFilePath = os.path.join(ctdFileDir,'%s_out.txt'%os.path.splitext(fileName)[0])
                            if ctd2kkyy(ctdFilePath, kkyyFilePath, boundingBox, callSign):
                                writeBottomDO(ctdFilePath, dataFileDir)
                                #
                                # Upload to NDBC
                                # 
                                if not options.dry_run:
                                    fp = open(kkyyFilePath, 'r')
                                    logging.info('Uploading %s.'%kkyyFilePath)
                                    storcmd = 'STOR %s'%(os.path.split(kkyyFilePath)[1])
                                    ftpNDBC.storlines(storcmd, fp)
                                    fp.close()
                                    #
                                    # Log this file as having been processed
                                    #
                                    open('%s/processedFiles.txt'%dataFileDir,'a').write('%s\n'%fileName)
                            else:
                                logging.warning('ctd2kkyy encountered an error in %s'%fileName)
                        #
                        # Disconnect until next time
                        #
                        if not options.dry_run:
                           ftpNDBC.quit()

                    except socket.gaierror, msg:
                        logging.warning('Socket error: %s'%str(msg))
                        logging.warning('Will retry %d more times.'%(MAX_RETRIES - loopCtr))
                        ftpError = True
                        time.sleep(5)
                    except ftplib.all_errors, msg:
                        logging.warning('FTP error (NDBC): %s'%str(msg))
                        logging.warning('Will retry %d more times.'%(MAX_RETRIES - loopCtr))
                        ftpError = True
                        time.sleep(5)
                else:
                    logging.info('No new files detected.')
                #
                # Disconnect until next time
                #
                #ftpNCDDC.close()
                ftpNCDDC.quit()

            except socket.gaierror, msg:
                logging.warning('Socket error: %s'%str(msg))
                logging.warning('Will retry %d more times.'%(MAX_RETRIES - loopCtr))
                ftpError = True
                time.sleep(5)
            except ftplib.all_errors, msg:
                logging.warning('FTP error (NCEI): %s'%str(msg))
                logging.warning('Will retry %d more times.'%(MAX_RETRIES - loopCtr))
                ftpError = True
                time.sleep(5)
            except (pysftp.ConnectionException, 
                    pysftp.CredentialException, 
                    pysftp.SSHException,
                    pysftp.AuthenticationException,
                    pysftp.HostKeysException), msg:
                logging.warning('SFTP error (NCEI): %s'%str(msg))
                logging.warning('Will retry %d more times.'%(MAX_RETRIES - loopCtr))
                ftpError = True
                time.sleep(5)

        if options.exit_when_done:
            sys.exit(0)
        else:
            #
            # Calculate sleep interval, log it, sleep
            #
            then, delta = getSleepInterval(collectionInterval, offset)
            logging.info('Sleeping until %s (%f secs).'%(time.asctime(time.localtime(then)), delta))
            time.sleep(delta)
