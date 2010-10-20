# Author: David Avsajanishvili
# Contact: avsd05@gmail.com

"""
Module for parsing database structure
from Oracle SQL DDL script
"""

__all__ = ['Table','Column','parse_tables','parse_views','PERMITS_LIST']

import re

RXX_TABLENAME = \
    "(?P<tablename>([\\w\\$]+\\.|\"[\\w\\$]+\"\\.)?([\\w\\$]+|\"[\\w\\$]+\"))"

RX_TABLE = re.compile(
    r"\bCREATE\s+TABLE\s+" 
           + RXX_TABLENAME + 
           r"\s*\(" 
           r"(?P<columns>.*?)" 
           r"\)" 
           r"\s*(;|tablespace .*?;)"
    , re.DOTALL | re.IGNORECASE)

RX_COLUMN = re.compile(
    r'(?P<colname>([\w\$]+|"[\w\$ ]+"))\s+' 
       r'(?P<coltype>(\w+|"[^"]+")\s*[\(\)\d]*)\s*' 
       r"(\bdefault\s+(?P<default>\S+))?\s*" 
       r"(?P<primarykey>\bprimary\s+key)?\s*" 
       r"(?P<notnull>\bnot\s+null)?\s*" 
       r"(\benable)?\s*" 
           r"(?:\Z|,)"
    , re.DOTALL | re.IGNORECASE)


RX_VIEW = re.compile(
    r"\bCREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s(?P<tablename>[\w\$]*\.?[\w\$]+)\b" 
          r"\s*(\((?P<aliases>[\s\w\$,]*)\))?" 
          r"\s*\bAS\s+SELECT\s+" 
          r"(?P<columns>.*?)" 
          r"\bFROM\s+(?P<sources>.*?)(?P<isunion>\bUNION\b(\s+ALL\b)?.*?)?"
          r"(?:(\bWHERE\b)|(\bORDER\s+BY\b)|(\bGROUP\s+BY\b)|;)"
    , re.DOTALL | re.IGNORECASE)



RX_TAB_COMMENT = re.compile(
    r"\bCOMMENT\s+ON\s+TABLE\s+" 
        + RXX_TABLENAME + 
        r"\s+is\s+" 
        r"'(?P<comment>.*?)'\s*;"
    , re.DOTALL|re.IGNORECASE)

RX_COL_COMMENT = re.compile(
    r"\bCOMMENT\s+ON\s+COLUMN\s+" 
         + RXX_TABLENAME + r"\.(?P<colname>[\w\$]+)" 
         r"\s+is\s+" 
         r"'(?P<comment>.*?)'\s*;"
    , re.DOTALL|re.IGNORECASE)

PERMITS_LIST = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']

RX_PRIVILEGE = re.compile(
    r"\b(?P<privilege>GRANT|REVOKE)\s+(?P<permit>" + "|".join(PERMITS_LIST) + ")\s+"
        r"ON\s+" + RXX_TABLENAME + r"\s+TO\s+(?P<schema>[\w&$]+)\s*;"
    , re.DOTALL|re.IGNORECASE)

class Column(object):

    def __init__(self, nm, tp = "", nl = False, default=None, dsc = "", value = None):
        self.name = nm.replace("\"", "")
        self.type = tp
        self.nullable = nl
        self.desc = dsc
        self.default = default
        self.value = value

class Privileges(object):
    """
    Represents DB level privileges for certain schema
    """
    def __init__(self):
        self.privileges = dict([(p,None) for p in PERMITS_LIST])

    def grant(self, permit):
        if permit in PERMITS_LIST:
            self.privileges[permit] = True

    def revoke(self, permit):
        if permit in PERMITS_LIST:
            self.privileges[permit] = False

    def __getitem__(self,index):
        return self.privileges[index]

