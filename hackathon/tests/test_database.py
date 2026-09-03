import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.articulos_db import crear_articulo
from database.campanas_db import crear_campana
from database.centros_db import agregar_campana_a_centro, crear_centro, obtener_centro
from database.exceptions import InsufficientStockError
from database.inventario import obtener_stock
from database.json_manager import get_data_dir, set_data_dir
from database.movimientos_db import registrar_ajuste, registrar_entrega, registrar_merma, registrar_recepcion, registrar_transferencia
from database.usuarios_db import crear_usuario, validar_login


@pytest.fixture(autouse=True)
def temp_data_dir(tmp_path):
    original = get_data_dir()
    set_data_dir(tmp_path)
    yield
    set_data_dir(original)


def test_creacion_usuario_y_login():
    usuario = crear_usuario("Test User", "testuser", "1234", "voluntario")
    assert usuario["id"].startswith("U")
    assert validar_login("testuser", "1234")["id"] == usuario["id"]


def test_creacion_campana_y_centro():
    campana = crear_campana("Campaña Test", "2026-10-01", "2026-10-15")
    assert campana["id"].startswith("CAM")

    centro = crear_centro("Centro Test", "Institucion Test", "Ubicacion Test")
    assert centro["id"].startswith("C")

    agregar_campana_a_centro(centro["id"], campana["id"])
    centro_actualizado = obtener_centro(centro["id"])
    assert campana["id"] in centro_actualizado["campanas"]


def test_creacion_articulo_y_recepcion():
    articulo = crear_articulo("Lentejas", "no_perecedero", "kg")
    assert articulo["id"].startswith("A")

    usuario = crear_usuario("Usuario Recepcion", "recepcion1", "1234", "encargado_centro")
    centro = crear_centro("Centro Recepcion", "Institucion Test", "Ciudad X", encargado_id=usuario["id"])
    campana = crear_campana("Campaña Recepcion", "2026-11-01", "2026-11-30")
    agregar_campana_a_centro(centro["id"], campana["id"])

    movimiento = registrar_recepcion(centro["id"], campana["id"], articulo["id"], 25, usuario["id"])
    assert movimiento["tipo"] == "recepcion"
    assert obtener_stock(centro["id"], campana["id"], articulo["id"]) == 25


def test_entrega_y_merma():
    usuario = crear_usuario("Usuario Operativo", "op1", "1234", "encargado_centro")
    centro = crear_centro("Centro Operativo", "Institucion Test", "Ciudad Y", encargado_id=usuario["id"])
    campana = crear_campana("Campaña Operativa", "2026-12-01", "2026-12-30")
    agregar_campana_a_centro(centro["id"], campana["id"])
    articulo = crear_articulo("Pan", "perecedero", "caja")

    registrar_recepcion(centro["id"], campana["id"], articulo["id"], 20, usuario["id"])
    registrar_entrega(centro["id"], campana["id"], articulo["id"], 5, usuario["id"])
    registrar_merma(centro["id"], campana["id"], articulo["id"], 2, usuario["id"], "caducidad")

    assert obtener_stock(centro["id"], campana["id"], articulo["id"]) == 13


def test_transferencia_y_ajuste():
    usuario1 = crear_usuario("Encargado 1", "enc1", "1234", "encargado_centro")
    usuario2 = crear_usuario("Encargado 2", "enc2", "1234", "encargado_centro")
    centro1 = crear_centro("Centro A", "Institucion Test", "Ciudad A", encargado_id=usuario1["id"])
    centro2 = crear_centro("Centro B", "Institucion Test", "Ciudad B", encargado_id=usuario2["id"])
    campana = crear_campana("Campaña Transferencia", "2026-08-01", "2026-08-30")
    agregar_campana_a_centro(centro1["id"], campana["id"])
    agregar_campana_a_centro(centro2["id"], campana["id"])
    articulo = crear_articulo("Galletas", "no_perecedero", "caja")

    registrar_recepcion(centro1["id"], campana["id"], articulo["id"], 30, usuario1["id"])
    transferencia = registrar_transferencia(centro1["id"], centro2["id"], campana["id"], articulo["id"], 10, usuario1["id"])
    assert transferencia["transferencia_id"]
    assert obtener_stock(centro1["id"], campana["id"], articulo["id"]) == 20
    assert obtener_stock(centro2["id"], campana["id"], articulo["id"]) == 10

    registrar_ajuste(centro1["id"], campana["id"], articulo["id"], 2, usuario1["id"], "positivo", "correccion")
    assert obtener_stock(centro1["id"], campana["id"], articulo["id"]) == 22


def test_stock_negativo_bloqueado():
    usuario = crear_usuario("Usuario Stock", "stock1", "1234", "encargado_centro")
    centro = crear_centro("Centro Stock", "Institucion Test", "Ciudad Z", encargado_id=usuario["id"])
    campana = crear_campana("Campaña Stock", "2026-07-01", "2026-07-30")
    agregar_campana_a_centro(centro["id"], campana["id"])
    articulo = crear_articulo("Aceite", "no_perecedero", "bolsa")

    registrar_recepcion(centro["id"], campana["id"], articulo["id"], 5, usuario["id"])
    try:
        registrar_entrega(centro["id"], campana["id"], articulo["id"], 10, usuario["id"])
        assert False, "Se esperaba InsufficientStockError"
    except InsufficientStockError:
        pass


def test_movimientos_tienen_actor_fecha():
    usuario = crear_usuario("Actor", "actor1", "1234", "voluntario")
    centro = crear_centro("Centro Fecha", "Institucion Test", "Ciudad F", encargado_id=usuario["id"])
    campana = crear_campana("Campaña Fecha", "2026-06-01", "2026-06-30")
    agregar_campana_a_centro(centro["id"], campana["id"])
    articulo = crear_articulo("Jabón", "limpieza", "pieza")

    movimiento = registrar_recepcion(centro["id"], campana["id"], articulo["id"], 4, usuario["id"])
    assert movimiento["actor_id"] == usuario["id"]
    assert "T" in movimiento["fecha"]


if __name__ == "__main__":
    test_creacion_usuario_y_login()
    test_creacion_campana_y_centro()
    test_creacion_articulo_y_recepcion()
    test_entrega_y_merma()
    test_transferencia_y_ajuste()
    test_stock_negativo_bloqueado()
    test_movimientos_tienen_actor_fecha()
    print("Todos los tests básicos de la base de datos pasaron.")
