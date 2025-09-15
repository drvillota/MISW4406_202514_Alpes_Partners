from abc import ABC
from seedwork.dominio.repositorios import Repositorio


class RepositorioColaboraciones(Repositorio, ABC):
    ...
    
class RepositorioEventosColaboraciones(Repositorio, ABC):
    ...