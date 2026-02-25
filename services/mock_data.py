from datetime import date
from typing import Optional


def _fallback_period(start, end):
    if not start and not end:
        # période par défaut
        return ("2025-01-01", "2025-01-31")
    return (start or "2025-01-01", end or "2025-01-31")

def mock_chat_response(question: str, scope: dict):
    start, end = _fallback_period(scope.get("start"), scope.get("end"))

    # Simule un cas “ambigu”
    if len(question) < 12:
        return {
            "needs_clarification": True,
            "clarifying_question": "Tu peux préciser la période (7 jours / 30 jours / 12 mois) et le secteur/quartier ?",
            "interpretable_as": [
                "Analyse sur 30 jours, tous secteurs",
                "Analyse sur 12 mois, par quartier",
                "Analyse sur 7 jours, autour d’une zone précise"
            ]
        }

    return {
        "needs_clarification": False,
        "answer_text": "Exemple de réponse data-grounded (mock).",
        "evidence": f"Période: {start} → {end}\nFiltres: {scope or 'aucun'}\nRésultat: (mock) 123 événements",
        "generated_query": "SELECT ... FROM collisions WHERE ... GROUP BY ...;  -- mock",
        "limits_and_next_checks": "Limites: données partielles / effet saisonnier.\nÀ vérifier: comparaison YoY, travaux routiers, qualité géocodage."
    }

def mock_briefing_response(start: Optional[str], end: Optional[str]):
    start, end = _fallback_period(start, end)
    return {
        "period": {"start": start, "end": end},
        "hotspots": [
            "Hotspot #1 : Intersection A — 32 collisions (6 graves), 16h–19h, pluie",
            "Hotspot #2 : Zone B (rayon 300m) — 120 requêtes 311 « déneigement » en 2 semaines",
            "Hotspot #3 : Segment C — collisions cyclistes en hausse",
            "Hotspot #4 : Arrêt STM D — proximité collisions graves",
            "Hotspot #5 : Quartier E — nids-de-poule + signalisation"
        ],
        "trends": [
            "Collisions piétons +18% sur 3 mois vs N-1 (mock).",
            "Pic horaire déplacé 17–19h → 15–17h (mock)."
        ],
        "weak_signals": [
            "Quartier C : requêtes « aqueduc/fuite » faibles mais en hausse continue depuis 6 semaines (mock)."
        ],
        "public_version": (
            "Cette semaine, certains points chauds ressortent (intersections et zones). "
            "Des actions ciblées (déneigement, signalisation) pourraient réduire les incidents. (mock)"
        ),
        "municipal_version": (
            "Brief municipal: prioriser interventions sur Hotspot #1 et #2. "
            "Proposer inspection signalisation + plan déneigement. Vérifier biais de reporting. (mock)"
        )
    }
def mock_dashboard_summary(start: Optional[str], end: Optional[str]):
    start, end = _fallback_period(start, end)
    return {
        "period": {"start": start, "end": end},
        "collisions": 1234,
        "top311": ["nids-de-poule", "déneigement", "éclairage", "signalisation"],
        "meteo_hint": "Quand T<0°C, hausse des requêtes « déneigement » (mock)."
    }

def mock_dashboard_points(start: Optional[str], end: Optional[str]):
    # Quelques points de démonstration sur Montréal
    return [
        {"lat": 45.5088, "lon": -73.5610, "weight": 5, "label": "Point A (mock)"},
        {"lat": 45.4890, "lon": -73.5850, "weight": 3, "label": "Point B (mock)"},
        {"lat": 45.5250, "lon": -73.6000, "weight": 4, "label": "Point C (mock)"}
    ]