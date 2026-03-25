"""
Pipeline executor: runs a visual pipeline definition using pandas.
Each node is executed in order (topological sort of the graph).

Node types:
- data_source: reads approved forms for a template → returns DataFrame
- processor: runs custom Python code with pandas → transforms DataFrame
- nivel2_output: aggregates DataFrame → writes to IndicadorNivel2 result
- nivel1_output: aggregates nivel2 results → final Level 1 value

The sandbox executes user Python code with these globals available:
  - pd (pandas)
  - df (input DataFrame from previous node)
  - result (must be set: either DataFrame or scalar float)
"""
import io
import logging
import traceback
import uuid
from collections import deque
from contextlib import redirect_stdout
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

SANDBOX_GLOBALS = {
    "__builtins__": {
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "list": list,
        "dict": dict,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "round": round,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "print": print,
        "isinstance": isinstance,
        "type": type,
    },
    "pd": pd,
}


def execute_node_code(
    code: str, input_df: pd.DataFrame | None, log_output: list[str]
) -> Any:
    """Execute a node's Python code in a restricted sandbox."""
    local_vars = {"df": input_df, "result": None}
    sandbox = {**SANDBOX_GLOBALS}

    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            exec(compile(code, "<pipeline_node>", "exec"), sandbox, local_vars)
        output = buf.getvalue()
        if output:
            log_output.append(f"[stdout] {output.rstrip()}")
        return local_vars.get("result")
    except Exception as e:
        err = traceback.format_exc()
        log_output.append(f"[ERROR] {err}")
        raise RuntimeError(f"Error en nodo: {e}") from e


def _topological_sort(nodes: list[dict], edges: list[dict]) -> list[str]:
    """
    Returns node ids sorted topologically (processing order).
    Raises ValueError if a cycle is detected.
    """
    node_ids = {n["id"] for n in nodes}
    in_degree: dict[str, int] = {nid: 0 for nid in node_ids}
    adjacency: dict[str, list[str]] = {nid: [] for nid in node_ids}

    for edge in edges:
        src = edge.get("source")
        tgt = edge.get("target")
        if src in node_ids and tgt in node_ids:
            adjacency[src].append(tgt)
            in_degree[tgt] += 1

    queue = deque(nid for nid, deg in in_degree.items() if deg == 0)
    result = []

    while queue:
        nid = queue.popleft()
        result.append(nid)
        for neighbor in adjacency[nid]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(node_ids):
        raise ValueError("El grafo del pipeline contiene un ciclo — no puede ejecutarse.")

    return result


async def _load_forms_for_template(
    template_id: str, db: AsyncSession, fecha_inicio=None, fecha_fin=None
) -> pd.DataFrame:
    """
    Load approved forms for a given template into a DataFrame.
    Each row is a form's datos_dinamicos merged with meta fields.
    """
    from app.models.form import Form, FormStatus

    query = select(Form).where(
        Form.plantilla_id == uuid.UUID(template_id),
        Form.estado == FormStatus.approved,
    )
    if fecha_inicio:
        query = query.where(Form.fecha_usuario >= fecha_inicio)
    if fecha_fin:
        query = query.where(Form.fecha_usuario <= fecha_fin)

    result = await db.execute(query)
    forms = result.scalars().all()

    rows = []
    for f in forms:
        row = {
            "_form_id": str(f.id),
            "_fecha_usuario": str(f.fecha_usuario) if f.fecha_usuario else None,
            "_dependency_id": str(f.dependency_id),
            "_informe_cualitativo": f.informe_cualitativo,
        }
        if isinstance(f.datos_dinamicos, dict):
            row.update(f.datos_dinamicos)
        rows.append(row)

    return pd.DataFrame(rows) if rows else pd.DataFrame()


