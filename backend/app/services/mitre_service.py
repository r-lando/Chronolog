"""
MITRE ATT&CK technique statistics and lab-mapping logic.

Same scoping philosophy as app/services/skill_tool_service.py: the
techniques themselves are shared, seeded reference data, but every
derived statistic is computed only from labs owned by the requesting
user.
"""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.lab import Lab
from app.models.mitre import LabTechnique, MitreTechnique
from app.services.activity import is_practiced
from app.services.activity import most_recent_activity_date as _most_recent_activity_date




def list_techniques_with_stats(db: Session, user_id: uuid.UUID) -> list[dict]:
    techniques = db.query(MitreTechnique).order_by(MitreTechnique.technique_id).all()
    results = []
    for technique in techniques:
        user_mappings = [lt for lt in technique.lab_techniques if lt.lab.user_id == user_id and is_practiced(lt.lab)]
        last_practiced = max((_most_recent_activity_date(lt.lab) for lt in user_mappings), default=None)
        results.append(
            {
                "id": technique.id,
                "technique_id": technique.technique_id,
                "sub_technique_id": technique.sub_technique_id,
                "name": technique.name,
                "tactic": technique.tactic,
                "description": technique.description,
                "lab_count": len(user_mappings),
                "last_practiced": last_practiced,
            }
        )
    return results


def get_technique_detail(db: Session, technique_pk: uuid.UUID, user_id: uuid.UUID) -> dict | None:
    technique = db.get(MitreTechnique, technique_pk)
    if technique is None:
        return None

    user_mappings = [lt for lt in technique.lab_techniques if lt.lab.user_id == user_id and is_practiced(lt.lab)]
    last_practiced = max((_most_recent_activity_date(lt.lab) for lt in user_mappings), default=None)
    user_mappings_sorted = sorted(user_mappings, key=lambda lt: _most_recent_activity_date(lt.lab), reverse=True)

    return {
        "id": technique.id,
        "technique_id": technique.technique_id,
        "sub_technique_id": technique.sub_technique_id,
        "name": technique.name,
        "tactic": technique.tactic,
        "description": technique.description,
        "lab_count": len(user_mappings),
        "last_practiced": last_practiced,
        "related_labs": [{"lab": lt.lab, "justification": lt.justification} for lt in user_mappings_sorted],
    }


def get_lab_technique_mapping(db: Session, lab_id: uuid.UUID, technique_pk: uuid.UUID) -> LabTechnique | None:
    return (
        db.query(LabTechnique)
        .filter(LabTechnique.lab_id == lab_id, LabTechnique.technique_id == technique_pk)
        .first()
    )
