"""Caso OTI: clases, validaciones y pruebas de programación orientada a objetos.

Ejecutar: python caso_oti.py
Solo utiliza la biblioteca estándar de Python. Las referencias son códigos str.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import IntEnum
from uuid import UUID, uuid4


def validar_texto(valor, campo, *, obligatorio=False, maximo=None):
    if not isinstance(valor, str):
        raise TypeError(f"{campo} debe ser texto.")
    valor = valor.strip()
    if obligatorio and not valor:
        raise ValueError(f"{campo} no puede quedar vacío.")
    if maximo is not None and len(valor) > maximo:
        raise ValueError(f"{campo} admite como máximo {maximo} caracteres.")
    return valor


def validar_entero(valor, campo, *, minimo=None, maximo=None):
    # bool es una subclase de int: se excluye para cantidades y horas.
    if type(valor) is not int:
        raise TypeError(f"{campo} debe ser un entero.")
    if minimo is not None and valor < minimo:
        raise ValueError(f"{campo} no puede ser menor que {minimo}.")
    if maximo is not None and valor > maximo:
        raise ValueError(f"{campo} no puede ser mayor que {maximo}.")
    return valor


def validar_decimal(valor, campo, *, minimo=None, maximo=None,
                    positivo=False, max_decimales=None):
    if isinstance(valor, bool) or not isinstance(valor, (int, float, str, Decimal)):
        raise TypeError(f"{campo} debe ser un número.")
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{campo} debe ser un número válido.") from None
    if not numero.is_finite():
        raise ValueError(f"{campo} debe ser un número finito.")
    if positivo and numero <= 0:
        raise ValueError(f"{campo} debe ser mayor que cero.")
    if minimo is not None and numero < minimo:
        raise ValueError(f"{campo} no puede ser menor que {minimo}.")
    if maximo is not None and numero > maximo:
        raise ValueError(f"{campo} no puede ser mayor que {maximo}.")
    if max_decimales is not None:
        # Los ceros finales no agregan precisión: 4.000 equivale a 4.
        partes = numero.as_tuple()
        decimales = max(0, -partes.exponent)
        digitos = list(partes.digits)
        while decimales and digitos and digitos[-1] == 0:
            digitos.pop()
            decimales -= 1
        if decimales > max_decimales:
            raise ValueError(f"{campo} admite hasta {max_decimales} decimales.")
    return numero


def validar_bandera(valor, campo):
    if type(valor) not in (int, bool) or valor not in (0, 1):
        raise ValueError(f"{campo} solo admite 0, 1, False o True.")
    return int(valor)


def validar_intervalo(inicio, fin):
    # datetime se excluye para comparar fechas sin horas.
    if (not isinstance(inicio, date) or isinstance(inicio, datetime)
            or not isinstance(fin, date) or isinstance(fin, datetime)):
        raise TypeError("El inicio y el fin deben ser fechas date.")
    if fin < inicio:
        raise ValueError("La fecha de fin no puede ser anterior a la de inicio.")
    return inicio, fin


class RegistroConNombre(ABC):
    """Comparte la validación del nombre y exige un resumen a las subclases."""

    MAX_NOMBRE = None

    def __init__(self, nombre):
        self.nombre = nombre

    @property
    def nombre(self) -> str:
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        self.__nombre = validar_texto(
            valor, "nombre", obligatorio=True, maximo=self.MAX_NOMBRE)

    @abstractmethod
    def resumen(self) -> str:
        """Cada tipo de registro decide qué información mostrar."""


class Curso(RegistroConNombre):
    MAX_NOMBRE = 200

    def __init__(self, codigo, nombre, creditos, horas_teoricas=0,
                 horas_practicas=0, horas_seminario=0, horas_virtuales=0):
        super().__init__(nombre)
        self.__id_curso = uuid4()
        self.__codigo = validar_texto(codigo, "codigo")
        self.creditos = creditos
        self.horas_teoricas = horas_teoricas
        self.horas_practicas = horas_practicas
        self.horas_seminario = horas_seminario
        self.horas_virtuales = horas_virtuales

    @property
    def id_curso(self) -> UUID:
        return self.__id_curso

    @property
    def codigo(self) -> str:
        return self.__codigo

    @property
    def creditos(self) -> Decimal:
        return self.__creditos

    @creditos.setter
    def creditos(self, valor):
        self.__creditos = validar_decimal(
            valor, "creditos", positivo=True, max_decimales=2)

    @property
    def horas_teoricas(self) -> int:
        return self.__horas_teoricas

    @horas_teoricas.setter
    def horas_teoricas(self, valor):
        self.__horas_teoricas = validar_entero(
            valor, "horas_teoricas", minimo=0, maximo=255)

    @property
    def horas_practicas(self) -> int:
        return self.__horas_practicas

    @horas_practicas.setter
    def horas_practicas(self, valor):
        self.__horas_practicas = validar_entero(
            valor, "horas_practicas", minimo=0, maximo=255)

    @property
    def horas_seminario(self) -> int:
        return self.__horas_seminario

    @horas_seminario.setter
    def horas_seminario(self, valor):
        self.__horas_seminario = validar_entero(
            valor, "horas_seminario", minimo=0, maximo=255)

    @property
    def horas_virtuales(self) -> int:
        return self.__horas_virtuales

    @horas_virtuales.setter
    def horas_virtuales(self, valor):
        self.__horas_virtuales = validar_entero(
            valor, "horas_virtuales", minimo=0, maximo=255)

    @property
    def horas_totales(self) -> int:
        return (self.horas_teoricas + self.horas_practicas
                + self.horas_seminario + self.horas_virtuales)

    def resumen(self) -> str:
        return (f"Curso {self.codigo}: {self.nombre}, {self.creditos} créditos, "
                f"{self.horas_totales} horas.")


class Seccion:
    def __init__(self, codigo, codigo_curso, codigo_periodo, vacantes):
        self.__codigo = validar_texto(codigo, "codigo")
        self.__codigo_curso = validar_texto(codigo_curso, "codigo_curso")
        self.__codigo_periodo = validar_texto(codigo_periodo, "codigo_periodo")
        self.__matriculados = 0
        self.vacantes = vacantes

    @property
    def codigo(self) -> str:
        return self.__codigo

    @property
    def codigo_curso(self) -> str:
        return self.__codigo_curso

    @property
    def codigo_periodo(self) -> str:
        return self.__codigo_periodo

    @property
    def vacantes(self) -> int:
        return self.__vacantes

    @vacantes.setter
    def vacantes(self, valor):
        valor = validar_entero(valor, "vacantes", minimo=1)
        if valor < self.__matriculados:
            raise ValueError("Las vacantes no pueden ser menores que los matriculados.")
        self.__vacantes = valor

    @property
    def matriculados(self) -> int:
        return self.__matriculados

    @property
    def vacantes_disponibles(self) -> int:
        return self.vacantes - self.matriculados

    def matricular(self):
        if self.vacantes_disponibles == 0:
            raise ValueError("La sección está llena: matrícula rechazada.")
        self.__matriculados += 1

    def retirar(self):
        if self.__matriculados == 0:
            raise ValueError("No hay matriculados para retirar.")
        self.__matriculados -= 1


class PlanEstudio(RegistroConNombre):
    MAX_NOMBRE = 36

    def __init__(self, nombre, anio_aprobacion, codigo_escuela,
                 creditos_obligatorios, creditos_electivos,
                 creditos_extracurriculares, vigente=1, nuevo=0):
        super().__init__(nombre)
        self.__anio_aprobacion = validar_entero(anio_aprobacion, "anio_aprobacion")
        self.__codigo_escuela = validar_texto(codigo_escuela, "codigo_escuela")
        self.creditos_obligatorios = creditos_obligatorios
        self.creditos_electivos = creditos_electivos
        self.creditos_extracurriculares = creditos_extracurriculares
        self.vigente = vigente
        self.nuevo = nuevo

    @property
    def anio_aprobacion(self) -> int:
        return self.__anio_aprobacion

    @property
    def codigo_escuela(self) -> str:
        return self.__codigo_escuela

    @property
    def creditos_obligatorios(self) -> Decimal:
        return self.__creditos_obligatorios

    @creditos_obligatorios.setter
    def creditos_obligatorios(self, valor):
        self.__creditos_obligatorios = validar_decimal(
            valor, "creditos_obligatorios", minimo=0)

    @property
    def creditos_electivos(self) -> Decimal:
        return self.__creditos_electivos

    @creditos_electivos.setter
    def creditos_electivos(self, valor):
        self.__creditos_electivos = validar_decimal(
            valor, "creditos_electivos", minimo=0)

    @property
    def creditos_extracurriculares(self) -> Decimal:
        return self.__creditos_extracurriculares

    @creditos_extracurriculares.setter
    def creditos_extracurriculares(self, valor):
        self.__creditos_extracurriculares = validar_decimal(
            valor, "creditos_extracurriculares", minimo=0)

    @property
    def creditos_totales(self) -> Decimal:
        return (self.creditos_obligatorios + self.creditos_electivos
                + self.creditos_extracurriculares)

    @property
    def vigente(self) -> bool:
        return bool(self.__vigente)

    @vigente.setter
    def vigente(self, valor):
        self.__vigente = validar_bandera(valor, "vigente")

    @property
    def nuevo(self) -> bool:
        return bool(self.__nuevo)

    @nuevo.setter
    def nuevo(self, valor):
        self.__nuevo = validar_bandera(valor, "nuevo")

    def resumen(self) -> str:
        return (f"Plan {self.nombre} ({self.anio_aprobacion}): "
                f"{self.creditos_totales} créditos, vigente={self.vigente}.")


class EscuelaProfesional(RegistroConNombre):
    # El caso no señala un máximo para el nombre de la escuela.
    MAX_NOMBRE = None

    def __init__(self, codigo, nombre, informacion_general, perfil_egresado,
                 codigo_director, codigo_secretario):
        super().__init__(nombre)
        self.__codigo = validar_texto(codigo, "codigo")
        self.__informacion_general = validar_texto(informacion_general, "informacion_general")
        self.__perfil_egresado = validar_texto(perfil_egresado, "perfil_egresado")
        self.__codigo_director = validar_texto(codigo_director, "codigo_director")
        self.__codigo_secretario = validar_texto(codigo_secretario, "codigo_secretario")

    @property
    def codigo(self) -> str:
        return self.__codigo

    @property
    def informacion_general(self) -> str:
        return self.__informacion_general

    @property
    def perfil_egresado(self) -> str:
        return self.__perfil_egresado

    @property
    def codigo_director(self) -> str:
        return self.__codigo_director

    @property
    def codigo_secretario(self) -> str:
        return self.__codigo_secretario

    def resumen(self) -> str:
        return (f"Escuela {self.codigo}: {self.nombre}, "
                f"director={self.codigo_director}, secretario={self.codigo_secretario}.")


class EstadoPeriodo(IntEnum):
    PLANIFICADO = 1
    EN_CURSO = 2
    MATRICULA_CERRADA = 3
    FINALIZADO = 4


class PeriodoAcademico(RegistroConNombre):
    MAX_NOMBRE = 45

    def __init__(self, codigo, nombre, numero, anio, fecha_inicio, fecha_fin,
                 inicio_matricula, fin_matricula, es_verano=0,
                 nota_minima=11, estado=EstadoPeriodo.PLANIFICADO):
        super().__init__(nombre)
        self.__codigo = validar_texto(codigo, "codigo")
        self.__numero = validar_entero(numero, "numero")
        self.__anio = validar_entero(anio, "anio")
        self.actualizar_fechas(fecha_inicio, fecha_fin)
        self.actualizar_matricula(inicio_matricula, fin_matricula)
        self.es_verano = es_verano
        self.nota_minima = nota_minima
        self.estado = estado

    @property
    def codigo(self) -> str:
        return self.__codigo

    @property
    def numero(self) -> int:
        return self.__numero

    @property
    def anio(self) -> int:
        return self.__anio

    @property
    def fecha_inicio(self) -> date:
        return self.__fecha_inicio

    @property
    def fecha_fin(self) -> date:
        return self.__fecha_fin

    @property
    def inicio_matricula(self) -> date:
        return self.__inicio_matricula

    @property
    def fin_matricula(self) -> date:
        return self.__fin_matricula

    def actualizar_fechas(self, inicio, fin):
        inicio, fin = validar_intervalo(inicio, fin)
        self.__fecha_inicio, self.__fecha_fin = inicio, fin

    def actualizar_matricula(self, inicio, fin):
        inicio, fin = validar_intervalo(inicio, fin)
        self.__inicio_matricula, self.__fin_matricula = inicio, fin

    @property
    def es_verano(self) -> bool:
        return bool(self.__es_verano)

    @es_verano.setter
    def es_verano(self, valor):
        self.__es_verano = validar_bandera(valor, "es_verano")

    @property
    def nota_minima(self) -> Decimal:
        return self.__nota_minima

    @nota_minima.setter
    def nota_minima(self, valor):
        self.__nota_minima = validar_decimal(valor, "nota_minima", minimo=0, maximo=20)

    @property
    def estado(self) -> EstadoPeriodo:
        return self.__estado

    @estado.setter
    def estado(self, valor):
        if not isinstance(valor, EstadoPeriodo) and type(valor) is not int:
            raise TypeError("estado debe ser un entero o un EstadoPeriodo.")
        try:
            nuevo_estado = EstadoPeriodo(valor)
        except ValueError:
            raise ValueError("estado solo admite valores del 1 al 4.") from None
        self.__estado = nuevo_estado

    def resumen(self) -> str:
        return (f"Periodo {self.nombre}: {self.fecha_inicio} a {self.fecha_fin}, "
                f"estado={self.estado.name}, nota mínima={self.nota_minima}.")


class Persona(ABC):
    def __init__(self, dni, nombres, apellidos):
        self.__dni = validar_texto(dni, "dni")
        self.__nombres = validar_texto(nombres, "nombres")
        self.__apellidos = validar_texto(apellidos, "apellidos")

    @property
    def dni(self) -> str:
        return self.__dni

    @property
    def nombres(self) -> str:
        return self.__nombres

    @property
    def apellidos(self) -> str:
        return self.__apellidos

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos}".strip()

    @property
    @abstractmethod
    def rol(self) -> str:
        """Cada persona concreta debe indicar su rol universitario."""

    def __str__(self) -> str:
        return f"{self.nombre_completo} | Rol: {self.rol}"


class Estudiante(Persona):
    def __init__(self, dni, nombres, apellidos, codigo_estudiante, codigo_escuela):
        super().__init__(dni, nombres, apellidos)
        self.__codigo_estudiante = validar_texto(codigo_estudiante, "codigo_estudiante")
        self.__codigo_escuela = validar_texto(codigo_escuela, "codigo_escuela")

    @property
    def codigo_estudiante(self) -> str:
        return self.__codigo_estudiante

    @property
    def codigo_escuela(self) -> str:
        return self.__codigo_escuela

    @property
    def rol(self) -> str:
        return "Estudiante"


class Docente(Persona):
    def __init__(self, dni, nombres, apellidos, codigo_docente):
        super().__init__(dni, nombres, apellidos)
        self.__codigo_docente = validar_texto(codigo_docente, "codigo_docente")

    @property
    def codigo_docente(self) -> str:
        return self.__codigo_docente

    @property
    def rol(self) -> str:
        return "Docente"


def crear_curso(**cambios):
    datos = dict(codigo="IS-282", nombre="Programación orientada a objetos",
                 creditos="4.25", horas_teoricas=2, horas_practicas=3,
                 horas_seminario=0, horas_virtuales=1)
    datos.update(cambios)
    return Curso(**datos)


def crear_plan(**cambios):
    datos = dict(nombre="Plan 2026", anio_aprobacion=2026, codigo_escuela="EP-IS",
                 creditos_obligatorios=180, creditos_electivos=20,
                 creditos_extracurriculares=5, vigente=1, nuevo=0)
    datos.update(cambios)
    return PlanEstudio(**datos)


def crear_periodo(**cambios):
    datos = dict(codigo="2026-II", nombre="2026-II", numero=2, anio=2026,
                 fecha_inicio=date(2026, 8, 17), fecha_fin=date(2026, 12, 18),
                 inicio_matricula=date(2026, 8, 1), fin_matricula=date(2026, 8, 16),
                 es_verano=0, nota_minima="10.5", estado=EstadoPeriodo.PLANIFICADO)
    datos.update(cambios)
    return PeriodoAcademico(**datos)


def crear_escuela(**cambios):
    datos = dict(codigo="EP-IS", nombre="Ingeniería de Sistemas",
                 informacion_general="Escuela profesional de la universidad",
                 perfil_egresado="Diseña y desarrolla soluciones informáticas",
                 codigo_director="DOC-001", codigo_secretario="DOC-002")
    datos.update(cambios)
    return EscuelaProfesional(**datos)


def ejecutar_pruebas():
    """Cada regla tiene ejemplos aceptados y errores capturados con try/except."""
    aceptados = rechazados = 0

    def aceptar(etiqueta, operacion):
        nonlocal aceptados
        try:
            resultado = operacion()
        except Exception as error:
            raise AssertionError(f"FALLO: {etiqueta}: {error}") from error
        aceptados += 1
        print(f"ACEPTADO | {etiqueta} | {resultado}")

    def rechazar(etiqueta, operacion, error_esperado=(ValueError, TypeError, AttributeError)):
        nonlocal rechazados
        try:
            operacion()
        except error_esperado as error:
            rechazados += 1
            print(f"RECHAZADO | {etiqueta} | {error}")
        else:
            raise AssertionError(f"FALLO: {etiqueta}: se aceptó un dato inválido.")

    print("PRUEBAS DE NOMBRES")
    for fabrica, limite in ((crear_curso, 200), (crear_plan, 36), (crear_periodo, 45)):
        aceptar(f"{fabrica.__name__}: nombre de {limite} caracteres",
                lambda f=fabrica, n=limite: f(nombre="A" * n).nombre)
        rechazar(f"{fabrica.__name__}: nombre demasiado largo",
                 lambda f=fabrica, n=limite: f(nombre="A" * (n + 1)))
    for fabrica in (crear_curso, crear_plan, crear_periodo, crear_escuela):
        aceptar(f"{fabrica.__name__}: nombre válido", lambda f=fabrica: f().nombre)
        rechazar(f"{fabrica.__name__}: nombre vacío", lambda f=fabrica: f(nombre="   "))
    aceptar("Escuela sin límite de longitud indicado", lambda: crear_escuela(nombre="A" * 300).nombre)
    curso = crear_curso()
    aceptar("Cambio válido del nombre", lambda: setattr(curso, "nombre", "POO"))
    rechazar("Cambio del nombre a vacío", lambda: setattr(curso, "nombre", ""))

    print("\nPRUEBAS DE CURSO")
    otro_curso = crear_curso()
    assert curso.id_curso != otro_curso.id_curso
    aceptar("Identificador generado", lambda: curso.id_curso)
    rechazar("Identificador inmutable", lambda: setattr(curso, "id_curso", uuid4()), AttributeError)
    for valor in ("0.01", "4.25", "4.000"):
        aceptar(f"Créditos {valor}", lambda v=valor: crear_curso(creditos=v).creditos)
    for valor in (0, -1, "4.251", "NaN", "Infinity"):
        rechazar(f"Créditos inválidos {valor}", lambda v=valor: setattr(curso, "creditos", v))
    for campo in ("horas_teoricas", "horas_practicas", "horas_seminario", "horas_virtuales"):
        for valor in (0, 255):
            aceptar(f"{campo}={valor}", lambda c=campo, v=valor: setattr(curso, c, v))
        for valor in (-1, 256, 1.5):
            rechazar(f"{campo}={valor}", lambda c=campo, v=valor: setattr(curso, c, v))
    curso = crear_curso()
    assert curso.horas_totales == 6
    curso.horas_practicas = 5
    assert curso.horas_totales == 8
    aceptar("Horas totales recalculadas", lambda: curso.horas_totales)
    rechazar("Edición del total de horas", lambda: setattr(curso, "horas_totales", 999), AttributeError)

    print("\nPRUEBAS DE SECCIÓN")
    aceptar("Sección con vacantes positivas", lambda: Seccion("A", "IS-282", "2026-II", 2).vacantes)
    for valor in (0, -1, 1.5):
        rechazar(f"Vacantes inválidas {valor}", lambda v=valor: Seccion("A", "IS-282", "2026-II", v))
    seccion = Seccion("A", "IS-282", "2026-II", 2)
    aceptar("Matricular con cupo", seccion.matricular)
    aceptar("Ocupar el último cupo", seccion.matricular)
    assert seccion.matriculados == 2 and seccion.vacantes_disponibles == 0
    rechazar("Matricular en sección llena", seccion.matricular)
    rechazar("Reducir vacantes por debajo de matriculados", lambda: setattr(seccion, "vacantes", 1))
    aceptar("Vacantes iguales a matriculados", lambda: setattr(seccion, "vacantes", 2))
    aceptar("Retirar libera un cupo", seccion.retirar)
    assert seccion.matriculados == 1 and seccion.vacantes_disponibles == 1
    aceptar("Vacantes disponibles calculadas", lambda: seccion.vacantes_disponibles)
    rechazar("Editar matriculados directamente", lambda: setattr(seccion, "matriculados", 100), AttributeError)
    rechazar("Editar vacantes disponibles", lambda: setattr(seccion, "vacantes_disponibles", 100), AttributeError)
    seccion.retirar()
    rechazar("Retirar con cero matriculados", seccion.retirar)

    print("\nPRUEBAS DE PLAN Y BANDERAS")
    plan = crear_plan()
    for campo in ("creditos_obligatorios", "creditos_electivos", "creditos_extracurriculares"):
        aceptar(f"{campo}=0", lambda c=campo: setattr(plan, c, 0))
        aceptar(f"{campo}=12.5", lambda c=campo: setattr(plan, c, "12.5"))
        rechazar(f"{campo} negativo", lambda c=campo: setattr(plan, c, -1))
    plan = crear_plan()
    assert plan.creditos_totales == Decimal("205")
    plan.creditos_electivos = 25
    assert plan.creditos_totales == Decimal("210")
    aceptar("Créditos totales recalculados", lambda: plan.creditos_totales)
    rechazar("Edición del total de créditos", lambda: setattr(plan, "creditos_totales", 999), AttributeError)
    periodo = crear_periodo()
    for objeto, campo in ((plan, "vigente"), (plan, "nuevo"), (periodo, "es_verano")):
        for valor in (0, 1, False, True):
            aceptar(f"{campo}={valor}", lambda o=objeto, c=campo, v=valor: setattr(o, c, v))
            assert type(getattr(objeto, campo)) is bool
        for valor in (2, -1, "1", 1.0):
            rechazar(f"{campo} inválido {valor!r}", lambda o=objeto, c=campo, v=valor: setattr(o, c, v))
    # Solo en la prueba se inspecciona el almacenamiento privado.
    assert type(plan._PlanEstudio__vigente) is int
    assert type(plan._PlanEstudio__nuevo) is int
    assert type(periodo._PeriodoAcademico__es_verano) is int

    print("\nPRUEBAS DE PERIODO")
    for metodo in (periodo.actualizar_fechas, periodo.actualizar_matricula):
        aceptar("Intervalo ordenado", lambda m=metodo: m(date(2026, 1, 1), date(2026, 2, 1)))
        aceptar("Inicio y fin iguales", lambda m=metodo: m(date(2026, 3, 1), date(2026, 3, 1)))
        rechazar("Intervalo invertido", lambda m=metodo: m(date(2026, 5, 1), date(2026, 4, 1)))
        rechazar("Fechas como texto", lambda m=metodo: m("2026-01-01", "2026-02-01"))
    periodo = crear_periodo()
    antes = (periodo.fecha_inicio, periodo.fecha_fin)
    rechazar("Actualización inválida conserva ambas fechas", lambda: periodo.actualizar_fechas(date(2027, 1, 1), date(2026, 1, 1)))
    assert (periodo.fecha_inicio, periodo.fecha_fin) == antes
    antes = (periodo.inicio_matricula, periodo.fin_matricula)
    rechazar("Actualización inválida conserva matrícula", lambda: periodo.actualizar_matricula(date(2027, 1, 1), date(2026, 1, 1)))
    assert (periodo.inicio_matricula, periodo.fin_matricula) == antes
    aceptar("Ambas fechas cambian juntas", lambda: periodo.actualizar_fechas(date(2027, 3, 1), date(2027, 7, 1)))
    for campo in ("fecha_inicio", "fecha_fin", "inicio_matricula", "fin_matricula"):
        rechazar(f"Edición individual de {campo}", lambda c=campo: setattr(periodo, c, date(2026, 1, 1)), AttributeError)
    for valor in (0, "10.5", 20):
        aceptar(f"Nota mínima {valor}", lambda v=valor: setattr(periodo, "nota_minima", v))
    for valor in (-1, "20.01", "NaN"):
        rechazar(f"Nota inválida {valor}", lambda v=valor: setattr(periodo, "nota_minima", v))
    for estado in EstadoPeriodo:
        aceptar(f"Estado {estado.name}", lambda e=estado: setattr(periodo, "estado", e))
    aceptar("Estado numérico 2 convertido a enum", lambda: setattr(periodo, "estado", 2))
    for valor in (7, 0, 5, True, 2.0):
        rechazar(f"Estado inválido {valor}", lambda v=valor: setattr(periodo, "estado", v))

    print("\nPRUEBAS DE ABSTRACCIÓN Y PERSONAS")
    aceptar("Registro concreto", lambda: crear_curso().resumen())
    rechazar("Instanciar RegistroConNombre", lambda: RegistroConNombre("Registro"), TypeError)
    class RegistroIncompleto(RegistroConNombre):
        pass
    rechazar("Subclase sin resumen", lambda: RegistroIncompleto("Registro"), TypeError)
    estudiante = Estudiante("01234567", "Ana", "Quispe", "EST-001", "EP-IS")
    docente = Docente("12345678", "Luis", "Ramos", "DOC-001")
    aceptar("Estudiante con rol y nombre completo", lambda: str(estudiante))
    aceptar("Docente con rol y nombre completo", lambda: str(docente))
    assert estudiante.nombre_completo == "Ana Quispe"
    assert estudiante.rol == "Estudiante" and docente.rol == "Docente"
    rechazar("Instanciar Persona", lambda: Persona("01234567", "Ana", "Quispe"), TypeError)
    class PersonaIncompleta(Persona):
        pass
    rechazar("Subclase sin rol", lambda: PersonaIncompleta("01234567", "Ana", "Quispe"), TypeError)

    print("\nPRUEBAS DE REFERENCIAS COMO TEXTO")
    escuela = crear_escuela()
    referencias = (seccion.codigo_curso, seccion.codigo_periodo, plan.codigo_escuela,
                   escuela.codigo_director, escuela.codigo_secretario, estudiante.codigo_escuela)
    aceptar("Todos los códigos de referencia son str", lambda: referencias)
    assert all(type(codigo) is str for codigo in referencias)
    rechazar("Sección recibe un objeto Curso", lambda: Seccion("B", curso, "2026-II", 2), TypeError)
    rechazar("Sección recibe un objeto Periodo", lambda: Seccion("B", "IS-282", periodo, 2), TypeError)
    rechazar("Plan recibe un objeto Escuela", lambda: crear_plan(codigo_escuela=escuela), TypeError)
    rechazar("Escuela recibe objeto en director", lambda: crear_escuela(codigo_director=docente), TypeError)
    rechazar("Escuela recibe objeto en secretario", lambda: crear_escuela(codigo_secretario=docente), TypeError)
    rechazar("Estudiante recibe objeto Escuela", lambda: Estudiante("01234567", "Ana", "Quispe", "EST-001", escuela), TypeError)

    print("\nPOLIMORFISMO DE REGISTROS")
    registros = [crear_curso(), crear_plan(), crear_escuela(), crear_periodo()]
    for registro in registros:
        print(registro.resumen())  # Sin isinstance ni condiciones por tipo.
    print("\nPOLIMORFISMO DE PERSONAS")
    for persona in (estudiante, docente):
        print(persona)
    print(f"\nRESULTADO: {aceptados} casos válidos aceptados, "
          f"{rechazados} casos inválidos rechazados. Todas las verificaciones pasaron.")


if __name__ == "__main__":
    ejecutar_pruebas()
