"""Entidades y agregación del dominio de colaboraciones

Este archivo define las entidades principales y la raíz de agregación
para contratos y colaboraciones con influencers en el dominio de marketing.
"""

from dataclasses import dataclass, field
from typing import List

from core.seedworks.entidades import Entidad 
from core.seedworks.objetos_valor import (
    Identificador,
    Email,
    EstadoColaboracion,
    EstadoCampania,
    EstadoContrato,
    Periodo,
    RedSocial,
    IdentidadEnRed,
    NombreCampania,
    Publicacion,
)


# -------------------------------
# ENTIDADES
# -------------------------------

@dataclass
class Influencer(Entidad):
    nombre: str
    email: Email
    identidades: List[IdentidadEnRed] = field(default_factory=list)

    def agregar_identidad(self, identidad: IdentidadEnRed):
        if identidad in self.identidades:
            raise ValueError("El influencer ya tiene esta identidad en la red")
        self.identidades.append(identidad)

@dataclass
class Campania(Entidad):
    nombre: NombreCampania
    marca: str
    periodo: Periodo
    estado: EstadoCampania

@dataclass
class Contrato(Entidad):
    periodo: Periodo
    estado: EstadoContrato

# -------------------------------
# AGREGACIÓN RAÍZ
# -------------------------------

@dataclass
class Colaboracion:
    id: Identificador
    campania: Campania
    influencer: Influencer
    contrato: Contrato
    estado: EstadoColaboracion
    publicaciones: List[str] = field(default_factory=list)
    
    def firmar_contrato(self):
        if self.contrato.estado.valor != "PENDIENTE":
            raise ValueError("Solo se pueden firmar contratos en estado PENDIENTE")
        self.contrato = Contrato(
            id=self.contrato.id,
            periodo=self.contrato.periodo,
            estado=EstadoContrato("FIRMADO"),
        )
        self.estado = EstadoColaboracion("VIGENTE")

    def cancelar(self):
        self.contrato = Contrato(
            id=self.contrato.id,
            periodo=self.contrato.periodo,
            estado=EstadoContrato("CANCELADO"),
        )
        self.estado = EstadoColaboracion("CANCELADA")

    def finalizar(self):
        self.estado = EstadoColaboracion("FINALIZADA")
    
    def registrar_publicacion(self, publicacion: Publicacion):
        """Agrega una publicación asociada a esta colaboración"""
        self.publicaciones.append(publicacion)