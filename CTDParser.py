#------------------------------------------------------------------------------------------
#
# CTDParser
#
# Sea-Bird SBE 9 parser class for Python.  Generates KKYY format output.
#
# Ref http://www.dfo-mpo.gc.ca/science/data-donnees/gts-smt/codes/tesac-code-eng.html
#
#------------------------------------------------------------------------------------------
import logging, time
import re
#
# Some useful regexes
#
tokenizer = re.compile(r'\S+')
number_regex = re.compile(r'[\+?|\-?]?\d+\.?\d*')
#
# End-of-header flag
#
END_OF_HEADER = '*END*'
#
# Hemispheric multiplication factors for signed lat/lon
#
hmFactors = { 'N' : 1.0, 'S' : -1.0, 'E' : 1.0, 'W' : -1.0 }
#
# Key terms in the header to parse
#   Keys are arbitrary descriptors chosen by me
#   Values are snippets to look for in the header when extracting required data
#     (usu. at the beginning of the line)
#
headerTerms = {'DateTime'     : '* System UpLoad Time =',
               'NMEA Lat'     : '* NMEA Latitude =',
               'NMEA Lon'     : '* NMEA Longitude =',
               'Operator Lat' : '* Latitude',
               'Operator Lon' : '* Longitude',
               'Index'        : '# name',
               'Data Lines'   : '# nvalues',
               'Data Values'  : '# nquan',
               'Ship'         : '** Ship',
               'Cruise'       : '** Cruise',
               'Station'      : '** Station',
               'Depth'        : '** Depth',
               'Cast'         : '** Cast'}
           
#
# Env. parameters we're interested in (indexed by '# name' fields in header)
#
parameters = ['Temperature', 'Depth', 'Salinity', 'Oxygen, SBE 43 [mg/l]']


class CTDParser():

    def __init__(self, filename, boundingBox=[-180.0,-90.0,180.0,90.0]):
        """
        Description:   "Constructor" method.
        Input:         filename:    <string> Path to file being parsed
                       boundingBox: <list>   Bounding box [min_lon, min_lat, max_lon, max_lat]
        Output:        None.
        Return Value:  None, but will log an error and set 'fp' to None if something bad happened.
        """

        try:
            self.fp = open(filename, 'r')
            self.date = None
            self.time = None
            self.epoch = None
            self.lat = None   # KKYY latitude
            self.lon = None   # KKYY longitude
            self.flat = None  # Float latitude
            self.flon = None  # Float longitude
            self.ship = None
            self.cruise = None
            self.station = None
            self.cast = None
            self.depth = None
            self.quadrant = None
            self.ndxTemp = None
            self.ndxDepth = None
            self.ndxSalinity = None
            self.ndxOxygen = None
            self.nDataLines = None
            self.nDataValues = None
            self.min_lon, self.min_lat, self.max_lon, self.max_lat = boundingBox
        except IOError, msg:
	    logging.critical('Unable to open %s for reading: %s'%(filename, str(msg)))
            self.fp = None

#------------------------------------------------------------------------------

    def __del__(self):

        if self.fp and not self.fp.closed:
            self.fp.close()

