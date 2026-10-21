"""Genera el diagrama UML completo del caso OTI usando solo Python estándar.

Guardar junto a oti.py y ejecutar: python generar_uml.py
Resultado: diagrama_uml.svg, que se puede abrir en cualquier navegador.

El archivo oti.py se lee con ast: no se importa ni se ejecutan sus pruebas.
Clases, atributos, propiedades, métodos y herencias se extraen del código.
Las asociaciones por códigos se declaran aquí porque una cadena str no permite
deducir por sí sola la clase a la que hace referencia.
"""

import argparse
import ast
from dataclasses import dataclass, field
from html import escape
from math import hypot
from pathlib import Path


@dataclass
class Clase:
    nombre: str
    bases: list = field(default_factory=list)
    abstracta: bool = False
    enumeracion: bool = False
    atributos: list = field(default_factory=list)
    propiedades: list = field(default_factory=list)
    metodos: list = field(default_factory=list)

    def grupos(self):
        if self.enumeracion:
            return [("VALORES", self.atributos)]
        return [(titulo, filas) for titulo, filas in (
            ("ATRIBUTOS", self.atributos),
            ("PROPIEDADES", self.propiedades),
            ("MÉTODOS", self.metodos),
        ) if filas]

    def alto(self):
        return 80 + sum(32 + 25 * len(filas) + 10
                        for _, filas in self.grupos())


# El valor público bool se conserva internamente como int (0 o 1).
TIPOS_INTERNOS = {
    ("PlanEstudio", "__vigente"): "int",
    ("PlanEstudio", "__nuevo"): "int",
    ("PeriodoAcademico", "__es_verano"): "int",
}
CALCULADAS = {"horas_totales", "vacantes_disponibles",
              "creditos_totales", "nombre_completo"}

# (origen, destino, propiedad que contiene el código, nombre del papel).
# Son asociaciones lógicas: no representan referencias a objetos ni composición.
ASOCIACIONES = [
    ("Seccion", "Curso", "codigo_curso", ""),
    ("Seccion", "PeriodoAcademico", "codigo_periodo", ""),
    ("PlanEstudio", "EscuelaProfesional", "codigo_escuela", ""),
    ("Estudiante", "EscuelaProfesional", "codigo_escuela", ""),
    ("EscuelaProfesional", "Docente", "codigo_director", "director"),
    ("EscuelaProfesional", "Docente", "codigo_secretario", "secretario académico"),
]
ORDEN = ("RegistroConNombre", "Curso", "PeriodoAcademico", "PlanEstudio",
         "EscuelaProfesional", "Seccion", "EstadoPeriodo", "Estudiante",
         "Docente", "Persona")


def nombre_decorador(nodo):
    return ast.unparse(nodo)