class TableView(object):

    _obj_type = ""

    def __init__(self, nm, dsc = "", txt = ""):
        self.name = nm.replace("\"", "")
        self.desc = dsc
        self.text = txt
        
        # Columns
        self.cols = []
        
        # Permissions
        self.permits = {}

    def grant(self, schema, permit):
        if not schema in self.permits:
            self.permits[schema] = Privileges()
        self.permits[schema].grant(permit)

    def revoke(self, schema, permit):
        if not schema in self.permits:
            self.permits[schema] = Privileges()
        self.permits[schema].revoke(permit)

    def __str__(self):
        return "%s %s" % (self._obj_type, self.name)

    def add_col(self, col):
        self.cols.append(col)
        return col
    
    def add_column(self, nm, tp, nl=False, default=None, dsc=""):
        return self.add_col(Column(nm, tp, nl, default, dsc))

    def render_cols(self, pattern, column_format_func=None):
        """
        Renders columns using string-formatting pattern.

        Parameters:
        
            pattern -- string, representing formatting pattern.
                May contain following named parameters:
                    %(name)s
                    %(type)s
                    %(nullable)s
                    %(notnull)s
                    %(default)s
                    %(value)s
                    %(desc)s
                In case of using column_format_func parameter
                these names may be altered.
                
            column_format_func -- optional callback function,
                called for each column and returning dictionary
                to be applied to the "pattern" to format it.
                Must accept single argument - Column object.
        """

        ret = ""

        # If only one column - '*', not render:
        if len(self.cols) == 1 and self.cols[0].name == '*':
            return ''

        for c in self.cols:
            dct = column_format_func(c) if column_format_func else {
                    'name'      : c.name,
                    'type'      : c.type,
                    'nullable'  : c.nullable,
                    'notnull'   : '' if c.nullable else ' not null',
                    'default'   : c.default,
                    'value'     : c.value,
                    'desc'      : c.desc,
                }
            ret += pattern % dct
            
        return ret
            
    def parse_privileges(self,sql):
        """
        Parses privileges and revokes for the object from passed SQL
        """

        for g in RX_PRIVILEGE.finditer(sql):
            dt = g.groupdict()
            if dt['tablename'].replace("\"", "").lower() == self.name.lower():
                if dt['privilege'].lower() == 'revoke':
                    self.revoke(dt['schema'],dt['permit'])
                else:
                    self.grant(dt['schema'],dt['permit'])


class Table(TableView):
    _obj_type = "Table"

class View(TableView):
    _obj_type = "View"

    def __init__(self, nm, dsc = "", txt = ""):
        super(View, self).__init__(nm, dsc, txt)
        self.sources = []
        self.is_union = False

def remove_sql_comments(sql):
    """
    Removes inline and block comments of SQL (/*...*/, --...)
    """

    fnd =re.compile(r"(\/\*.*?\*\/)", re.DOTALL)
    while fnd.search(sql):
        sql = fnd.sub("", sql)

    is_str = False
    is_cmt = False
    sql2 = ""
    i = 0
    while i < len(sql):
        if is_cmt:
            if sql[i]=="\n":
                is_cmt = False
                sql2 += sql[i]
        else:
            if is_str:
                sql2 += sql[i]
            else:
                if sql[i:i+2] == '--':
                    is_cmt = True
                else:
                    sql2 += sql[i]
            if sql[i]=="'":
                is_str = not is_str
        i+=1
    sql = sql2
    
    return sql

def parse_table_comments(sql):
    """
    Parses comments for TABLES and returns as Dictionary
    """

    tabcoms = {}
    for t in RX_TAB_COMMENT.finditer(sql):
        t = t.groupdict()
        tabcoms[t['tablename']] = t['comment'].replace("''", "'")

    return tabcoms

def parse_column_comments(sql):
    """
    Parses comments for COLUMNS and returns as Dictionary
    (by table) of Dictionaries (column comments)
    """

    colcoms = {}
    for t in RX_COL_COMMENT.finditer(sql):
        t = t.groupdict()

        # Add new dictionary if not exists
        if not colcoms.has_key(t['tablename']):
            colcoms[t['tablename']] = {}
        colcoms[t['tablename']][t['colname']] = t['comment'].replace("''", "'")
    return colcoms