async def execute_pipeline(
    pipeline_def: dict,
    db: AsyncSession,
    fecha_inicio=None,
    fecha_fin=None,
) -> tuple[dict, str]:
    """
    Execute a pipeline definition.
    Returns (resultado_dict, log_string).

    pipeline_def is the value of PipelineDefinicion.grafo:
    {
      "nodes": [
        {"id": "n1", "type": "data_source", "data": {"template_id": "...", "nombre": "..."}},
        {"id": "n2", "type": "processor", "data": {"codigo_python": "...", "nombre": "..."}},
        {"id": "n3", "type": "nivel2_output", "data": {"indicador_nivel2_id": 1, "nombre": "..."}},
        {"id": "n4", "type": "nivel1_output", "data": {"indicador_nivel1_id": 1, "nombre": "..."}}
      ],
      "edges": [
        {"source": "n1", "target": "n2"},
        {"source": "n2", "target": "n3"},
        {"source": "n3", "target": "n4"}
      ]
    }
    """
    log_output: list[str] = []
    resultado: dict[str, Any] = {}

    nodes: list[dict] = pipeline_def.get("nodes", [])
    edges: list[dict] = pipeline_def.get("edges", [])

    if not nodes:
        return {"error": "El pipeline no tiene nodos."}, "No hay nodos en el pipeline."

    log_output.append(f"[INFO] Iniciando pipeline con {len(nodes)} nodos y {len(edges)} aristas.")

    try:
        order = _topological_sort(nodes, edges)
    except ValueError as e:
        log_output.append(f"[ERROR] {e}")
        return {"error": str(e)}, "\n".join(log_output)

    # Build lookup maps
    node_map = {n["id"]: n for n in nodes}
    # Map from node_id → its computed result (DataFrame or float)
    node_results: dict[str, Any] = {}

    # Build reverse edge lookup: node_id → list of predecessor node_ids
    predecessors: dict[str, list[str]] = {n["id"]: [] for n in nodes}
    for edge in edges:
        src = edge.get("source")
        tgt = edge.get("target")
        if src and tgt:
            predecessors[tgt].append(src)

    nivel2_outputs: dict[int, float] = {}  # nivel2_id → computed value

    for node_id in order:
        node = node_map[node_id]
        node_type = node.get("type", "")
        node_data = node.get("data", {})
        node_name = node_data.get("nombre", node_id)

        log_output.append(f"\n[NODE] {node_name} (type={node_type}, id={node_id})")

        # Determine input: last predecessor's result
        pred_ids = predecessors[node_id]
        input_df: pd.DataFrame | None = None
        if pred_ids:
            pred_result = node_results.get(pred_ids[-1])
            if isinstance(pred_result, pd.DataFrame):
                input_df = pred_result
            elif pred_result is not None:
                # Scalar from previous node — wrap into single-row DataFrame
                input_df = pd.DataFrame([{"value": pred_result}])

        try:
            if node_type == "data_source":
                template_id = node_data.get("template_id")
                if not template_id:
                    log_output.append("[WARN] data_source sin template_id — retornando DataFrame vacío.")
                    node_results[node_id] = pd.DataFrame()
                else:
                    df = await _load_forms_for_template(
                        template_id, db, fecha_inicio, fecha_fin
                    )
                    log_output.append(f"[INFO] Cargados {len(df)} formularios aprobados.")
                    node_results[node_id] = df

            elif node_type == "processor":
                code = node_data.get("codigo_python", "")
                if not code.strip():
                    log_output.append("[WARN] processor sin código — pasando DataFrame sin cambios.")
                    node_results[node_id] = input_df if input_df is not None else pd.DataFrame()
                else:
                    result = execute_node_code(code, input_df, log_output)
                    node_results[node_id] = result
                    if isinstance(result, pd.DataFrame):
                        log_output.append(f"[INFO] Resultado: DataFrame con {len(result)} filas.")
                    else:
                        log_output.append(f"[INFO] Resultado escalar: {result}")

            elif node_type == "nivel2_output":
                nivel2_id = node_data.get("indicador_nivel2_id")
                aggregation = node_data.get("aggregation", "mean")  # mean|sum|count
                code = node_data.get("codigo_python", "")

                if code.strip():
                    result = execute_node_code(code, input_df, log_output)
                    valor = float(result) if result is not None else 0.0
                else:
                    # Default aggregation on 'calculo_formula' column if present
                    if input_df is not None and not input_df.empty and "calculo_formula" in input_df.columns:
                        col = pd.to_numeric(input_df["calculo_formula"], errors="coerce").dropna()
                        if aggregation == "sum":
                            valor = float(col.sum())
                        elif aggregation == "count":
                            valor = float(col.count())
                        else:
                            valor = float(col.mean()) if len(col) > 0 else 0.0
                    else:
                        valor = 0.0

                log_output.append(f"[INFO] Nivel 2 (id={nivel2_id}) valor: {valor}")
                if nivel2_id:
                    nivel2_outputs[int(nivel2_id)] = valor
                resultado[f"nivel2_{nivel2_id}"] = valor
                node_results[node_id] = valor

            elif node_type == "nivel1_output":
                nivel1_id = node_data.get("indicador_nivel1_id")
                code = node_data.get("codigo_python", "")

                if code.strip():
                    # Provide nivel2_outputs dict as context
                    local_vars = {
                        "df": input_df,
                        "nivel2_outputs": nivel2_outputs,
                        "result": None,
                    }
                    sandbox = {**SANDBOX_GLOBALS}
                    buf = io.StringIO()
                    try:
                        with redirect_stdout(buf):
                            exec(
                                compile(code, "<pipeline_nivel1>", "exec"),
                                sandbox,
                                local_vars,
                            )
                        output = buf.getvalue()
                        if output:
                            log_output.append(f"[stdout] {output.rstrip()}")
                        valor_n1 = float(local_vars.get("result") or 0.0)
                    except Exception as e:
                        err = traceback.format_exc()
                        log_output.append(f"[ERROR] {err}")
                        raise RuntimeError(f"Error en nivel1_output: {e}") from e
                else:
                    # Default: mean of all nivel2 outputs
                    if nivel2_outputs:
                        valor_n1 = sum(nivel2_outputs.values()) / len(nivel2_outputs)
                    else:
                        valor_n1 = 0.0

                log_output.append(f"[INFO] Nivel 1 (id={nivel1_id}) valor final: {valor_n1}")
                resultado[f"nivel1_{nivel1_id}"] = valor_n1
                resultado["valor_final"] = valor_n1
                node_results[node_id] = valor_n1

            else:
                log_output.append(f"[WARN] Tipo de nodo desconocido: {node_type}")
                node_results[node_id] = input_df

        except Exception as exc:
            log_output.append(f"[FATAL] Error en nodo {node_name}: {exc}")
            resultado["error"] = str(exc)
            return resultado, "\n".join(log_output)

    log_output.append("\n[INFO] Pipeline completado exitosamente.")
    resultado["nivel2_outputs"] = nivel2_outputs

    return resultado, "\n".join(log_output)