def leer_clases(ruta):
    arbol = ast.parse(ruta.read_text(encoding="utf-8-sig"), filename=str(ruta))
    clases = {}
    for nodo in arbol.body:
        if not isinstance(nodo, ast.ClassDef):
            continue
        bases = [ast.unparse(base) for base in nodo.bases]
        metodos = [m for m in nodo.body if isinstance(m, ast.FunctionDef)]
        clase = Clase(nodo.name, bases,
                      any("abstractmethod" in [nombre_decorador(d)
                                               for d in m.decorator_list]
                          for m in metodos),
                      "IntEnum" in bases)
        getters = {m.name: m for m in metodos
                   if "property" in [nombre_decorador(d)
                                     for d in m.decorator_list]}
        setters = {m.name for m in metodos
                   if any(nombre_decorador(d).endswith(".setter")
                          for d in m.decorator_list)}

        for miembro in nodo.body:
            if not isinstance(miembro, ast.Assign):
                continue
            for destino in miembro.targets:
                if not isinstance(destino, ast.Name):
                    continue
                valor = ast.unparse(miembro.value)
                if clase.enumeracion:
                    clase.atributos.append((f"{destino.id} = {valor}", False))
                else:
                    tipo = "int | None" if valor == "None" else "int"
                    clase.atributos.append((
                        f"+ {destino.id}: {tipo} = {valor} [estático]", False))

        privados = []
        for metodo in metodos:
            for miembro in ast.walk(metodo):
                if (isinstance(miembro, ast.Attribute)
                        and isinstance(miembro.value, ast.Name)
                        and miembro.value.id == "self"
                        and isinstance(miembro.ctx, ast.Store)
                        and miembro.attr.startswith("__")
                        and miembro.attr not in privados):
                    privados.append(miembro.attr)
        filas_privadas = []
        for nombre in privados:
            getter = getters.get(nombre[2:])
            tipo = TIPOS_INTERNOS.get((clase.nombre, nombre))
            if tipo is None:
                tipo = ast.unparse(getter.returns) if getter and getter.returns else "?"
            if tipo == "?":
                raise ValueError(f"Falta indicar el tipo de {clase.nombre}.{nombre}.")
            filas_privadas.append((f"- {nombre}: {tipo}", False))
        clase.atributos = filas_privadas + clase.atributos

        for nombre, getter in getters.items():
            tipo = ast.unparse(getter.returns) if getter.returns else "?"
            acceso = "RW" if nombre in setters else "R"
            if nombre in CALCULADAS:
                acceso += ", calc"
            abstracto = any(nombre_decorador(d) == "abstractmethod"
                            for d in getter.decorator_list)
            sufijo = " {abstracta}" if abstracto else ""
            clase.propiedades.append((f"+ {nombre}: {tipo} [{acceso}]{sufijo}",
                                       abstracto))

        for metodo in metodos:
            if metodo.name in getters or any(
                    nombre_decorador(d).endswith(".setter")
                    for d in metodo.decorator_list):
                continue
            abstracto = any(nombre_decorador(d) == "abstractmethod"
                            for d in metodo.decorator_list)
            if metodo.name == "__init__":
                firma = "+ __init__(...)"
            else:
                argumentos = []
                for argumento in metodo.args.args[1:]:
                    tipo = ast.unparse(argumento.annotation) if argumento.annotation else None
                    if metodo.name in ("actualizar_fechas", "actualizar_matricula"):
                        tipo = tipo or "date"
                    argumentos.append(argumento.arg + (f": {tipo}" if tipo else ""))
                retorno = ast.unparse(metodo.returns) if metodo.returns else "None"
                firma = f"+ {metodo.name}({', '.join(argumentos)}): {retorno}"
            if abstracto:
                firma += " {abstracto}"
            clase.metodos.append((firma, abstracto))
        clases[clase.nombre] = clase

    if set(clases) != set(ORDEN):
        raise ValueError("Las clases de oti.py cambiaron. Actualiza ORDEN y la "
                         "distribución del diagrama para representar el nuevo modelo.")
    for origen, destino, codigo, _ in ASOCIACIONES:
        propiedades = [fila for fila, _ in clases[origen].propiedades]
        if not any(fila.startswith(f"+ {codigo}:") for fila in propiedades):
            raise ValueError(f"No existe {origen}.{codigo} para asociarlo con {destino}.")
    return clases


ANCHO_CAJA = 620
ANCHO = 3140
PARTES = []


def texto(x, y, contenido, tamano=16, color="#24334a", centro=False,
          negrita=False, cursiva=False, mono=False):
    familia = "'DejaVu Sans Mono', Consolas, monospace" if mono else "Arial, sans-serif"
    atributos = (f'x="{x}" y="{y}" font-size="{tamano}" fill="{color}" '
                 f'font-family="{familia}"')
    if centro:
        atributos += ' text-anchor="middle"'
    if negrita:
        atributos += ' font-weight="bold"'
    if cursiva:
        atributos += ' font-style="italic"'
    PARTES.append(f"<text {atributos}>{escape(contenido)}</text>")


