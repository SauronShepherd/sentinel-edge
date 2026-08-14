from __future__ import annotations

import json, math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sentinel_edge.domain.models import CapabilityState, ClaimClass, ModelQualityManifest, ModelQualityReport
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


def load_model_quality_manifest(path:str|Path)->ModelQualityManifest:
    return ModelQualityManifest.model_validate_json(Path(path).read_text(encoding='utf-8'))


def _safe(root:Path, relative:str)->Path:
    p=(root/relative).resolve(); p.relative_to(root.resolve()); return p


def _score(model:dict[str,Any], features:dict[str,float])->float:
    z=float(model.get('bias',0.0))+sum(float(w)*float(features.get(name,0.0)) for name,w in model['weights'].items())
    return 1.0/(1.0+math.exp(-z))


def qualify_model_quality(manifest:ModelQualityManifest, *, root:str|Path, now:datetime|None=None)->ModelQualityReport:
    now=now or datetime.now(timezone.utc); rootp=Path(root).resolve(); reasons=[]
    manifest_sha=sha256_bytes(canonical_json_bytes(manifest.model_dump(mode='json')))
    try:
        model_path=_safe(rootp,manifest.model_path); data_path=_safe(rootp,manifest.dataset_path); ka_path=_safe(rootp,manifest.known_answer_path)
    except ValueError:
        return ModelQualityReport(model_id=manifest.model_id,manifest_sha256=manifest_sha,model_integrity_match=False,dataset_integrity_match=False,known_answer_integrity_match=False,graph_quarantine_passed=False,known_answer_passed=False,split_leakage_detected=True,final_claim_set_frozen=manifest.final_claim_set_frozen,sample_count=0,claim_sample_count=0,recall=0,false_alarm_rate=1,abstention_rate=1,quality_guardrails_passed=False,target_qualified=False,state=CapabilityState.FAILED,reason_codes=('path_outside_root',))
    model_ok=model_path.is_file() and sha256_file(model_path)==manifest.model_sha256
    data_ok=data_path.is_file() and sha256_file(data_path)==manifest.dataset_sha256
    ka_ok=ka_path.is_file() and sha256_file(ka_path)==manifest.known_answer_sha256
    if not model_ok: reasons.append('model_integrity_failed')
    if not data_ok: reasons.append('dataset_integrity_failed')
    if not ka_ok: reasons.append('known_answer_integrity_failed')
    model={}; rows=[]; cases=[]
    if model_ok:
        try: model=json.loads(model_path.read_text())
        except Exception: reasons.append('model_not_json')
    graph_ok=bool(model) and model.get('type')=='linear_sigmoid' and isinstance(model.get('weights'),dict) and not model.get('external_data') and set(model)<= {'schema','type','weights','bias','threshold','abstain_margin','external_data'}
    if not graph_ok: reasons.append('graph_quarantine_failed')
    if data_ok:
        for i,line in enumerate(data_path.read_text().splitlines(),1):
            if line.strip():
                try: rows.append(json.loads(line))
                except Exception: reasons.append(f'dataset_row_invalid:{i}')
    if ka_ok:
        try: cases=json.loads(ka_path.read_text())['cases']
        except Exception: reasons.append('known_answer_file_invalid')
    known_answer_passed=graph_ok and bool(cases)
    if known_answer_passed:
        for case in cases:
            observed=_score(model,case['features'])
            decision='abstain' if abs(observed-model['threshold'])<=model.get('abstain_margin',0.0) else 'positive' if observed>=model['threshold'] else 'negative'
            if abs(observed-float(case['expected_score']))>manifest.score_tolerance or decision!=case['expected_decision']:
                known_answer_passed=False; reasons.append('known_answer_mismatch'); break
    elif not cases: reasons.append('known_answer_cases_missing')
    split_groups={}
    for row in rows: split_groups.setdefault(row['split'],set()).add(row[manifest.split_group_field])
    leakage=any(split_groups.get(a,set()) & split_groups.get(b,set()) for a,b in [('development','calibration'),('development','claim'),('calibration','claim')])
    if leakage: reasons.append('split_group_leakage')
    claim=[r for r in rows if r.get('split')=='claim']; tp=fn=fp=tn=abstain=0
    if graph_ok:
        for row in claim:
            score=_score(model,row['features']); label=int(row['label'])
            if abs(score-model['threshold'])<=model.get('abstain_margin',0.0): abstain+=1; continue
            pred=1 if score>=model['threshold'] else 0
            tp+=pred==1 and label==1; fn+=pred==0 and label==1; fp+=pred==1 and label==0; tn+=pred==0 and label==0
    recall=tp/(tp+fn) if tp+fn else 0.0; far=fp/(fp+tn) if fp+tn else 0.0; abst=abstain/len(claim) if claim else 1.0
    if recall<manifest.minimum_recall: reasons.append('recall_below_guardrail')
    if far>manifest.maximum_false_alarm_rate: reasons.append('false_alarm_rate_above_guardrail')
    if abst>manifest.maximum_abstention_rate: reasons.append('abstention_rate_above_guardrail')
    if not manifest.final_claim_set_frozen: reasons.append('final_claim_set_not_frozen')
    license_ok=manifest.license_id.strip().upper() not in {'', 'NOASSERTION', 'UNKNOWN', 'UNLICENSED'}
    if not license_ok: reasons.append('model_license_unresolved')
    if now>=manifest.expires_at: reasons.append('model_quality_expired')
    passed=license_ok and model_ok and data_ok and ka_ok and graph_ok and known_answer_passed and not leakage and bool(claim) and manifest.final_claim_set_frozen and recall>=manifest.minimum_recall and far<=manifest.maximum_false_alarm_rate and abst<=manifest.maximum_abstention_rate and now<manifest.expires_at
    target=passed and manifest.source_class is ClaimClass.MEASURED
    state=CapabilityState.TARGET_QUALIFIED if target else CapabilityState.TESTED if passed else CapabilityState.EXPIRED if now>=manifest.expires_at else CapabilityState.FAILED
    return ModelQualityReport(model_id=manifest.model_id,manifest_sha256=manifest_sha,model_integrity_match=model_ok,dataset_integrity_match=data_ok,known_answer_integrity_match=ka_ok,graph_quarantine_passed=graph_ok,known_answer_passed=known_answer_passed,split_leakage_detected=leakage,final_claim_set_frozen=manifest.final_claim_set_frozen,sample_count=len(rows),claim_sample_count=len(claim),recall=recall,false_alarm_rate=far,abstention_rate=abst,quality_guardrails_passed=passed,target_qualified=target,state=state,reason_codes=tuple(sorted(set(reasons))) if reasons else ('model_quality_target_qualified' if target else 'model_quality_development_passed',))
