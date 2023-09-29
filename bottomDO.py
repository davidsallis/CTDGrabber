#---------------------------------------------------------------
#
# bottomDO.py
#
# Write bottom dissolved oxygen from a SeaBird 9 CTD data file
# into a CSV file for use by Hypoxia Watch.
#
#---------------------------------------------------------------

import csv, time, os, logging
from CTDParser import CTDParser
from regexes import *

#---------------------------------------------------------------

def writeBottomDO(ctdFilePath, dataFileDir):
    """ """

    ctdFileName = os.path.split(ctdFilePath)[1]
    callsign = ctdCallsignPattern.match(ctdFileName).group()
    dtg = ctdDateTimeGroupPattern.search(ctdFileName).group()
    DOFileName = 'HypoxiaWatch_%s_%s.dat'%(callsign, dtg[:6])
    p = CTDParser(ctdFilePath)
    p.parseHeader()
    for depth, temp, salinity, oxygen in p.getData(format='not_kkyy'):
        continue
    try:
        if oxygen is not None:
            DOFileName = os.path.join(dataFileDir, DOFileName)
            logging.debug('DO file name is %s'%`DOFileName`)
            needHeader = not os.path.exists(DOFileName)
            try:
                fp = open(DOFileName, 'a')
                writer = csv.writer(fp)
                if needHeader:
                    writer.writerow(['Ship','Cruise','DateUTC','TimeUTC','Station','Cast','Longitude','Latitude','WaterDepthM','SampleDepthM','OxMgL'])
                dateUTC = time.strftime('%d%b%Y',time.gmtime(p.epoch)).upper()
                timeUTC = time.strftime('%H:%M:%S', time.gmtime(p.epoch))
                writer.writerow([p.ship,
                                 p.cruise,
                                 dateUTC,
                                 timeUTC,
                                 p.station,
                                 p.cast,
                                 '%.6f'%p.flon,
                                 '%.6f'%p.flat,
                                 p.depth,
                                 depth,
                                 oxygen])
                fp.close()
            except IOError, msg:
                 logging.warning('Error opening %s for output: %s'%(DOFileName, str(msg)))
    except UnboundLocalError, msg:
        logging.warning('UnboundLocalError: %s'%str(msg))

#---------------------------------------------------------------

if __name__ == '__main__':
   import sys 
   writeBottomDO(sys.argv[1], sys.argv[2])
