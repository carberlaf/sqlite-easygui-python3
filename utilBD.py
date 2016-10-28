#! /usr/bin/env python3

"""
    La interface básica de la aplicación es un cuadro de elección de acciones en pantalla
    Si se ejecuta en terminal Linux. -> ./utilBd.py
        la acción salir en este modo cierra la aplicación
    Si se importa a PythonConsole -> from utilBD import *
        la acción salir oculta la gui
        teclear >>> ver_gui() para mostrar de nuevo el cuadro de acciones en pantalla
    Varias funciones para utilizar sqlite3 en :memory:
    Se pueden importar/exportar bases de datos desde/hacia archivos dump.sql
    Se pueden importar/exportar tablas desde/hacia archivos .csv
    Se puede guardar la base :memory: en una base .sqlite
    Se pueden adjuntar bases de datos .sqlite
    Se utiliza el módulo easygui y a través de los distintos diálogos que aparecen
        en pantalla se introducen datos, se eligen acciones a realizar, etc...

"""

import sqlite3 as sq

import easygui as eg

# A utilizar como título en las ventanas
TITULO = 'UTILIZACIÓN DE SQLITE3'
# dict -> esquema base (key(nombre de tabla):value(lista de campos)
esquema = {}

_con = sq.connect(':memory:')  # inicio de la conexión
_con.row_factory = sq.Row  # Row factory para utilizar los resultados como dicccionario
_c = _con.cursor()  # se crea cursor para ejecutar las sqls


def _cuantos_campos(num):  # se utiliza en la funcion crear tabla
    _campos = []
    for i in range(1, num + 1):
        _campos.append('campo' + i.__str__())
    return _campos


def _concat(*args, sep = ','):  # se utiliza para concatenar las sentencias sql
    return sep.join(*args)


def crear_tabla():
    """
    Hay que teclear en un diálogo:
        el nombre de la tabla a crear y
        el número de campos que tendrá la tabla
    Por defecto crea campos con nombres:
        campo1, campo2, ..., campon
    En el siguiente diálogo se da opción a cambiar estos nombres
    :return: mensaje de creación de tabla
    """
    try:
        _tabla, num_campos = eg.multenterbox('Datos de la tabla', TITULO,
                                             fields = ['nombre de la tabla', 'número de campos'])
        _campos = eg.multenterbox(msg = 'Introducir nombres de campos',
                                  title = TITULO,
                                  fields = _cuantos_campos(int(num_campos)),
                                  values = _cuantos_campos(int(num_campos)))
        _sql = 'create table ' + _tabla + '(' + _concat(_campos, sep = ',') + ');'
        _c.execute(_sql)
        esquema[_tabla] = _campos
        _con.commit()
        eg.msgbox('Creada tabla ' + _tabla, TITULO)
    except:
        pass


def borrar_tabla():
    _tabla = eg.choicebox('Elegir tabla a eliminar', TITULO, choices=list(esquema.keys()))
    if _tabla is None:
        return
    _c.execute('drop table %s' % _tabla)
    esquema.pop(_tabla)


def insertar_datos(tabla):
    """
    Se muestra un diálogo con los nombres de los campos
    para introducir los valores de cada uno de ellos
    :param tabla: str
    :return None
    """
    try:
        datos = eg.multenterbox('Introducir Datos', TITULO, esquema[tabla])
        _sql = "insert into " + tabla + " values('" + _concat(datos, sep = "','") + "');"
        _c.execute(_sql)
        _con.commit()
    except:
        pass


def ver_datos(tabla):
    """
    Es una simple consulta SELECT de la tabla
    Se muestra cuadro con los datos de la tabla. Incluye el rowid
    :rtype: cuadro con los datos
    :param tabla: str
    """
    try:
        _sql = "select rowid, * from " + tabla
        registros = _c.execute(_sql).fetchall()
        lectura = '{:*^40}'.format(tabla) + '\n'
        lectura += str(registros[0].keys()) + '\n'
        for _row in registros:
            lectura += str(list([*_row])) + "\n"
        eg.textbox('Datos en ' + tabla, TITULO, lectura)
    except:
        pass


def guardar_base():
    """
    Se guarda la base en un archivo 'dump' con extensión .sql
    :return: None
    """
    with open(eg.filesavebox('', '', default = "dump_*.sql", filetypes = ' \*.sql'), 'w') as _f:
        for _line in _con.iterdump():
            _f.write('%s\n' % _line)


def recuperar_base(origen, _master = None):
    """
    Según el origen:
        si .sql(0) se abre base
        si .sqlite(1) se adjunta
    Se actualiza el esquema
    :param origen: int
    :param _master: None
        Se utiliza la tabla sqlite_master de la recuperada para actualizar el esquema
    :return: None
    """
    try:
        if origen == 0:  # desde .sql
            with open(eg.fileopenbox(default = './*.sql'), 'r') as _f:
                for _line in _f:
                    _con.execute(_line)
        if origen == 2:  # desde *.sqlite
            _archivo = eg.fileopenbox(default = './*.sqlite', filetypes = [['*.sqlite', '*.sqlite3', 'Sqlite Files']])
            _con.execute('attach database "' + _archivo + '" as adjunta')
    except:
        pass
    finally:  # recuperar esquema
        if origen == 0:
            _master = 'sqlite_master'
        if origen == 2:
            _master = 'adjunta.sqlite_master'
        for _row in _c.execute('select name from ' + _master).fetchall():
            _sql = 'select * from {} limit 1'.format(_row[0])
            for _r in _c.execute(_sql).fetchall():
                esquema[_row[0]] = list(_r.keys())


