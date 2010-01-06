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

import sys, os, getopt, codecs

def get_table(sql, connstr, nls_lang=None):
    """
    Retrieves data from table and returns it as list
    """

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
    try:
        import cx_Oracle
    except:
        raise ImportError("""Required cx_Oracle module not found.
The module could be obtained from here: http://cx-oracle.sourceforge.net/
See also: http://www.orafaq.com/wiki/Python""")

    # if NLS_LANG is defined, set it to environment variable
    if nls_lang:
        import os
        os.environ["NLS_LANG"] = nls_lang

    connection = cx_Oracle.connect(connstr)
    cursor = connection.cursor()
    cursor.execute(sql)

    ret = cursor.fetchall()

    cursor.close()
    connection.close()

    if nls_lang:
        try:
            enc = nls_lang.split('.')[-1]
            ret2 = [tuple(
                            [isinstance(b,basestring) and unicode(b,enc) or b
                             for b in a]
                         )for a in ret]
        except LookupError:
            return ret
        ret = ret2
        
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
        -h, --help
            Display this help message.
        -n, --nls
            NLS language definition (for example, "AMERICAN_AMERICA.UTF8")
        -o, --output=FILENAME
            Output file. If not specified, goes to standard
            output (stdout).
        -v, --verbose
            Write detailed information to stderr.
    """

    def log_error(s):
        sys.stderr.write(s)
        sys.stderr.write('\n')
    def log(s):
        pass

    command = os.path.split(argv[0])[1]
    params = {}
    cpt_char = None

    #Extract options
    try:
        opts, args = getopt.getopt(
            argv[1:],
            "n:o:c:vh",
            ["output=", "connection-string=", "verbose", "help", "nls="])

        sql = args and " ".join(args) or None
        connstr = None
        outfile = None
        nls = None

    except getopt.GetoptError, err:
        print main.__doc__ % locals()
        print "Error: %s" % err
        return -2
    except IndexError, err:
        print main.__doc__ % locals()
        print "Error: SQL not specified."
        return -2        

    
    for o, a in opts:
        if   o in ("-v", "--verbose"):
            log = log_error
        elif o in ("-o", "--output"):
            outfile = a
        elif o in ("-n", "--nls"):
            nls = a
        elif o in ("-c", "--connection-string"):
            connstr = a
        elif o in ("-h", "--help"):
            print main.__doc__ % locals()
            return 0


    log("Generating ASCIIDOC from Oracle table")
    log("=====================================")
    
    if not connstr:
        log_error("Oracle connection string not specified!")
        return -2

    try:
        # Get SQL
        if not sql:
            sql = sys.stdin.read()
            sys.stdin.close()
        
        # Get data from Oracle
        log("Executing script: \n\t%s" % sql)
        ctnt = get_table(sql, connstr, nls)

        # Generate
        log("Generating ASCIIDOC...")
        ret = make_asciidoc(ctnt)

        # Write ASCIIDOC
        log("Writing file %s ..." % (outfile or 'stdout'))
        f = outfile and open(outfile, "w") or sys.stdout
        f.write(codecs.encode(ret,"utf8"))
        f.close()

        log("Done!")
        
    except Exception,err:
        log_error("Error: %s\n")
        raise

    log("")
    return 0
