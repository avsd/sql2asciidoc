# Author: David Avsajanishvili
# Contact: avsd05@gmail.com

"""
Helper package to make Python scripts with
command-line options, parsing database structure.
"""

__all__ = ['TOP_COMMENT', 'TABLE_SEP', 'sql_to_asciidoc', 'main_sql2asciidoc']

from db import *
import asciidoc
import getopt, os, re
import sys

TOP_COMMENT = \
r"""// ''''''''''''''''''''''''''''''''''''''''''''''''''
// THIS FILE IS GENERATED AUTOMATICALLY - DON'T EDIT!
// ''''''''''''''''''''''''''''''''''''''''''''''''''
// Tables parsed from SQL
// using script, written on Python
// and sql2asciidoc library
// ''''''''''''''''''''''''''''''''''''''''''''''''''
"""

TABLES_CPT = "Tables"
VIEWS_CPT = "Views"

TABLE_SEP = "|============================================================"

# Text inclusions
TEXT_INCLS = []


def preformat_coldesc(txt):
    """
    Preformats column description to represent lists
    """

    # Converting unnumbered lists directly to DocBook:
    #
    # The list:
    #
    # - one
    # - two
    # - three
    #
    # Is converted to:
    # The list:
    # +++<itemizedlist>
    # <listitem><simpara> one </simpara></listitem>
    # <listitem><simpara> two </simpara></listitem>
    # <listitem><simpara> three </simpara></listitem>
    # </itemizedlist>
    #
    # 1. The list must be preceded with a text line, 
    #    followed by two blank lines.
    # 2. Each list item must start with "minus" (-) without indention.
    #    Line breaks inside list items are not allowed.
    # 3. Two or more list items must exist.

    if not txt: txt=""
    g = re.compile("(\n\s*)((\n- [^\n]+){2,})")
    txt = g.sub(r"\1 +++<itemizedlist> \2 </itemizedlist>+++", txt)

    g = re.compile(r"(\+\+\+<itemizedlist>.*\n)- ([^\n]+)(.*</itemizedlist>\+\+\+)", re.DOTALL)
    while(g.search(txt)):
        txt = g.sub(r"\1 <listitem><simpara>+++ \2 +++</simpara></listitem> \3", txt)

    return txt

def columndict_callback(c):
    """
    Callback funciton, returning column formatting dictionary
    for Table::render_cols function
    """

    def subQ(txt):
        return re.sub(r"'([^']*)'", r"`\1'", (txt or '')).replace(r'|', r'\|')

    return {
        'name'      : c.name,
        'type'      : c.type,
        'nullable'  : c.nullable,
        'value'     : subQ(c.value),
        'default'   : subQ(c.default),
        'defaultf'  : ("\n\n*Default: %s*" % subQ(c.default))
                        if c.default else '',
        'notnull'   : '' if c.nullable else ' not null',
        'desc': c.desc,
        'descf': c.desc,        
    }
    
def tables_to_asciidoc(
        sql,
        title_char = r'~'):

    """
    Renders SQL with Tables creation DDL -- to ASCIIDOC.
    """

        
    ret = ""
    coldesctbl_header = "|Column |Type |Description"
    coldesctbl_attributes = '[cols="8m,5m,15a",options="header"]'
    
    # Parse tables
    tbs = parse_tables(sql)

    # Some globals to locals
    table_sep = TABLE_SEP

    # Render tables
    for t in tbs:

        tnm = t.name
        ttl = title_char * len(tnm)
        dsc = t.desc
        cols = t.render_cols("|%(name)s  |%(type)s|%(descf)s%(defaultf)s\n", columndict_callback)

        ret += """
%(tnm)s
%(ttl)s

%(dsc)s

.Columns of the table
%(coldesctbl_attributes)s
%(table_sep)s
%(coldesctbl_header)s
%(cols)s
%(table_sep)s

""" % locals()

    return ret


def views_to_asciidoc(
        sql,
        title_char = r'~'):

    """
    Renders SQL with Views creation DDL -- to ASCIIDOC.
    """

    global TEXT_INCLS
        
    ret = ""
    coldesctbl_attributes = '[cols="8m,8m,12a",options="header"]'
    coldesctbl_header = "|Alias |Value |Description"
        
    # Parse tables
    vws = parse_views(sql)

    # Some globals to locals
    table_sep = TABLE_SEP

    # Render views
    for t in vws:

        tnm = t.name
        ttl = title_char * len(tnm)
        dsc = t.desc
        cols = t.render_cols("|%(name)s  |+++%(value)s+++|%(descf)s\n", columndict_callback)

        ret += """
%(tnm)s
%(ttl)s

%(dsc)s

""" % locals()

        if t.sources:
            srcs = ""
            for src1 in t.sources:
                a, tmp, b = src1.rpartition(" ")
                srcs += "|%s |%s\n" % (

                    # Getting left part (Table/View) or entire if not partitioned,
                    # replacing at-sign with inline-block ($$@$$) to avoid generating
                    # mailto: link automatically.
                    (a or b).replace(r"|", r"\|").replace(r"@", r"$$@$$"),

                    # Getting right part or nothing if not partitioned
                    (b if a else '').replace(r"|", r"\|"),
                    )
                
            ret += """
.Sources of the view
[cols="8m,5m",options="header",width="70%%"]
%(table_sep)s
|Table/View |Alias
%(srcs)s
%(table_sep)s

""" % locals()

        if cols:
            ret += """
.Columns of the view
%(coldesctbl_attributes)s
%(table_sep)s
%(coldesctbl_header)s
%(cols)s
%(table_sep)s

""" % locals()

        if t.is_union:
            TEXT_INCLS.append(t.text)
            ret += """

The view is created using UNION select. Script of the view
is shown below:
            
.View SQL
[source,sql]
------------------------------------------------------------
INCLUSION_%d
------------------------------------------------------------
""" % (len(TEXT_INCLS) - 1)

    return ret