def linea(puntos, tipo="asociacion"):
    datos = "M " + " L ".join(f"{x},{y}" for x, y in puntos)
    estilo = ' stroke-dasharray="8 6"' if tipo == "dependencia" else ""
    PARTES.append(f'<path d="{datos}" fill="none" stroke="#53657c" '
                  f'stroke-width="2.2"{estilo}/>')
    # Dibujar la punta explícitamente también permite verla en visores SVG
    # que no implementan los marcadores del formato.
    x, y = puntos[-1]
    anterior_x, anterior_y = puntos[-2]
    largo = hypot(x - anterior_x, y - anterior_y)
    ux, uy = (x - anterior_x) / largo, (y - anterior_y) / largo
    distancia, mitad = (21, 10) if tipo == "herencia" else (13, 7)
    base_x, base_y = x - ux * distancia, y - uy * distancia
    extremo_1 = (base_x - uy * mitad, base_y + ux * mitad)
    extremo_2 = (base_x + uy * mitad, base_y - ux * mitad)
    if tipo == "herencia":
        vertices = f"{x},{y} {extremo_1[0]},{extremo_1[1]} {extremo_2[0]},{extremo_2[1]}"
        PARTES.append(f'<polygon points="{vertices}" fill="white" '
                      'stroke="#53657c" stroke-width="2.2"/>')
    else:
        PARTES.append(f'<path d="M {extremo_1[0]},{extremo_1[1]} L {x},{y} '
                      f'L {extremo_2[0]},{extremo_2[1]}" fill="none" '
                      'stroke="#53657c" stroke-width="2.2"/>')


def etiqueta(x, y, *filas):
    ancho = max(len(fila) for fila in filas) * 8 + 20
    alto = len(filas) * 21 + 10
    PARTES.append(f'<rect x="{x-ancho/2}" y="{y-17}" width="{ancho}" '
                  f'height="{alto}" rx="5" fill="#f5f7fb"/>')
    for indice, fila in enumerate(filas):
        texto(x, y + indice * 21, fila, 14, centro=True)


def dibujar_clase(clase, x, y):
    alto = clase.alto()
    color = "#1b6470" if clase.enumeracion else "#243c5e"
    if clase.abstracta:
        color = "#365d91"
    PARTES.append(f'<g id="clase-{clase.nombre}">')
    PARTES.append(f'<rect x="{x}" y="{y}" width="{ANCHO_CAJA}" '
                  f'height="{alto}" fill="white" stroke="{color}" stroke-width="2"/>')
    PARTES.append(f'<rect x="{x}" y="{y}" width="{ANCHO_CAJA}" '
                  f'height="76" fill="{color}"/>')
    clase_tipo = "«enumeración»" if clase.enumeracion else (
        "«abstracta»" if clase.abstracta else "«clase»")
    texto(x + ANCHO_CAJA/2, y + 27, clase_tipo, 14, "#dce8f8", centro=True)
    texto(x + ANCHO_CAJA/2, y + 55, clase.nombre, 23, "white", centro=True,
          negrita=True, cursiva=clase.abstracta)
    cursor = y + 80
    for titulo, filas in clase.grupos():
        PARTES.append(f'<line x1="{x}" y1="{cursor}" x2="{x+ANCHO_CAJA}" '
                      f'y2="{cursor}" stroke="#d3dce8"/>')
        texto(x + 18, cursor + 23, titulo, 12, "#66778e", negrita=True)
        cursor += 32
        for contenido, abstracto in filas:
            texto(x + 18, cursor + 18, contenido, 16, cursiva=abstracto, mono=True)
            cursor += 25
        cursor += 10
    PARTES.append("</g>")