#------------------------------------------------------------------------------

    def parseHeader(self):
        """
        Description:    Parse the CTD file header and store certain parameter values.
        Input:          None.
        Output:         None.
        Return Value:   Boolean; True if successful and False if not.
        """

        logging.debug('parseHeader()')

        haveParam = {
                     'DATETIME':False,
                     'LATITUDE':False,
                     'LONGITUDE':False,
                     'TEMPERATURE_INDEX':False,
                     'DEPTH_INDEX':False,
                     'SALINITY_INDEX':False,
                     'N_DATA_LINES':False,
                     'N_DATA_VALUES':False,
                    # 'TEMPERATURE_MINMAX':False,
                    # 'DEPTH_MINMAX':False,
                    # 'SALINITY_MINMAX':False,
                    }

        if self.fp:
            self.fp.seek(0)
            for line in self.fp.xreadlines():
                line = line.strip()
                if line.find(END_OF_HEADER) != -1:
                    break
                #
                # Scan the input line, looking for any of our key terms.  When one is found,
                # process as indicated.
                #
                for key in headerTerms:
                    if line.find(headerTerms[key]) != -1:
                        if key == 'DateTime':
                            haveParam['DATETIME'] = self.setDateTime(line)
                        elif key == 'NMEA Lat':
                            haveParam['LATITUDE'] = self.setLatitude(line)
                            if not haveParam['LATITUDE']:
                                logging.info('   (will try to use alternate data line for latitude')
                        elif key == 'NMEA Lon':
                            haveParam['LONGITUDE'] = self.setLongitude(line)
                            if not haveParam['LONGITUDE']:
                                logging.info('   (will try to use alternate data line for longitude')
                        elif key == 'Operator Lat':
                            if not haveParam['LATITUDE']:
                                haveParam['LATITUDE'] = self.setLatitude(line)
                        elif key == 'Operator Lon':
                            if not haveParam['LONGITUDE']:
                                haveParam['LONGITUDE'] = self.setLongitude(line)
                        elif key == 'Index':
                            for parameter in parameters:
                                if line.find(parameter) != -1:
                                    if parameter == 'Temperature':
                                        haveParam['TEMPERATURE_INDEX'] = self.setIntVal('ndxTemp', line)
                                    elif parameter == 'Depth':
                                        haveParam['DEPTH_INDEX'] = self.setIntVal('ndxDepth', line)
                                    elif parameter == 'Salinity':
                                        haveParam['SALINITY_INDEX'] = self.setIntVal('ndxSalinity', line)
                                    elif parameter == 'Oxygen, SBE 43 [mg/l]':
                                        self.setIntVal('ndxOxygen', line)
                        elif key == 'Data Lines':
                            haveParam['N_DATA_LINES'] = self.setIntVal('nDataLines', line)
                        elif key == 'Data Values':
                            haveParam['N_DATA_VALUES'] = self.setIntVal('nDataValues', line)
                        elif key in ['Ship','Cast','Depth','Station','Cruise']:
                            setattr(self, key.lower(), line[line.find(':')+1:].strip())

            logging.debug('Date/Time: %s %s'%(self.date, self.time))
            logging.debug('Latitude: %s'%self.lat)
            logging.debug('Longitude: %s'%self.lon)
            logging.debug('Temp index: %s'%self.ndxTemp)
            logging.debug('Depth index: %s'%self.ndxDepth)
            logging.debug('Salinity index: %s'%self.ndxSalinity)
            logging.debug('Oxygen index: %s'%self.ndxOxygen)
            logging.debug('# data lines: %s'%`self.nDataLines`)
            logging.debug('# data values: %s'%`self.nDataValues`)
        else:
            logging.critical('parseHeader():  No file handle.')

        return reduce(lambda x,y:x and y, haveParam.values())

#------------------------------------------------------------------------------

    def setQuadrant(self):
        """
        Description  : Sets the WMO code for global quadrant based on signed lat/lon.
        Input        : None.
        Output       : None.
        Return Value : None.
        Reference    : http://www.dfo-mpo.gc.ca/science/data-donnees/gts-smt/codes/wmo-omm-eng.html#ct3333
        """

        if self.flat >= 0.0:
            self.quadrant = '1' if self.flon >= 0.0 else '7'
        else:
            self.quadrant = '3' if self.flon >= 0.0 else '5'

#------------------------------------------------------------------------------

    def setDateTime(self, data):
        """
        Description:    Parse the datetime string in the header and store in KKYY format.
        Input:          data: <string> The header line containing the datetime string.
        Output:         None.
        Return Value:   Boolean.
        Discussion:     Data looks like '* System UpLoad Time = May 08 2013 18:35:13'
                        KKYY format is DDMMY for date, HHMM for time
        """

        logging.debug('setDateTime()')
        logging.debug('   data %s'%`data`)
        data = data[data.find('=')+1:].strip()
        tt = time.strptime(data, '%b %d %Y %H:%M:%S')
        self.date = '%2.2d%2.2d%d'%(tt[2], tt[1], tt[0]%10)
	self.time = '%2.2d%2.2d'%(tt[3], tt[4])
        self.epoch = time.mktime(tt)
        logging.debug('   date %s time %s'%(self.date, self.time))
        return True

