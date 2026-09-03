import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.articulos_db import crear_articulo
from database.campanas_db import crear_campana
from database.centros_db import agregar_campana_a_centro, crear_centro
from database.exceptions import InsufficientStockError
from database.inventario import obtener_stock
from database.json_manager import get_data_dir, set_data_dir
from database.movimientos_db import (
    registrar_ajuste,
    registrar_entrega,
    registrar_merma,
    registrar_recepcion,
    registrar_transferencia,
)
from database.usuarios_db import crear_usuario


@pytest.fixture(autouse=True)
def temp_data_dir(tmp_path):
    original = get_data_dir()
    set_data_dir(tmp_path)
    yield
    set_data_dir(original)


def test_secuencia_basica_inventario():
    u1 = crear_usuario('U100', 'u100', '1234', 'encargado_centro')
    u2 = crear_usuario('U101', 'u101', '1234', 'encargado_centro')
    c1 = crear_centro('Centro A Real', 'Inst', 'Loc A', encargado_id=u1['id'])
    c2 = crear_centro('Centro B Real', 'Inst', 'Loc B', encargado_id=u2['id'])
    camp = crear_campana('Camp Real', '2026-11-01', '2026-11-30')
    agregar_campana_a_centro(c1['id'], camp['id'])
    agregar_campana_a_centro(c2['id'], camp['id'])
    art = crear_articulo('Arroz Real', 'no_perecedero', 'kg')

    registrar_recepcion(c1['id'], camp['id'], art['id'], 100, u1['id'])
    assert obtener_stock(c1['id'], camp['id'], art['id']) == 100.0

    registrar_entrega(c1['id'], camp['id'], art['id'], 30, u1['id'])
    assert obtener_stock(c1['id'], camp['id'], art['id']) == 70.0

    registrar_merma(c1['id'], camp['id'], art['id'], 10, u1['id'], 'caducidad')
    assert obtener_stock(c1['id'], camp['id'], art['id']) == 60.0

    t = registrar_transferencia(c1['id'], c2['id'], camp['id'], art['id'], 20, u1['id'])
    assert t['transferencia_id']
    assert obtener_stock(c1['id'], camp['id'], art['id']) == 40.0
    assert obtener_stock(c2['id'], camp['id'], art['id']) == 20.0

    try:
        registrar_entrega(c1['id'], camp['id'], art['id'], 100, u1['id'])
        assert False, 'Se esperaba rechazo por stock insuficiente'
    except InsufficientStockError:
        pass
    assert obtener_stock(c1['id'], camp['id'], art['id']) == 40.0

    registrar_ajuste(c1['id'], camp['id'], art['id'], 5, u1['id'], 'positivo', 'Correccion')
    registrar_ajuste(c1['id'], camp['id'], art['id'], 3, u1['id'], 'negativo', 'Ajuste de inventario')
    assert obtener_stock(c1['id'], camp['id'], art['id']) == 42.0


def test_validaciones_y_trazabilidad():
    u = crear_usuario('U200', 'u200', '1234', 'voluntario')
    c = crear_centro('Centro Historial', 'Inst', 'Loc H', encargado_id=u['id'])
    camp = crear_campana('Camp Hist', '2026-12-01', '2026-12-15')
    agregar_campana_a_centro(c['id'], camp['id'])
    art = crear_articulo('Leche Hist', 'perecedero', 'caja')

    m = registrar_recepcion(c['id'], camp['id'], art['id'], 4, u['id'])
    assert m['actor_id'] == u['id']
    assert 'T' in m['fecha']

    try:
        registrar_recepcion(c['id'], camp['id'], art['id'], 0, u['id'])
        assert False
    except Exception:
        pass

    try:
        registrar_merma(c['id'], camp['id'], art['id'], 2, u['id'], '')
        assert False
    except Exception:
        pass