def parse_tables(sql):
    """
    Parses Oracle-formatted SQL file, extracts tables
    and returns them as List
    """

    sql = remove_sql_comments(sql)

    # Parse comments
    tab_comments = parse_table_comments(sql)
    col_comments = parse_column_comments(sql)

    # Parse tables
    tables = []
    for t in RX_TABLE.finditer(sql):
        dt = t.groupdict()

        # Create table object
        tabl = Table(dt['tablename'], tab_comments.get(dt['tablename'], ''), t.group())
        tabl_colcomments = col_comments.get(tabl.name, {})

        # Parse columns of the table
        for t2 in RX_COLUMN.finditer(dt['columns']):
            dc = t2.groupdict()

            # Add column
            tabl.add_column(
                dc['colname'],
                dc['coltype'],
                False if str(dc['notnull']).upper()=="NOT NULL" else True,
                dc['default'],
                tabl_colcomments.get(dc['colname'], ""))
            #print dc['colname']

        # Parse privileges of the table
        tabl.parse_privileges(sql)
            
        # Add table to Dictionary
        tables.append(tabl)

    return tables


def parse_views(sql):
    """
    Parses views, represented with "Create As Select" script
    and returns them as a list.
    """

    sql = remove_sql_comments(sql)

    # Parse comments
    tab_comments = parse_table_comments(sql)
    col_comments = parse_column_comments(sql)

    # Parse views
    views = []
    for t in RX_VIEW.finditer(sql):
        dt = t.groupdict()

        # Create View object
        view = View(dt['tablename'], tab_comments.get(dt['tablename'], ''), t.group())
        view_colcomments = col_comments.get(view.name, {})
        view.is_union = bool(dt.get('isunion'))


        # ---------------------
        # Adding Columns
        # ---------------------
        col_vl = "" #Value
        col_al = "" #Alias
        bFillingAlias = False

        def add_col_to_view(view, col_al, col_vl, colcomments_dict):
            """
            Adds a column to View
            """
            col_al = (col_al.strip() or col_vl).split(".")[-1].strip()
            cc = Column(
                nm    = col_al,
                value = col_vl.strip())
            cc.desc = colcomments_dict.get(cc.name)

            cc = view.add_col(col=cc)
            #-------------------------

        parth = 0
        is_str = False

        for c in dt['columns']:
            if not (parth>0 or is_str):
                if c == ",":
                    add_col_to_view(view, col_al, col_vl, view_colcomments)

                    col_vl = ""
                    col_al = ""
                    bFillingAlias = False
                    continue

                # If some space found
                elif c in " \n" and bool(col_vl.strip()):
                    bFillingAlias = True

            if c == "'":
                is_str = not is_str

            if not is_str:
                if c == '(':
                    parth+=1
                elif c == ')':
                    parth-=1

            if bFillingAlias:
                col_al +=c
            else:
                col_vl +=c

        # Add the final column
        add_col_to_view(view, col_al, col_vl, view_colcomments)

        # Optional column aliases before the AS keyword
        aliases = dt.get('aliases')
        if aliases:
            aliases = aliases.split(",")
            if len(aliases)==len(view.cols):
                for i in range(len(aliases)):
                    view.cols[i].name = aliases[i].strip()
                    view.cols[i].desc = view_colcomments.get(view.cols[i].name)
        
        # ---------------------
        # Adding View-Sources
        # ---------------------
        if dt['sources'].strip():
            view.sources = dt['sources'].split(",")
            for i in range(0,len(view.sources)):
                view.sources[i] = view.sources[i].strip()

        # Parse privileges of the view
        view.parse_privileges(sql)
        
        # Add view to Dictionary
        views.append(view)

    return views
