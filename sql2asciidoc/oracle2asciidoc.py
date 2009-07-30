# Author: David Avsajanishvili
# Contact: avsd05@gmail.com

"""
Helper package to make Python scripts with
command-line options, converting database table contents
to ASCIIDOC table.

Connects to database specified in the Conneciton string
and prints containment of the table
in ASCIIDOC format.

Requires Python 2.6 and cx_Oracle
to be installed on the workstation
"""

import sys, os, getopt

###########################################
# cx_Oracle module is needed for specified
# version of Oracle (9,10 or 11).
# It could be downloaded from SourceForge:
#
#   http://cx-oracle.sourceforge.net/
#
# For more help see:
#   http://www.orafaq.com/wiki/Python
###########################################
import cx_Oracle

def get_table(sql, connstr):
    """
    Retrieves data from table and returns it as list
    """

    connection = cx_Oracle.connect(connstr)
    cursor = connection.cursor()
    cursor.execute(sql)

    ret = cursor.fetchall()

    cursor.close()
    connection.close()

    return ret
    
def make_asciidoc(dct):
    """
    Returns contents as rows of a table
    in asciidoc format
    """

    if not dct:
        return ""
    
    ret = ""
    for row in dct:
        for cell in row:
            ret += "|%s " % unicode(cell or "").replace(r"|",r"\|")
        ret += "\n"
        
    return ret
    
def main(argv):
    """
    %(command)s - Prints ASCIIDOC of table contents from Oracle database
                  that's connection and SQL passed as command-line in argv.

    Usage:
        %(command)s [options] sql_command
        
    Options:
        -c, --connection-string=CONNSTRING
            Connection string to connect to Oracle DB, mandatory.
        -o, --output=FILENAME
            Output file, mandatory.
        -s, --silent
            Don't generate any output
    """

    def log(s):
        print(s)

    command = os.path.split(argv[0])[1]
    params = {}
    cpt_char = None

    #Extract options
    try:
        opts, args = getopt.getopt(
            argv[1:],
            "o:c:s",
            ["output=", "connection-string=", "silent"])

        sql = args[0]
        connstr = None
        outfile = None

    except getopt.GetoptError, err:
        print main.__doc__ % locals()
        print "Error: %s" % err
        return -2
    except IndexError, err:
        print main.__doc__ % locals()
        print "Error: SQL not specified."
        return -2        

    
    for o, a in opts:
        if   o in ("-s", "--silent"):
            def log(s):
                pass
        elif o in ("-o", "--output"):
            outfile = a
        elif o in ("-c", "--connection-string"):
            connstr = a


    log("Generating ASCIIDOC from Oracle table")
    log("=====================================")
    
    if not connstr:
        log("Oracle connection string not specified!")
        return -2
    if not outfile:
        log("Output file not specified!")
        return -2

    try:
        # Get data from Oracle
        log("Executing script: \n\t%s" % sql)
        ctnt = get_table(sql, connstr)

        # Generate
        log("Generating ASCIIDOC...")
        ret = make_asciidoc(ctnt)

        # Write ASCIIDOC
        log("Writing file %s ..." % outfile)
        f = open(outfile, "w")
        f.write(ret)
        f.close()

        log("Done!")
        
    except Exception,err:
        print "Error: %s" % err
        raise

    log("")
    return 0