def objects_to_comments(sql):
    """
    Parses tables, views, columns and makes file of comments
    """
    
    def colf(c):
        """
        Callback funciton, returning column formatting dictionary
        for Table::render_cols function
        """
        return {
            'name'      : c.name,
            'desc'      : (c.desc or "").replace("'", "''"),
        }
    
    # Parse tables & views
    objs = parse_tables(sql) + parse_views(sql)

    # Render objects
    ret = """
-- COMMENTS    ON    DATABASE    OBJECTS --
-- Auto-generated from SQL CREATE script --
-------------------------------------------
    """
    for o in objs:
        onm = o.name
        OTP = o._obj_type.upper()
        dsc = (o.desc or "").replace("'", "''")
        cols = o.render_cols("comment on column %s.%%(name)s\n  is '%%(desc)s';\n" % onm, colf)
        
        ret += """
------ %(OTP)s: %(onm)s ------
comment on table %(onm)s
  is '%(dsc)s';
%(cols)s
""" % locals()

    return ret
    


def main(argv):
    """
    %(command)s - Prints ASCIIDOC of table descriptions from SQL,
                  passed as command-line in argv.

    Usage:
        %(command)s [options] sql_filename
        
    Options:
        -c, --title-char=TITLECHAR
            Characters for title underlines.
            If ONE character, only tables are rendered.
            if TWO OR MORE -- both tables and views are
            rendered; In this case first character is underline
            for "Tables" or "Views" captions, second - for
            table and viewnames themselves.
            Default: ~
        -o, --output=FILENAME
            Output file. By default - sql_filename with
            asciidoc extension. If "-" is specified as FILENAME,
            output is written to stdout.
        -m, --comments
            Generate SQL comments rather than asciidoc output
        -v, --verbose
            Write detailed information to stderr.
    Note:
        If sql_filename is not specified, SQL is expected from
        stdin. In this case output goes to stdout as well,
        unless -o parameter is specified.
    """

    def log_error(s):
        sys.stderr.write(s)
        sys.stderr.write('\n')
    def log(s):
        pass

    global TEXT_INCLS
    TEXT_INCLS = []

    command = os.path.split(argv[0])[1]
    params = {}
    cpt_char = None
    comments = False

    #Extract options
    try:
        opts, args = getopt.getopt(
            argv[1:],
            "c:a:t:r:A:V:R:o:vm",
            ["title-char=",
             "table-attributes=", "table-header=", "row-pattern=",
             "view-table-attributes=", "view-header=", "view-row-pattern=",
             "output=", "verbose", "comments"])

        infile = args and args[0] or None
        outfile = infile and "%s.asciidoc" % os.path.splitext(os.path.split(infile)[1])[0] or '-'

    except getopt.GetoptError, err:
        print main.__doc__ % locals()
        print "Error: %s" % err
        return -2
    except IndexError, err:
        print main.__doc__ % locals()
        print "Error: File not specified."
        return -2        

    
    for o, a in opts:
        if   o in ("-c", "--title-char"):
            a = a.strip()
            if len(a) > 1:
                cpt_char = a[0]
                params['title_char'] = a[1]
            else:
                params['title_char'] = a
        elif o in ("-v", "--verbose"):
            log = log_error
        elif o in ("-o", "--output"):
            outfile = a
        elif o in ("-m", "--comments"):
            comments = True

    if outfile=='-':
        outfile = None

    if comments:
        log("Generating SQL COMMENTS from SQL")
        log("================================")
    else:
        log("Generating ASCIIDOC from SQL")
        log("============================")

    try:
        # Read SQL
        log("Reading file %s ..." % infile)
        f = infile and open(infile) or sys.stdin
        sql = f.read()
        f.close()

        if comments:
            ret = objects_to_comments(sql)
        else:
            ret = TOP_COMMENT

            if cpt_char:
                ret += "\n\n%s\n%s\n" % (TABLES_CPT, cpt_char*len(TABLES_CPT))

            # Parse Tables from SQL
            log("Parsing Tables...")
            ret += tables_to_asciidoc(sql, **params)

            if cpt_char:

                ret += "\n\n%s\n%s\n" % (VIEWS_CPT, cpt_char*len(VIEWS_CPT))
                
                # Parse Views from SQL
                log("Parsing Views...")
                ret += views_to_asciidoc(sql, **params)
                

            # Making title references
            ret = asciidoc.make_title_references(ret)
            
            # Making text inclusions of the Views
            for i in range(len(TEXT_INCLS)):
                ret = ret.replace("INCLUSION_%d" % i, TEXT_INCLS[i])

        # Write SQL
        log("Writing file %s ..." % outfile)
        f = outfile and open(outfile, "w") or sys.stdout
        f.write(ret)
        f.close()

        log("Done!")
        
    except Exception,err:
        log_error("Error: %s" % err)
        raise

    log("")
    return 0
