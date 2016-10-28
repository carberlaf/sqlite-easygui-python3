#! /usr/bin/env python3

"""
    The basic interface of the application is a choice box screen actions
         If it runs on Linux terminal. -> ./utilBd.py
             action out in this way closes the application
         If you import to PythonConsole -> from utilBD import *
             action out hides the gui
             type display_gui () to redisplay the dialog screen actions
     Several functions to use sqlite3 in: memory:
     You can import / export databases from / to dump.sql files
     You can import / export tables from / to CSV files
     You can convert a :memory: in a database .sqlite
     You can attach databases .sqlite
     It's used the module easygui and through the various dialogs displayed
         in screen: data is entered, actions are chosen to perform, etc ...

__author__=carberlaf
"""

import sqlite3 as sq

import easygui as eg

# A title used in dialog_boxes
TITLE = 'UTILS -- SQLITE3'
# dict -> scheme database (key(table's name):value(list of fields)
scheme = {}

_con = sq.connect(':memory:')  # init connection
_con.row_factory = sq.Row  # init row factory to use the results as dict
_c = _con.cursor()  # init cursor to exec the sql


def _howmany_fields(num):  # used in function new_table
    _fields = []
    for i in range(1, num + 1):
        _fields.append('field' + i.__str__())
    return _fields


def _concat(*args, sep = ','):  # used to format the sql
    return sep.join(*args)


def new_table():
    """
    You must enter into a dialogue_box:
         the name of the table to create and
         the number of fields that will have the table
     By default creates fields with names:
         field1, field2, ..., field_n
     In the next dialog_box shown,  gives option to change these names
     : Return: message-table
    """
    try:
        _table, _fields_number = eg.multenterbox("Table's data", TITLE,
                                                 fields = ["table's name", "number of fields"])
        _fields = eg.multenterbox(msg = 'Key the names of fields',
                                  title = TITLE,
                                  fields = _howmany_fields(int(_fields_number)),
                                  values = _howmany_fields(int(_fields_number)))
        _sql = 'create table ' + _table + '(' + _concat(_fields, sep = ',') + ');'
        _c.execute(_sql)
        scheme[_table] = _fields
        _con.commit()
        eg.msgbox('Created table ' + _table, TITLE)
    except:
        pass


def delete_table():
    _table = eg.choicebox('Choose table to delete', TITLE, choices=list(scheme.keys()))
    if _table is None:
        return
    _c.execute('drop table %s' % _table)
    scheme.pop(_table)


def insert_data(table):
    """
    A dialog_box is displayed with the field names to enter values for each
     : Param table: str
     : Return None
    """
    try:
        data = eg.multenterbox('Introducing data', TITLE, scheme[table])
        _sql = "insert into " + table + " values('" + _concat(data, sep = "','") + "');"
        _c.execute(_sql)
        _con.commit()
    except:
        pass  # if button cancel is pressed


def select_data(table):
    """
    It is a simple query SELECT from table
    The data in the table is shown into a text_box.
     It includes rowid
     : rtype: table with data
     : Param table: str
    """
    try:
        _sql = "select rowid, * from " + table
        records = _c.execute(_sql).fetchall()
        reading = '{:*^40}'.format(table) + '\n'
        reading += str(records[0].keys()) + '\n'
        for _row in records:
            reading += str(list([*_row])) + "\n"
        eg.textbox('Content in %s' % table, TITLE, reading)
    except:
        pass  # if button cancel is pressed


def save_base():
    """
    Save the all database in a file 'dump' with extension .sql
    :return: None
    """
    with open(eg.filesavebox('', '', default = "dump_*.sql", filetypes = ' \*.sql'), 'w') as _f:
        for _line in _con.iterdump():
            _f.write('%s\n' % _line)


def recover_base(origin, _master = None):
    """
    According to the source:
         if .sql (origin=0) database is open in :memory:
         if .sqlite (origin=1) database is attached
     The scheme of the database is updated
     : Param origin: int
     : Param _master: None
         the sqlite_master recovered table is used to update the schema
     : Return: None
    """
    try:
        if origin == 0:  # from .sql
            with open(eg.fileopenbox(default = './*.sql'), 'r') as _f:
                for _line in _f:
                    _con.execute(_line)
        if origin == 2:  # from *.sqlite
            _file = eg.fileopenbox(default = './*.sqlite', filetypes = [['*.sqlite', '*.sqlite3', 'Sqlite Files']])
            _con.execute('attach database "' + _file + '" as attached')

    except:
        pass
    finally:  # update scheme
        if origin == 0:
            _master = 'sqlite_master'
        if origin == 2:
            _master = 'attached.sqlite_master'
        for _row in _c.execute('select name from ' + _master).fetchall():
            _sql = 'select * from {} limit 1'.format(_row[0])
            for _r in _c.execute(_sql).fetchall():
                scheme[_row[0]] = list(_r.keys())


