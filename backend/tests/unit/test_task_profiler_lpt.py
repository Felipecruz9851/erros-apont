import json
import os
import pytest
from backend.app.tasks.profiler import TaskProfiler


def test_task_profiler_records_duration_and_moving_average(tmp_path):
    storage_file = str(tmp_path / "test_task_times.json")
    profiler = TaskProfiler(storage_file=storage_file)

    # 1. Primeiro registro
    profiler.record_duration("task_colchoes", 5.0, grupo="consumo_ordem", local="COLCHOES", rows_extracted=100)
    assert os.path.exists(storage_file)

    with open(storage_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "task_colchoes" in data
    assert data["task_colchoes"]["avg_duration_seconds"] == 5.0
    assert data["task_colchoes"]["count"] == 1

    # 2. Segundo registro (atualiza média móvel: (5.0 + 7.0) / 2 = 6.0)
    profiler.record_duration("task_colchoes", 7.0, grupo="consumo_ordem", local="COLCHOES", rows_extracted=150)
    with open(storage_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["task_colchoes"]["avg_duration_seconds"] == 6.0
    assert data["task_colchoes"]["last_duration_seconds"] == 7.0
    assert data["task_colchoes"]["min_duration_seconds"] == 5.0
    assert data["task_colchoes"]["max_duration_seconds"] == 7.0
    assert data["task_colchoes"]["count"] == 2


def test_task_profiler_orders_tasks_lpt_longest_processing_time_first(tmp_path):
    storage_file = str(tmp_path / "test_task_times.json")
    profiler = TaskProfiler(storage_file=storage_file)

    # Simula históricos com tempos bem diferentes:
    # COLCHOES é lenta (8.5s), CORTE é média (5.0s), TAPA_FURO é rápida (0.4s)
    profiler.record_duration("tarefa_tapa_furo", 0.4, grupo="consumo", local="TAPA FURO")
    profiler.record_duration("tarefa_colchoes", 8.5, grupo="consumo", local="COLCHOES")
    profiler.record_duration("tarefa_corte", 5.0, grupo="consumo", local="CORTE")

    input_tasks = [
        {"task_id": "tarefa_tapa_furo", "local": "TAPA FURO", "grupo": "consumo"},
        {"task_id": "tarefa_colchoes", "local": "COLCHOES", "grupo": "consumo"},
        {"task_id": "tarefa_corte", "local": "CORTE", "grupo": "consumo"},
        {"task_id": "tarefa_sem_historico", "local": "DESCONHECIDO", "grupo": "outro_grupo"},
    ]

    ordered = profiler.order_tasks_lpt(input_tasks)

    # A tarefa mais lenta deve estar no topo da fila (LPT)
    assert ordered[0]["task_id"] == "tarefa_colchoes"
    # A intermediária em segundo
    assert ordered[1]["task_id"] == "tarefa_corte"
    # A mais rápida deve ficar para o final
    assert ordered[-1]["task_id"] == "tarefa_tapa_furo"
