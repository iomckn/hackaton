import pandas as pd
from typing import Optional, Dict, Any, List

from services.loader import load_collisions
from services.loader_311 import load_311
from services.llm_local import ollama_generate


MODEL_NAME = "mistral"  # ou "llama3"


def _to_dt(s: Optional[str]):
    if not s:
        return None
    dt = pd.to_datetime(s, errors="coerce")
    return dt if pd.notna(dt) else None


def _filter_by_date(df: pd.DataFrame, col: str, start: Optional[str], end: Optional[str]) -> pd.DataFrame:
    sdt = _to_dt(start)
    edt = _to_dt(end)
    if sdt is not None and col in df.columns:
        df = df[df[col] >= sdt]
    if edt is not None and col in df.columns:
        df = df[df[col] <= edt]
    return df


def _top_counts(df: pd.DataFrame, col: str, k: int = 5) -> List[Dict[str, Any]]:
    if col not in df.columns:
        return []
    s = df[col].fillna("").astype(str).str.strip()
    s = s[s != ""]
    vc = s.value_counts().head(k)
    return [{"label": idx, "count": int(val)} for idx, val in vc.items()]


def _classify_intent(question: str) -> str:
    """
    Retourne un label parmi:
    - collisions_top_rues
    - collisions_graves_total
    - collisions_total
    - req311_top_acti
    - req311_total
    """
    prompt = f"""
Tu es un classifieur. Réponds UNIQUEMENT par un des labels suivants:
collisions_top_rues
collisions_graves_total
collisions_total
req311_top_acti
req311_total

Question: {question}
Label:
""".strip()
    out = ollama_generate(prompt, model=MODEL_NAME).strip().lower()
    # sécurité: fallback si le modèle répond autre chose
    allowed = {
        "collisions_top_rues",
        "collisions_graves_total",
        "collisions_total",
        "req311_top_acti",
        "req311_total",
    }
    return out if out in allowed else "collisions_top_rues"


def answer_chat(question: str, start: Optional[str] = None, end: Optional[str] = None) -> Dict[str, Any]:
    intent = _classify_intent(question)

    result_rows = []
    meta = {"start": start, "end": end, "intent": intent}

    if intent.startswith("collisions"):
        df = load_collisions("collisions_routieres.csv").copy()
        df = _filter_by_date(df, "DT_ACCDN", start, end)
        meta["dataset"] = "collisions"
        meta["n_rows_filtered"] = int(len(df))

        if intent == "collisions_top_rues":
            result_rows = _top_counts(df, "RUE_ACCDN", 5)
        elif intent == "collisions_graves_total":
            if "GRAVITE" in df.columns:
                grav = df["GRAVITE"].astype(str)
                df = df[grav.str.contains("Grave|Mort|Décès|Deces|Fatal", case=False, na=False)]
            result_rows = [{"count": int(len(df))}]
        else:  # collisions_total
            result_rows = [{"count": int(len(df))}]

    else:
        df = load_311("requetes311.csv").copy()
        df = _filter_by_date(df, "DDS_DATE_CREATION", start, end)
        meta["dataset"] = "req311"
        meta["n_rows_filtered"] = int(len(df))

        if intent == "req311_top_acti":
            result_rows = _top_counts(df, "ACTI_NOM", 5)
        else:  # req311_total
            result_rows = [{"count": int(len(df))}]

    # Rédaction “IA” basée sur résultats réels
    prompt = f"""
Tu es Mobility Copilot. Tu dois répondre en français en te basant UNIQUEMENT sur les résultats ci-dessous.
Ne crée aucun chiffre qui n'est pas présent.
Structure:
1) Réponse courte
2) Preuves (période + chiffres + top)
3) Limites (données manquantes, approximations)

Question: {question}
Meta: {meta}
Résultats: {result_rows}
""".strip()

    answer_text = ollama_generate(prompt, model=MODEL_NAME).strip()

    return {
        "answer_text": answer_text,
        "evidence": {"meta": meta, "rows": result_rows},
        "generated_query": intent,
        "limits_and_next_checks": "Voir section Limites dans la réponse."
    }