def update_data(table, rowid, *news):
    """
     Data record (rowid) are updated within a table
     Both parameters are mandatory.
     If there is no *news parameter, it takes the record and the current status is displayed
         to allow modify data.
     If there's *news shows how would the record and give the OK.
     : param table: str
     : param rowid: int
     : param *news: list
    """
    if not news:
        sql = 'select * from %s where rowid=%s' % (table, rowid)
        _values = list(*[_c.execute(sql).fetchone()])
    else:
        _values = news
    try:
        _data = eg.multenterbox('Update record with rowid %s' % rowid, TITLE,
                                fields = scheme[table], values = _values)
        l = dict(zip(scheme[table], _data))
        sql = 'update ' + table + ' set '
        for k, v in l.items():
            sql += k + '="' + v + '",'
        sql = sql[0:len(sql) - 1]  # delete the last coma
        sql += ' where rowid=' + str(rowid) + ';'
        _c.execute(sql)
    except TypeError:  # if button cancel is pressed
        pass


def table2csv():
    """
     A table is chosen and save it in a file named <table>.csv
     : return: displays a text_box with the file content created for verification
    """
    import csv
    table = eg.choicebox('Choose table to convert to .csv', TITLE, choices = list(scheme.keys()))
    file = table + '.csv'
    response = _c.execute('select * from ' + table).fetchall()
    with open(file, 'w') as f:
        fieldnames = response[0].keys()
        writer = csv.DictWriter(f, fieldnames = fieldnames)
        writer.writeheader()
        for x in range(len(response)):
            writer.writerow({k: response[x][k] for k in response[x].keys()})
    # verification
    with open(file) as f:
        reader = csv.reader(f)
        reading = ""
        for row in reader:
            reading += str(row) + '\n'
        eg.textbox('Saved file {} with content: '.format(file), TITLE, reading)


def csv2table():
    """
     A <filename>.csv is chosen and becomes a table named <filename>
     : return: None
    """
    from csv import reader
    arch = eg.fileopenbox(default = '*.csv')
    table = arch.split('/')[len(arch.split('/')) - 1].replace('.csv', '')
    with open(arch) as f:
        _reader = reader(f)
        _fields = next(_reader)
        sql = 'create table ' + table + '(' \
              + _concat(_fields, sep = ',') + ')'
        _c.execute(sql)
        scheme[table] = _fields
        for row in _reader:
            sql = "insert into " + table + " values('" + \
                  _concat(row, sep = "','") + "');"
            _c.execute(sql)


# Initial dialog_box to select the action to execute
def display_gui(v = True):
    while v:
        if len(list(scheme.keys())) > 0:
            _actions = ['new table', 'delete table',
                        'insert', 'select',
                        'update', 'save',
                        'recover', 'quit']
        else:
            _actions = ['new table',
                        'recover',
                        'quit']
        _response = eg.buttonbox('''
                    Main Dialog
                    Choose action''', TITLE, _actions)

        if _response == 'new table':
            new_table()

        if _response == 'delete table':
            delete_table()

        if _response == 'insert':
            _table = eg.choicebox('Choose table to insert', _response, choices = list(scheme.keys()))
            if not _table:
                continue
            insert_data(_table)

        if _response == 'select':
            _table = eg.choicebox('Choose table from select', _response, choices = list(scheme.keys()))
            if _table:
                select_data(_table)

        if _response == 'update':
            _table = eg.choicebox('Choose table to update', _response, choices = list(scheme.keys()))
            _rowid = eg.integerbox('Choose rowid to update', _response)
            if not _table or not _rowid:
                continue
            update_data(_table, _rowid)

        if _response == 'save':
            _x = eg.indexbox('''    Comment:
                        In .sql format to save the whole base from :memory:
                    except attached bases.\n
                        In .csv format one by one table,
                    but also from the attached bases''',
                             TITLE,
                             choices = ['in .sql', 'in .csv', 'in sqlite'])
            if _x == 0:
                save_base()
            elif _x == 1:
                table2csv()
            elif _x == 2:
                save_sqlite()
            else:
                continue

        if _response == 'recover':
            _x = eg.indexbox('''        From?:
                             sql:    import one or several tables\n
                             csv:    import one table\n
                             sqlite: attach base''',
                             'Recover base or table',
                             choices = ['*.csv', '*.sql', '*.sqlite'])
            if _x == 0:
                csv2table()
            elif _x in range(1, 3):
                recover_base(_x)
            else:
                continue

        if _response == 'quit':
            break


def save_sqlite():
    import io
    stream = io.StringIO()
    for line in _con.iterdump():
        stream.write(line)
    file = eg.enterbox('Name of new database .sqlite', TITLE)
    if file is None:
        return
    new = sq.connect(file)
    new.executescript(stream.getvalue())
    stream.close()
    new.close()


def _init():
    eg.msgbox("Let's create an 'in memory' base", TITLE)
    display_gui()


if __name__ == '__main__':
    _init()
