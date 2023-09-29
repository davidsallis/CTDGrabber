#------------------------------------------------------------------------------------------
#
# startup.py
#
# Perform application startup:  process command-line arguments, read the configuration file,
# configure the logger
#
#------------------------------------------------------------------------------------------

import sys, logging
from ConfigParser import SafeConfigParser
from optparse import OptionParser

#------------------------------------------------------------------------------------------

def getOptionsFromOptionParser():
    """
    Description:    Configure the option parser and process any command-line arguments.
    Input:          None.
    Return Value:   A Python OptionParser object.
    """

    usage = 'usage: %prog [options]'
    parser = OptionParser(usage)
    parser.add_option('-c', '--config-file',
                      dest='config_file',
                      default='./CTDGrabber.cfg',
                      action='store',
                      help='Path to configuration file [./CTDGrabber.cfg]')
    parser.add_option('-d', '--dry-run',
                      dest='dry_run',
                      default=False,
                      action='store_true',
                      help='Dry run; do everything but send the file to NDBC [False]')
    parser.add_option('-g', '--debug',
                      dest='debug',
                      default=False,
                      action='store_true',
                      help='Run in debug mode (read: copious logging output) [False]')
    parser.add_option('-x', '--exit-when-done',
                      dest='exit_when_done',
                      default=False,
                      action='store_true',
                      help='Exit when processing is complete [False]')
    return parser.parse_args()

#------------------------------------------------------------------------------------------

def configureTheLogger(options):
    """
Description:  Configure the logger.
Input:        options:  <obj>  A Python OptionParser object.
Return Value: None.
    """

    logLevel = logging.DEBUG if options.debug else logging.INFO
    logging.basicConfig(level=logLevel,
                        format='%(asctime)-s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        stream=sys.stdout)

#------------------------------------------------------------------------------------------

def readTheConfigFile(options):
    """
Description:  Read the application configuration file.
Input:        options:  <obj>  A Python OptionParser object.
Return Value: A Python ConfigParser object.
    """

    #
    # 'optionxform = str' is used here to force case-sensitive option
    # parsing (default is to convert all options to lowercase)
    #
    config = SafeConfigParser()
    config.optionxform = str
    config.read(options.config_file)

    return config

#------------------------------------------------------------------------------------------

def startup():
    """
Description:   Perform application startup.
Input:         None.
Return Value:  A 3-tuple containing an OptionParser object, command-line arguments, and
               a ConfigParser object.
    """

    options, args = getOptionsFromOptionParser()
    configureTheLogger(options)
    config = readTheConfigFile(options)

    return options, args, config