def actualizar_datos(tabla, rowid, *nuevos):
    """
    Se actualizan los datos de un registro (rowid) dentro de una tabla (tabla)
    Ambos son parametros obligatorios.
    Si no hay parámetro *nuevos, se toma el registro y se muestra el estado actual
        para permitir modificar los datos.
    Si existe *nuevos se muestra cómo quedaría el registro y dar el Ok.
    :param tabla: str
    :param rowid: int
    :param nuevos: lista
    """
    if not nuevos:
        sql = 'select * from %s where rowid=%s' % (tabla, rowid)
        _valores = list(*[_c.execute(sql).fetchone()])
    else:
        _valores = nuevos
    try:
        datos = eg.multenterbox('Actualizar registro con rowid %s' % rowid, TITULO,
                                fields = esquema[tabla], values = _valores)
        l = dict(zip(esquema[tabla], datos))
        sql = 'update ' + tabla + ' set '
        for k, v in l.items():
            sql += k + '="' + v + '",'
        sql = sql[0:len(sql) - 1]  # quito la ultima coma
        sql += ' where rowid=' + str(rowid) + ';'
        _c.execute(sql)
    except TypeError:  # si se cancela la entrada de datos
        pass


def tabla2csv():
    """
    Se elige un tabla y la convierte en un archivo con nombre <tabla>.csv
    :return: muestra un cuadro con el contenido del archivo creado para su comprobación
    """
    import csv
    tabla = eg.choicebox('Seleccionar tabla a convertir a .csv', TITULO, choices = list(esquema.keys()))
    archivo = tabla + '.csv'
    respuesta = _c.execute('select * from ' + tabla).fetchall()
    with open(archivo, 'w') as f:
        fieldnames = respuesta[0].keys()
        writer = csv.DictWriter(f, fieldnames = fieldnames)
        writer.writeheader()
        for x in range(len(respuesta)):
            writer.writerow({k: respuesta[x][k] for k in respuesta[x].keys()})
    # comprobación
    with open(archivo) as f:
        reader = csv.reader(f)
        lectura = ""
        for row in reader:
            lectura += str(row) + '\n'
        eg.textbox('Creado archivo {} con el contenido: '.format(archivo), TITULO, lectura)


def csv2tabla():
    """
    Se elige un <archivo>.csv y la convierte en una tabla con nombre <archivo>
    :return: None
    """
    from csv import reader
    arch = eg.fileopenbox(default = '*.csv')
    tabla = arch.split('/')[len(arch.split('/')) - 1].replace('.csv', '')
    with open(arch) as f:
        lector = reader(f)
        nombre_campos = next(lector)
        sql = 'create table ' + tabla + '(' \
              + _concat(nombre_campos, sep = ',') + ')'
        _c.execute(sql)
        esquema[tabla] = nombre_campos
        for row in lector:
            sql = "insert into " + tabla + " values('" + \
                  _concat(row, sep = "','") + "');"
            _c.execute(sql)


# Muestra diálogo inicial para seleccionar la acción a ejecutar
def ver_gui(v = True):
    while v:
        if len(list(esquema.keys())) > 0:
            _acciones = ['crear tabla', 'borrar tabla',
                         'insertar', 'ver',
                         'actualizar', 'guardar',
                         'recuperar', 'salir']
        else:
            _acciones = ['crear tabla',
                         'recuperar',
                         'salir']
        _respuesta = eg.buttonbox('''
                    Diálogo Principal
                    Elegir acción''', TITULO, _acciones)

        if _respuesta == 'crear tabla':
            crear_tabla()

        if _respuesta == 'borrar tabla':
            borrar_tabla()

        if _respuesta == 'insertar':
            _tabla = eg.choicebox('Insertar registros a...', TITULO, choices = list(esquema.keys()))
            if not _tabla:
                continue
            insertar_datos(_tabla)

        if _respuesta == 'ver':
            _tabla = eg.choicebox('Seleccionar registros de... ', TITULO, choices = list(esquema.keys()))
            if _tabla:
                ver_datos(_tabla)

        if _respuesta == 'actualizar':
            _tabla = eg.choicebox('Actualizar registro en...', TITULO, choices = list(esquema.keys()))
            _rowid = eg.integerbox('Seleccionar rowid', _respuesta)
            if not _tabla or not _rowid:
                continue
            actualizar_datos(_tabla, _rowid)

        if _respuesta == 'guardar':
            _x = eg.indexbox('''        Observaciones:
                            En formato sql se guarda toda la base :memory:
                        no las bases adjuntas.\n
                            En formato csv una sola tabla
                        pero también de las adjuntas''',
                             TITULO,
                             choices = ['en sql', 'en csv', 'en sqlite'])
            if _x == 0:
                guardar_base()
            elif _x == 1:
                tabla2csv()
            elif _x == 2:
                guardar_sqlite()
            else:
                continue

        if _respuesta == 'recuperar':
            _x = eg.indexbox('''        ¿Desde?:
                            sql o csv: se crea(n) tabla(s) en memoria\n
                            sqlite:    se adjunta base''',
                             'Recuperar Base',
                             choices = ['*.csv', '*.sql', '*.sqlite'])
            if _x == 0:
                csv2tabla()
            elif _x in range(1, 3):
                recuperar_base(_x)
            else:
                continue

        if _respuesta == 'salir':
            break


def guardar_sqlite():
    import io
    stream = io.StringIO()
    for line in _con.iterdump():
        stream.write(line)
    archivo = eg.enterbox('Nombre de la nueva base .sqlite', TITULO)
    if archivo is None:
        return
    nueva_base = sq.connect(archivo)
    nueva_base.executescript(stream.getvalue())
    stream.close()
    nueva_base.close()


def _inicio():
    eg.msgbox('Vamos a crear una base "in memory"', TITULO)
    ver_gui()


if __name__ == '__main__':
    _inicio()
