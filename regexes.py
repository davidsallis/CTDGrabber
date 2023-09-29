#---------------------------------------------------------------------
#
# regexes.py
#
# Some useful regular expressions.
#
# Filename pattern: CCCC_YYYYMMDDHHMM_DDD.cnv
# where 'CCCC' is the ship callsign;
#       'YYYYMMDDHHMM' is a date/time group;
#       'DDD' is the CTD cast number.
#
#
#---------------------------------------------------------------------
import re

ctdFilenamePattern = re.compile(r'\S{4}_\d{12}_\d{3}.cnv')
ctdDateTimeGroupPattern = re.compile(r'\d{12}')
ctdCallsignPattern = re.compile(r'\S{4}')