#------------------------------------------------------------------------------

    def setLatitude(self, data):
        """
        Description:    Parse the latitude string in the header.
        Input:          data: <string> The header line containing the latitude string.
        Output:         None.
        Return Value:   Boolean.
        Discussion:     Data looks like '* NMEA Latitude = 27 59.54 N'
                                     or '** Latitude: 27 59.54 N'
        """

        logging.debug('setLatitude()')
        status = False
 
        try:
            degrees, minutes = number_regex.findall(data)
            hemisphere = data[-1]

            logging.debug('   data %s'%`data`)
            logging.debug('   degrees %s minutes %s hemisphere %s'%(degrees, minutes, hemisphere))

            if hemisphere in ['N','S']:
                try:
                    degrees = float(degrees)
                    minutes = float(minutes)
                    if degrees >= self.min_lat and degrees <= self.max_lat:
                        if minutes >= 0.0 and minutes < 60.0:
                            hmFactor = hmFactors[hemisphere]
	                    minutes = minutes/60.0
	                    lat = degrees + minutes
                            self.flat = lat * hmFactor
	                    self.lat = '%5.5d'%(int(round(lat, 3) * 1000.0))
                            logging.debug('   flat %f lat %s'%(self.flat, self.lat))
                            status = True
                        else:
                            logging.warning('   Minutes out of range (%f)'%minutes)
                    else:
                        logging.warning('   Degrees out of range (%f)'%degrees)
                except ValueError, msg:
                    logging.warning('   String conversion failed: %s'%str(msg))
                    logging.warning('   degrees: %s'%degrees)
                    logging.warning('   minutes: %s'%minutes)
            else:
                logging.warning('   Unrecognized hemisphere--expecting \'N\' or \'S\'') 
        except ValueError:
            logging.warning('   Unable to parse incoming text.') 

        return status

#------------------------------------------------------------------------------

    def setLongitude(self, data):
        """
        Description:    Parse the longitude string in the header.
        Input:          data: <string> The header line containing the longitude string.
        Output:         None.
        Return Value:   Boolean.
        Discussion:     Data looks like '* NMEA Longitude = 092 59.95 W'
                                     or '** Longitude: 092 59.95 W'
        """
        
        logging.debug('setLongitude()')
        status = False

        try:
            degrees, minutes = number_regex.findall(data)
            hemisphere = data[-1]

            logging.debug('   data %s'%`data`)
            logging.debug('   degrees %s minutes %s hemisphere %s'%(degrees, minutes, hemisphere))

            if hemisphere in ['E','W']:
                try:
	            degrees = float(degrees)
                    minutes = float(minutes)
                    if degrees >= self.min_lon and degrees <= self.max_lon:
                        if minutes >= 0.0 and minutes <= 60.0:
                            hmFactor = hmFactors[hemisphere]
	                    minutes = minutes/60.0
	                    lon = degrees + minutes
                            self.flon = lon * hmFactor
	                    self.lon = '%6.6d'%int(round(lon, 3) * 1000.0)
                            logging.debug('   flon %f lon %s'%(self.flon, self.lon))
                            status = True
                        else:
                            logging.warning('   Minutes out of range (%f)'%minutes)
                            logging.warning('   data: %s'%data)
                    else:
                        logging.warning('   Degrees out of range (%f)'%degrees)
                        logging.warning('   data: %s'%data)
                except ValueError, msg:
                    logging.warning('   String conversion failed: %s'%str(msg))
                    logging.warning('   degrees: %s'%degrees)
                    logging.warning('   minutes: %s'%minutes)
            else:
                logging.warning('   Unrecognized hemisphere--expecting \'E\' or \'W\'')
                logging.warning('   data: %s'%data)
        except ValueError, msg:
                logging.warning('   Unable to parse incoming text.') 
                logging.warning('   data: %s'%data)

	return status

