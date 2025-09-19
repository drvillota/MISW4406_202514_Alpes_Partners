# src/colaboraciones/modulos/dominio/fabricas.py
from dataclasses import dataclass
from modulos.dominio.entidades import Colaboracion
from modulos.dominio.excepciones import TipoObjetoNoExisteEnDominioColaboracionesExcepcion
from seedwork.dominio.repositorios import Mapeador
from seedwork.dominio.fabricas import Fabrica
from seedwork.dominio.entidades import Entidad
from seedwork.dominio.eventos import EventoDominio


@dataclass
class _FabricaColaboracion(Fabrica):
    def crear_objeto(self, obj: any, mapeador: Mapeador) -> any:
        # Si llega una entidad o evento, lo paso a DTO
        if isinstance(obj, Entidad) or isinstance(obj, EventoDominio):
            return mapeador.entidad_a_dto(obj)
        else:
            # Si llega un DTO, lo paso a entidad de dominio
            colaboracion: Colaboracion = mapeador.dto_a_entidad(obj)
            return colaboracion


@dataclass
class FabricaColaboraciones(Fabrica):
    def crear_objeto(self, obj: any, mapeador: Mapeador) -> any:
        """
        Comportamiento seguro:
         - Si el mapeador declara `obtener_tipo()` y devuelve la clase `Colaboracion`,
           usamos la fábrica especializada.
         - Si el mapeador **no** implementa `obtener_tipo()` (compatibilidad hacia atrás),
           delegamos a la fábrica especializada que es capaz de decidir la dirección
           (entidad->dto o dto->entidad) según el objeto recibido.
         - Si el mapeador implementa `obtener_tipo()` pero devuelve otra cosa, lanzamos excepción.
        """
        # Si el mapeador tiene el método obtener_tipo, lo consultamos
        if hasattr(mapeador, "obtener_tipo") and callable(getattr(mapeador, "obtener_tipo")):
            try:
                tipo = mapeador.obtener_tipo()
            except Exception:
                tipo = None

            if tipo is Colaboracion:
                return _FabricaColaboracion().crear_objeto(obj, mapeador)
            else:
                raise TipoObjetoNoExisteEnDominioColaboracionesExcepcion()

        # Fallback: mapeador antiguo sin obtener_tipo -> intentar mapear según el objeto
        return _FabricaColaboracion().crear_objeto(obj, mapeador)
