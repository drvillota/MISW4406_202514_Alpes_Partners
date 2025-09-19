class TipoObjetoNoExisteEnDominioColaboracionesExcepcion(Exception):
    def __init__(self, mensaje="El tipo de objeto no existe en el dominio de Colaboraciones"):
        super().__init__(mensaje)