#------------------------------------------------------------------------------

    def setFloatVal(self, member, data):
        """
        Description:    Extract a floating-point value and store it in an instance member.
        Input:          member: <string> Name of the instance member to store the value.
                          data: <string> Header line containing the value.
        Output:         None.
        Return Value:   Boolean.
        Discussion:     Expecting a line that looks like '# nquan = 13'
        """

        try:
            setattr(self, member, float(number_regex.findall(data)[0]))
            return True
        except ValueError:
            logging.warning('setFloatVal(): cast to float failed')
            logging.warning('    data: %s'%data)
            logging.warning('    member: %s'%member)
            return False
        except (IndexError,AttributeError), msg:
            logging.warning('setFloatVal(): unable to find quantity')
            logging.warning('    data: %s'%data)
            logging.warning('    member: %s'%member)
            return False

#------------------------------------------------------------------------------

    def setIntVal(self, member, data):
        """
        Description:    Extract an integer value and store it in an instance member.
        Input:          member: <string> Name of the instance member to store the value.
                          data: <string> Header line containing the value.
        Output:         None.
        Return Value:   Boolean.
        Discussion:     Expecting a line that looks like '# nquan = 13'
        """

        try:
            setattr(self, member, int(number_regex.findall(data)[0]))
            return True
        except ValueError:
            logging.warning('setIntVal(): cast to int failed')
            logging.warning('    data: %s'%data)
            logging.warning('    member: %s'%member)
            return False
        except (IndexError,AttributeError), msg:
            logging.warning('setIntVal(): unable to find quantity')
            logging.warning('    data: %s'%data)
            logging.warning('    member: %s'%member)
            return False

#------------------------------------------------------------------------------

    def getData(self, format='kkyy', rewind=False):
        """
        Description:   Parse the data section of the file and return a depth, temperature, salinity
                       tuple for each data line in the section.  Values are formatted according to
                       the KKYY spec.
        Input:         format  <string>  if 'kkyy', return KKYY-formatted depth, temp, salinity triplets.
                                         if 'raw',  return raw floating-point values.
                       rewind  <boolean> if True, rewind the file before parsing the data lines.
        Output:        None.
        Return Value:  This method is a generator.  Return value is a 3-tuple until EOF. 
        """

        if self.fp:
            format = format.lower()
            if rewind:
                #
                # Rewind the file and churn through the header
                #
                self.fp.seek(0)
	        for line in self.fp.xreadlines():
	           if line.find(END_OF_HEADER) != -1:
	               break
            #
            # Should be in the data section now
            #
	    for line in self.fp.xreadlines():
	        tokens = tokenizer.findall(line)
                if len(tokens) != self.nDataValues:
                    logging.warning('Number of data values in file != number of data values in header (got %d, expected %d)'%(len(tokens), self.nDataValues))
                try:
                    depth = float(tokens[self.ndxDepth])
                    temp = float(tokens[self.ndxTemp])
                    salinity = float(tokens[self.ndxSalinity])
                    try:
                       oxygen = float(tokens[self.ndxOxygen])
                    except TypeError:
                       oxygen = None
                    if format == 'kkyy':
                        try:
                           depth = 20000 + int(depth)
                           try:
                               temp = 30000 + int(round(temp, 2) * 100.0)
                               try:
                                   salinity = 40000 + int(round(salinity, 2) * 100.0)
                                   yield depth, temp, salinity
                               except ValueError, msg:
                                   logging.warning('getData() ValueError salinity: %s'%str(msg))
                           except ValueError, msg:
                               logging.warning('getData() ValueError temperature: %s'%str(msg))
                        except ValueError, msg:
                           logging.warning('getData() ValueError temperature: %s'%str(msg))
                    else:
                        yield depth, temp, salinity, oxygen
                except IndexError:
                    logging.warning('getData() IndexError: idxDepth %d idxTemp %d idxSalinity %d nvalues %d'%(self.ndxDepth,
                                                                                                              self.ndxTemp,
                                                                                                              self.ndxSalinity,
                                                                                                              len(tokens)))
        else:
            logging.critical('getData():  No file handle.')