def test_inventario_y_validaciones_del_requisito_hackathon():
    u1 = crear_usuario('U300', 'u300', '1234', 'encargado_centro')
    u2 = crear_usuario('U301', 'u301', '1234', 'encargado_centro')
    c1 = crear_centro('Centro A', 'Inst', 'Loc A', encargado_id=u1['id'])
    c2 = crear_centro('Centro B', 'Inst', 'Loc B', encargado_id=u2['id'])
    camp = crear_campana('Camp Hack', '2026-09-10', '2026-09-20')
    agregar_campana_a_centro(c1['id'], camp['id'])
    agregar_campana_a_centro(c2['id'], camp['id'])
    art = crear_articulo('Papa', 'no_perecedero', 'kg')

    registrar_recepcion(c1['id'], camp['id'], art['id'], 100, u1['id'])
    assert obtener_stock(c1['id'], camp['id'], art['id']) == 100.0

    registrar_entrega(c1['id'], camp['id'], art['id'], 30, u1['id'])
    assert obtener_stock(c1['id'], camp['id'], art['id']) == 70.0

    registrar_merma(c1['id'], camp['id'], art['id'], 10, u1['id'], 'caducidad')
    assert obtener_stock(c1['id'], camp['id'], art['id']) == 60.0

    registrar_ajuste(c1['id'], camp['id'], art['id'], 20, u1['id'], 'positivo', 'Ajuste manual')
    assert obtener_stock(c1['id'], camp['id'], art['id']) == 80.0

    registrar_ajuste(c1['id'], camp['id'], art['id'], 15, u1['id'], 'negativo', 'Ajuste manual')
    assert obtener_stock(c1['id'], camp['id'], art['id']) == 65.0

    transfer = registrar_transferencia(c1['id'], c2['id'], camp['id'], art['id'], 20, u1['id'])
    assert transfer['transferencia_id']
    assert obtener_stock(c1['id'], camp['id'], art['id']) == 45.0
    assert obtener_stock(c2['id'], camp['id'], art['id']) == 20.0

    try:
        registrar_entrega(c1['id'], camp['id'], art['id'], 100, u1['id'])
        assert False, 'Debe rechazarse entrega mayor al stock disponible'
    except InsufficientStockError:
        pass
    assert obtener_stock(c1['id'], camp['id'], art['id']) == 45.0

    try:
        registrar_merma(c1['id'], camp['id'], art['id'], 5, u1['id'], '')
        assert False, 'Merma sin motivo debe rechazarse'
    except Exception:
        pass

    try:
        registrar_recepcion(c1['id'], camp['id'], art['id'], 0, u1['id'])
        assert False, 'Cantidad 0 debe rechazarse'
    except Exception:
        pass

    try:
        registrar_recepcion(c1['id'], camp['id'], art['id'], -5, u1['id'])
        assert False, 'Cantidad negativa debe rechazarse'
    except Exception:
        pass

    try:
        registrar_transferencia(c1['id'], c1['id'], camp['id'], art['id'], 5, u1['id'])
        assert False, 'Transferencia al mismo centro debe rechazarse'
    except Exception:
        pass

    centro_inactivo = crear_centro('Centro Inactivo', 'Inst', 'Loc I', encargado_id=u1['id'])
    centro_inactivo['activo'] = False
    from database.json_manager import save_json
    from database.centros_db import _load_centros
    centros = _load_centros()
    centros.append(centro_inactivo)
    save_json('centros.json', centros)
    try:
        registrar_recepcion(centro_inactivo['id'], camp['id'], art['id'], 5, u1['id'])
        assert False, 'Centro inactivo debe rechazarse'
    except Exception:
        pass

    camp_inactiva = crear_campana('Camp Inactiva', '2026-09-21', '2026-09-25')
    from database.campanas_db import desactivar_campana
    desactivar_campana(camp_inactiva['id'])
    try:
        registrar_recepcion(c1['id'], camp_inactiva['id'], art['id'], 5, u1['id'])
        assert False, 'Campaña inactiva debe rechazarse'
    except Exception:
        pass


if __name__ == '__main__':
    test_secuencia_basica_inventario()
    test_validaciones_y_trazabilidad()
    test_inventario_y_validaciones_del_requisito_hackathon()
    print('Pruebas de revisión real ejecutadas correctamente.')
