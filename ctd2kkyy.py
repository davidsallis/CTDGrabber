#-----------------------------------------------------------------------------
#
# ctd2kkyy.py
#    Drives CTDParser and writes KKYY-format CTD data to an external disk file.
#
#-----------------------------------------------------------------------------
import sys, time, os, logging
from CTDParser import CTDParser

def ctd2kkyy(inFileName, outFileName, boundingBox, callSign):
    """
    Description:    Drives CTDParser and creates KKYY format files from Seabird CTD data files.
    Input:          inFileName:     <string> Name of the Seabird CTD data file
                    outFileName:    <string> Name of file to write to disk
                    boundingBox:    <list>   Min/max lat/lon pairs for validation
                    callSign:       <string> Ship callsign, appended to end of KKYY file.
    Output:         KKYY format file.
    Return Value:   <boolean>  True if successful, False if there are errors.
    """

    retval = False
    try:
        #
        # Instantiate the CTD Parser and parse the header.  If that worked, keep going.
        #
        p = CTDParser(inFileName, boundingBox)
        if p.parseHeader():
            p.setQuadrant() 
            #
            # KKYY data lines
            #
            kkyyDataLineList = ['%d %d %d'%item for item in p.getData()]
            if kkyyDataLineList:
                #
                # Length of dataLineList should be sames as nDataLines; if not log a warning.
                #
                if len(kkyyDataLineList) != p.nDataLines:
                    logging.warning('Number of data lines in file != number of data lines in header (got %d, expected %d)'%(len(kkyyDataLineList), p.nDataLines))
                try:
                    #
                    # Build the KKYY header, then open the file and write out the entire message.
                    #
	            kkyyHeader = 'KKYY %s %s/ %s%s %s 88872 83099'%(p.date, 
                                                                    p.time,
                                                                    p.quadrant,
                                                                    p.lat,
                                                                    p.lon)
                    logging.info('Writing %s'%outFileName)
                    open(outFileName, 'w').write('%s\n%s\n99999 %s\n'%(kkyyHeader, '\n'.join(kkyyDataLineList), callSign))
                    retval = True
                except IOError, msg:
                    logging.critical('Unable to open %s for output: %s'%(outFileName, str(msg)))
            else:
                logging.warning('No data lines present.')

        else:
            logging.critical('parseHeader() returned an error.')
    except IOError, msg:
        logging.critical('Unable to open %s for input: %s'%(inFileName, str(msg)))

    return retval
