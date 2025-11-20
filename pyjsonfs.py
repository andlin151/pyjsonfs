#!//usr/bin/env python3

import json
import os
import errno
import stat
from fuse import FUSE, Operations

class PyJSONFS( Operations ):
    def __init__( self, archivo ):
        # carga la estructura JSON al iniciar el FS
        with open( archivo, 'r' ) as f:
            self.mi_json = json.load( f )
        # Este diccionario estaria almacenando los archivos en memoria, con su contenido
        # para permitir lectura, escritura, etc.
        self.files = {}

    def _obtener_objeto( self, ruta ):
        """
        esta funcion es auxiliar y devuelve el objeto de la ruta dada.
        """
        if ruta == '/':
            # si me preguntas por la raiz, te devuelvo todo, no hay mas 
            return self.mi_json
        
        # si no es la raiz, vamos a recorrer la ruta
        partes = ruta.strip('/').split('/')
        objeto = self.mi_json
        # con esto iriamos de la raiz a las hojas 
        # objeto: archivo o directorio
        for parte in partes:
            if objeto != None:
                objeto = next( ( item for item in objeto["contenidos"] if item.get( "nombre" ) == parte ), None )
            else:
                break

        return objeto

    # --- Funciones obligatorias para FUSE ---

    def getattr( self, path, fh=None ):
        """
        me da los atributos de la ruta en cuestion,
        en linux estos serian los permisos, el tamaño, tipo...
        """
        objeto = self._obtener_objeto( path )
        if objeto is None:
            raise FileNotFoundError( errno.ENOENT, os.strerror( errno.ENOENT ), path )
        

        if objeto["es_dir"]:
            return { 
                'st_mode': stat.S_IFDIR | int( objeto["permisos"], 8 ),
                'st_nlink': 2  # 2 + número de subdirectorios que contiene
                # 'st_nlink': 2 + sum(1 for i in objeto["contenidos"] if i.get("es_dir", False))
            }
        else:
            return { 
                'st_mode': stat.S_IFREG | int( objeto["permisos"], 8 ),
                'st_nlink': 1,  # Por defecto, cuando creas un archivo
                'st_size': len( objeto["contenido"] )
            }
        

    def readdir( self, path, fh ):
        """
        contenidos del directorio
        """
        objeto = self._obtener_objeto( path )
        if objeto is None or not objeto.get("es_dir", False):
            raise FileNotFoundError( errno.ENOENT, os.strerror(errno.ENOENT), path )
        
        
        # "." y ".." son siempre parte del listado de directorios
        items = ['.', '..'] + [ i["nombre"] for i in objeto["contenidos"] ]
        print( items )
        for item in items:
            yield item

    def open( self, path, flags ):
        """
        al intentar abrir un archivo. Aquí sólo validamos que el archivo exista.
        """
        objeto = self._obtener_objeto( path )
        if objeto is None or objeto.get( "es_dir", False ):
            raise FileNotFoundError( errno.ENOENT, os.strerror( errno.ENOENT ), path )
        return 0  # solo para verificar si el archivo es valido, nada mas

    def read( self, path, size, offset, fh ):
        """     
        leeme el contenido del archivo de la ruta provista
        """
        objeto = self._obtener_objeto( path )
        if objeto is None or objeto.get( "es_dir", False ):
            raise FileNotFoundError( errno.ENOENT, os.strerror( errno.ENOENT ), path )

        
        return objeto["contenido"].encode( 'utf-8' )[ offset:offset+size ]
        

if __name__ == '__main__':
    import sys
    if len( sys.argv ) != 3:
        print( f'Usar de esta forma: { sys.argv[0] } <archivo_json> <directorio_de_montaje>' )
        exit( 1 )

    json_file = sys.argv[1]
    mount_point = sys.argv[2]

    fuse = FUSE( PyJSONFS( json_file ), mount_point, foreground=True, ro=True )

