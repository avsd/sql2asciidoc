#SQL to AsciiDoc Convertor

Imported from Google Code.

I used this script as a process of building technical documentation at [Geocell](http://geocell.ge)

##Summary

This is a [Python](http://www.python.org) library and script to export SQL DDL and SQL SELECT command's
output to AsciiDoc.

There are two scripts represented in the package:

 * `ddl2asciidoc` -- converts DDL (Create Table/View SQL scripts) to AsciiDoc source;
 * `sql2asciidoc` -- connects to database, executes SELECT ... script and converts it's result to AsciiDoc table body.


##ddl2asciidoc

```
    ddl2asciidoc - Prints ASCIIDOC of table descriptions from SQL,
                  passed as command-line in argv.

    Usage:
        ddl2asciidoc [options] sql_filename
        
    Options:
        -c, --title-char=TITLECHAR
            Characters for title underlines.
            If ONE character, only tables are rendered.
            if TWO OR MORE -- both tables and views are
            rendered; In this case first character is underline
            for "Tables" or "Views" captions, second - for
            table and viewnames themselves.
            Default: ~
        -h, --help
            Display this help message.
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
    
```

##sql2asciidoc

```
    sql2asciidoc - Prints ASCIIDOC of table contents from Oracle database
                  thats connection and SQL passed as command-line in argv.

    Usage:
        sql2asciidoc [options] sql_command
        
    Options:
        -c, --connection-string=CONNSTRING
            Connection string to connect to Oracle DB, mandatory.
        -h, --help
            Display this help message.
        -o, --output=FILENAME
            Output file. If not specified, goes to standard
            output (stdout).
        -v, --verbose
            Write detailed information to stderr.
    
```