def generar_svg(clases, fuente):
    PARTES.clear()
    segunda_fila = 650 + max(clases[n].alto() for n in (
        "Curso", "PeriodoAcademico", "PlanEstudio", "EscuelaProfesional")) + 220
    persona_y = segunda_fila + max(clases[n].alto() for n in (
        "Estudiante", "Docente")) + 180
    posiciones = {
        "RegistroConNombre": (1240, 170),
        "Curso": (70, 650), "PeriodoAcademico": (850, 650),
        "PlanEstudio": (1630, 650), "EscuelaProfesional": (2410, 650),
        "Seccion": (70, segunda_fila), "EstadoPeriodo": (850, segunda_fila),
        "Estudiante": (1630, segunda_fila), "Docente": (2410, segunda_fila),
        "Persona": (2020, persona_y),
    }

    def arriba(nombre, desplazamiento=310):
        x, y = posiciones[nombre]
        return x + desplazamiento, y

    def abajo(nombre, desplazamiento=310):
        x, y = posiciones[nombre]
        return x + desplazamiento, y + clases[nombre].alto()

    pie_y = max(y + clases[n].alto() for n, (x, y) in posiciones.items()) + 95
    altura = pie_y + 200
    PARTES.extend([
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ANCHO}" '
        f'height="{altura}" viewBox="0 0 {ANCHO} {altura}" role="img" '
        'aria-labelledby="titulo descripcion">',
        '<title id="titulo">Diagrama de clases UML del caso OTI</title>',
        '<desc id="descripcion">Siete clases concretas, dos abstractas y una '
        'enumeración. Incluye atributos, propiedades, métodos, seis herencias, '
        'seis asociaciones por códigos y una dependencia de tipo.</desc>',
        f'<rect width="{ANCHO}" height="{altura}" fill="#f5f7fb"/>',
    ])
    texto(70, 68, "CASO OTI · DIAGRAMA DE CLASES UML", 34, negrita=True)
    texto(70, 105, "Encapsulamiento, abstracción, herencia y asociaciones mediante códigos", 20)

    # Seis herencias. Las de RegistroConNombre comparten la línea horizontal.
    for hijo in ("Curso", "PeriodoAcademico", "PlanEstudio", "EscuelaProfesional"):
        inicio = arriba(hijo)
        destino = abajo("RegistroConNombre")
        linea([inicio, (inicio[0], 565), (destino[0], 565), destino], "herencia")
    for hijo, desplazamiento in (("Estudiante", 160), ("Docente", 460)):
        inicio = abajo(hijo)
        destino = arriba("Persona", desplazamiento)
        puente = persona_y - 85
        linea([inicio, (inicio[0], puente), (destino[0], puente), destino], "herencia")

    # Seis asociaciones lógicas: 0..* registros de origen por un destino.
    inicio = arriba("Seccion", 160)
    destino = abajo("Curso", 160)
    linea([inicio, destino])
    inicio_periodo = arriba("Seccion", 460)
    destino_periodo = abajo("PeriodoAcademico", 160)
    puente_periodo = segunda_fila - 105
    linea([inicio_periodo, (inicio_periodo[0], puente_periodo),
           (destino_periodo[0], puente_periodo), destino_periodo])
    y_plan = 900
    linea([(2250, y_plan), (2410, y_plan)])
    inicio_escuela = arriba("Estudiante", 460)
    destino_escuela = abajo("EscuelaProfesional", 140)
    puente_escuela = segunda_fila - 100
    linea([inicio_escuela, (inicio_escuela[0], puente_escuela),
           (destino_escuela[0], puente_escuela), destino_escuela])
    for desplazamiento in (330, 530):
        linea([abajo("EscuelaProfesional", desplazamiento),
               arriba("Docente", desplazamiento)])

    # Dependencia del tipo EstadoPeriodo: no es una asociación de registros.
    inicio_estado = abajo("PeriodoAcademico", 430)
    destino_estado = arriba("EstadoPeriodo", 430)
    linea([inicio_estado, destino_estado], "dependencia")

    for nombre in ORDEN:
        dibujar_clase(clases[nombre], *posiciones[nombre])

    # Rótulos en los espacios libres para mantener legibles las conexiones.
    etiqueta(290, (inicio[1] + destino[1]) / 2, "codigo_curso")
    texto(248, inicio[1] - 12, "0..*", 14)
    texto(248, destino[1] + 24, "1", 14)
    etiqueta(780, puente_periodo - 14, "codigo_periodo")
    texto(inicio_periodo[0] + 16, inicio_periodo[1] - 12, "0..*", 14)
    texto(destino_periodo[0] + 16, destino_periodo[1] + 24, "1", 14)
    etiqueta(2330, y_plan - 30, "codigo_escuela")
    texto(2258, y_plan - 9, "0..*", 13)
    texto(2388, y_plan - 9, "1", 13)
    etiqueta(2310, puente_escuela - 14, "codigo_escuela")
    texto(inicio_escuela[0] + 16, inicio_escuela[1] - 12, "0..*", 14)
    texto(destino_escuela[0] + 16, destino_escuela[1] + 24, "1", 14)
    for indice, (desplazamiento, papel, codigo) in enumerate((
            (330, "director", "codigo_director"),
            (530, "secretario académico", "codigo_secretario"))):
        origen = abajo("EscuelaProfesional", desplazamiento)
        fin = arriba("Docente", desplazamiento)
        y = origen[1] + (fin[1] - origen[1]) * (0.40 if indice == 0 else 0.70)
        etiqueta(origen[0], y, papel, codigo)
        texto(origen[0] + 15, origen[1] + 24, "0..*", 14)
        texto(fin[0] + 15, fin[1] - 12, "1", 14)
    etiqueta(1320, (inicio_estado[1] + destino_estado[1]) / 2, "tipo de estado")

    texto(70, segunda_fila + clases["Seccion"].alto() + 60,
          "Las asociaciones se implementan con códigos str;", 18)
    texto(70, segunda_fila + clases["Seccion"].alto() + 90,
          "no almacenan objetos de las otras clases.", 18)
    texto(70, segunda_fila + clases["Seccion"].alto() + 145,
          "Los miembros heredados se muestran en la clase base.", 18)
    texto(70, segunda_fila + clases["Seccion"].alto() + 175,
          "__init__(...) abrevia los parámetros del constructor.", 18)

    PARTES.append(f'<line x1="70" y1="{pie_y-35}" x2="3070" '
                  f'y2="{pie_y-35}" stroke="#cad5e4"/>')
    texto(70, pie_y, "CÓMO LEER EL DIAGRAMA", 16, negrita=True)
    texto(70, pie_y + 36,
          "- privado    + público    R: solo lectura    RW: lectura y escritura    calc: calculada", 18)
    texto(70, pie_y + 70,
          "Cursiva / {abstracto}: abstracción    [estático]: atributo de clase", 18)
    texto(70, pie_y + 104,
          "Triángulo vacío: herencia    Flecha: asociación    Flecha discontinua: dependencia de tipo", 18)
    texto(70, pie_y + 138,
          f"Multiplicidad: 0..* = cero o varios; 1 = un registro de destino. Fuente: {fuente.name}", 18)
    PARTES.append("</svg>")
    return "\n".join(PARTES)


def main():
    carpeta = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fuente", type=Path, default=carpeta / "oti.py",
                        help="Archivo del caso OTI; por defecto, oti.py junto al script.")
    parser.add_argument("--salida", type=Path, default=carpeta / "diagrama_uml.svg",
                        help="Imagen SVG de salida.")
    opciones = parser.parse_args()
    if not opciones.fuente.is_file():
        parser.error(f"No se encuentra {opciones.fuente}. Guarda este script junto a oti.py.")
    try:
        clases = leer_clases(opciones.fuente)
        svg = generar_svg(clases, opciones.fuente)
        opciones.salida.write_text(svg, encoding="utf-8")
    except (OSError, SyntaxError, ValueError) as error:
        parser.error(str(error))
    print(f"Diagrama UML generado: {opciones.salida.resolve()}")
    print("Incluye 7 clases concretas, 2 abstractas y 1 enumeración.")
    print("Relaciones: 6 herencias, 6 asociaciones por códigos y 1 dependencia.")
    print("Abre diagrama_uml.svg con tu navegador y utiliza el zoom para leerlo.")


if __name__ == "__main__":
    main()
