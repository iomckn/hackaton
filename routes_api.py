from flask import Blueprint, request, jsonify
import pandas as pd
from services.chat_engine import answer_chat
from services.loader_311 import load_311
from services.loader import load_collisions
from services.mock_data import (
    mock_chat_response,
    mock_briefing_response,
    mock_dashboard_summary,
    mock_dashboard_points
)

api_bp = Blueprint("api", __name__, url_prefix="/api")

def _get_date_param(name: str):
    # Lecture simple des query params (start/end)
    val = request.args.get(name)
    return val  # string "YYYY-MM-DD" ou None

@api_bp.post("/chat")
def api_chat():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    scope = payload.get("scope") or {}
    start = scope.get("start")
    end = scope.get("end")

    if not question:
        return jsonify({"error": "question is required"}), 400

    data = answer_chat(question, start, end)
    return jsonify(data), 200

@api_bp.get("/briefing")
def api_briefing():
    start = request.args.get("start")
    end = request.args.get("end")

    if not start or not end:
        return jsonify({"error": "start and end required"}), 400

    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)

    df = load_collisions("collisions_routieres.csv").copy()

    # --- Période actuelle ---
    df_current = df[(df["DT_ACCDN"] >= start_dt) & (df["DT_ACCDN"] <= end_dt)]
    total_current = len(df_current)

    # --- Période précédente (même durée juste avant) ---
    delta_days = (end_dt - start_dt).days
    prev_start = start_dt - pd.Timedelta(days=delta_days)
    prev_end = start_dt

    df_previous = df[(df["DT_ACCDN"] >= prev_start) & (df["DT_ACCDN"] < prev_end)]
    total_previous = len(df_previous)

    # --- Hotspots ---
    top_rues = (
        df_current["RUE_ACCDN"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    top_rues = top_rues[top_rues != ""].value_counts().head(5)

    hotspots = [
        f"{rue} — {count} collisions"
        for rue, count in top_rues.items()
    ]

    # --- Tendance ---
    if total_previous > 0:
        variation = ((total_current - total_previous) / total_previous) * 100
        tendance_text = f"{variation:.1f}% vs période précédente"
    else:
        tendance_text = "Pas de données période précédente"

    # --- Signal faible ---
    prev_top = (
        df_previous["RUE_ACCDN"]
        .fillna("")
        .astype(str)
        .str.strip()
        .value_counts()
        .head(5)
        .index
        .tolist()
    )

    weak_signal = None
    for rue in top_rues.index:
        if rue not in prev_top:
            weak_signal = f"Nouveau hotspot émergent : {rue}"
            break

    if not weak_signal:
        weak_signal = "Pas de nouveau hotspot détecté"

    # --- Version grand public ---
    public_text = (
        f"Sur la période sélectionnée, {total_current} collisions ont été recensées. "
        f"Les principales zones concernées sont : {', '.join(top_rues.index.tolist())}. "
        f"La tendance est de {tendance_text}."
    )

    # --- Version municipalité ---
    municipal_text = (
        f"Total collisions : {total_current}. "
        f"Variation : {tendance_text}. "
        f"Prioriser interventions sur : {', '.join(top_rues.index.tolist())}. "
        f"Recommandation : inspection signalisation et contrôle vitesse."
    )

    return jsonify({
        "period": {"start": start, "end": end},
        "hotspots": hotspots,
        "trend": tendance_text,
        "weak_signal": weak_signal,
        "public_version": public_text,
        "municipal_version": municipal_text
    })

@api_bp.get("/dashboard/summary")
def api_dashboard_summary():
    start = request.args.get("start")
    end = request.args.get("end")

    df = load_collisions("collisions_routieres.csv").copy()

    # Filtrage dates
    if start:
        start_dt = pd.to_datetime(start, errors="coerce")
        if pd.notna(start_dt):
            df = df[df["DT_ACCDN"] >= start_dt]
    if end:
        end_dt = pd.to_datetime(end, errors="coerce")
        if pd.notna(end_dt):
            df = df[df["DT_ACCDN"] <= end_dt]

    total = int(len(df))

    # Collisions "graves" (simple heuristique sur la colonne GRAVITE)
    # Adapte les mots si besoin selon tes valeurs réelles.
    if "GRAVITE" in df.columns:
        grav = df["GRAVITE"].astype(str)
        df_graves = df[grav.str.contains("Grave|Mort|Décès|Deces|Fatal", case=False, na=False)]
        graves = int(len(df_graves))
    else:
        graves = 0

    df311 = load_311("requetes311.csv").copy()

    # filtrage période (sur DDS_DATE_CREATION)
    if start:
        start_dt = pd.to_datetime(start, errors="coerce")
        if pd.notna(start_dt):
            df311 = df311[df311["DDS_DATE_CREATION"] >= start_dt]
    if end:
        end_dt = pd.to_datetime(end, errors="coerce")
        if pd.notna(end_dt):
            df311 = df311[df311["DDS_DATE_CREATION"] <= end_dt]

    req311_total = int(len(df311))

    # Top catégories : ACTI_NOM (souvent le plus parlant)
    if "ACTI_NOM" in df311.columns:
        s = df311["ACTI_NOM"].fillna("").astype(str).str.strip()
        s = s[s != ""]
        top_311 = s.value_counts().head(5)
        top_311_list = [{"label": k, "count": int(v)} for k, v in top_311.items()]
    else:
        top_311_list = []

    # Top 5 rues (hotspots simples)
    if "RUE_ACCDN" in df.columns:
        top_rues_series = (
            df["RUE_ACCDN"]
            .fillna("")
            .astype(str)
            .str.strip()
        )
        top_rues_series = top_rues_series[top_rues_series != ""]
        top_rues = top_rues_series.value_counts().head(5)
        top_rues_list = [
            {"rue": rue, "count": int(cnt)}
            for rue, cnt in top_rues.items()
        ]
    else:
        top_rues_list = []

    return jsonify({
        "period": {"start": start, "end": end},
        "collisions_total": total,
        "collisions_graves": graves,
        "top_rues": top_rues_list,
        "req311_total": req311_total,
        "top_311": top_311_list
    })


@api_bp.get("/dashboard/map")
def api_dashboard_map():
    start = request.args.get("start")
    end = request.args.get("end")

    # Charger collisions
    df = load_collisions("collisions_routieres.csv")

    # Filtrer par date si fourni
    if start:
        start_dt = pd.to_datetime(start, errors="coerce")
        if pd.notna(start_dt):
            df = df[df["DT_ACCDN"] >= start_dt]

    if end:
        end_dt = pd.to_datetime(end, errors="coerce")
        if pd.notna(end_dt):
            df = df[df["DT_ACCDN"] <= end_dt]

    # Échantillonner pour éviter d'envoyer 100k points
    sample = df.sample(n=min(200, len(df)), random_state=42)

    points = []
    for _, row in sample.iterrows():
        rue = str(row.get("RUE_ACCDN", "") or "")
        grav = str(row.get("GRAVITE", "") or "")
        label = f"{rue} — {grav}".strip(" —")

        points.append({
            "lat": float(row["LOC_LAT"]),
            "lon": float(row["LOC_LONG"]),
            "weight": 1,
            "label": label
        })

    return jsonify({"points": points})

@api_bp.get("/dashboard/map311")
def api_dashboard_map_311():
    start = request.args.get("start")
    end = request.args.get("end")

    from services.loader_311 import load_311
    df = load_311("requetes311.csv").copy()

    # Filtrage dates
    if "DDS_DATE_CREATION" in df.columns:
        if start:
            start_dt = pd.to_datetime(start, errors="coerce")
            if pd.notna(start_dt):
                df = df[df["DDS_DATE_CREATION"] >= start_dt]
        if end:
            end_dt = pd.to_datetime(end, errors="coerce")
            if pd.notna(end_dt):
                df = df[df["DDS_DATE_CREATION"] <= end_dt]

    # Garder points valides
    df = df.dropna(subset=["LOC_LAT", "LOC_LONG"])

    # Limiter pour performance
    sample = df.sample(n=min(200, len(df)), random_state=42)

    points = []
    for _, row in sample.iterrows():
        label = str(row.get("ACTI_NOM", "") or "")
        points.append({
            "lat": float(row["LOC_LAT"]),
            "lon": float(row["LOC_LONG"]),
            "label": label
        })

    return jsonify({"points": points})