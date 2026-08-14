from __future__ import annotations

import json, math, stat, statistics
from datetime import datetime, timezone
from pathlib import Path

from sentinel_edge.domain.models import CameraCommissioningReport, CameraFrameSample, CapabilityState
from sentinel_edge.security import canonical_json_bytes, sha256_bytes, sha256_file


def load_camera_frames(path: str | Path) -> tuple[CameraFrameSample, ...]:
    rows=[]
    with Path(path).open('r',encoding='utf-8') as handle:
        for line_no,line in enumerate(handle,1):
            if not line.strip(): continue
            try: rows.append(CameraFrameSample.model_validate(json.loads(line)))
            except Exception as exc: raise ValueError(f'invalid camera frame at line {line_no}: {exc}') from exc
    return tuple(rows)


def _percentile(values:list[float], q:float)->float:
    if not values: return 0.0
    ordered=sorted(values); idx=min(len(ordered)-1,max(0,math.ceil(q*len(ordered))-1)); return ordered[idx]


def commission_camera(path: str | Path, *, source_id:str, requested_fps:float, minimum_frames:int=60,
                      rate_tolerance_fraction:float=.10, maximum_gap_factor:float=3.0,
                      darkness_threshold:float=12.0, blur_threshold:float=20.0,
                      occlusion_threshold:float=.85, maximum_bad_fraction:float=.20,
                      preprocessing_profile:dict|None=None)->CameraCommissioningReport:
    source=Path(path); frames=load_camera_frames(source); reasons=[]
    try:
        resolved=source.resolve(); physical=resolved.as_posix().startswith('/dev/video') and stat.S_ISCHR(source.stat().st_mode)
    except OSError: physical=False
    if len(frames)<minimum_frames: reasons.append('insufficient_frames')
    intervals=[]; gaps=0; nonmono=0; capture_ages=[]; frozen=0
    resolutions={(f.width,f.height) for f in frames}
    for prev,cur in zip(frames,frames[1:]):
        delta=cur.monotonic_ns-prev.monotonic_ns
        if delta<=0: nonmono+=1
        else: intervals.append(delta)
        if cur.sequence!=prev.sequence+1: gaps+=1
        if cur.frame_sha256==prev.frame_sha256: frozen+=1
    for f in frames:
        if f.received_at < f.captured_at:
            reasons.append('received_before_capture')
        capture_ages.append(max(0.0,(f.received_at-f.captured_at).total_seconds()*1000))
    duration=(frames[-1].monotonic_ns-frames[0].monotonic_ns)/1e9 if len(frames)>1 and frames[-1].monotonic_ns>frames[0].monotonic_ns else 0.0
    observed=(len(frames)-1)/duration if duration else 0.0
    rate_error=abs(observed-requested_fps)/requested_fps
    intervals_ms=[v/1e6 for v in intervals]; max_gap=max(intervals_ms,default=0.0)
    median=statistics.median(intervals_ms) if intervals_ms else 0.0
    p99=_percentile([abs(v-median) for v in intervals_ms],.99)
    dark=sum(f.luminance_mean<darkness_threshold for f in frames)
    blurred=sum(f.blur_score<blur_threshold for f in frames)
    occluded=sum(f.occlusion_fraction>occlusion_threshold for f in frames)
    if nonmono: reasons.append('non_monotonic_capture_clock')
    if gaps: reasons.append('sequence_gaps')
    if len(resolutions)!=1: reasons.append('resolution_changed')
    if rate_error>rate_tolerance_fraction: reasons.append('frame_rate_out_of_tolerance')
    if max_gap>(1000/requested_fps)*maximum_gap_factor: reasons.append('capture_gap_exceeds_limit')
    for count,code in [(frozen,'frozen_frames'),(dark,'dark_frames'),(blurred,'blurred_frames'),(occluded,'occluded_frames')]:
        if frames and count/len(frames)>maximum_bad_fraction: reasons.append(code+'_exceed_limit')
    if not physical: reasons.append('physical_camera_not_proven')
    profile=preprocessing_profile or {'pixel_format':'metadata_fixture','resize':'none','privacy_mask':'none'}
    quality_blockers={'insufficient_frames','non_monotonic_capture_clock','sequence_gaps','resolution_changed','frame_rate_out_of_tolerance','capture_gap_exceeds_limit','received_before_capture','frozen_frames_exceed_limit','dark_frames_exceed_limit','blurred_frames_exceed_limit','occluded_frames_exceed_limit'}
    quality_ok=not any(r in quality_blockers for r in reasons)
    state=CapabilityState.FIELD_QUALIFIED if quality_ok and physical else CapabilityState.TESTED if quality_ok else CapabilityState.FAILED
    return CameraCommissioningReport(source_id=source_id,source_path=str(source.resolve()),source_sha256=sha256_file(source),physical_source_proven=physical,state=state,frame_count=len(frames),duration_seconds=duration,requested_fps=requested_fps,observed_fps=observed,rate_error_fraction=rate_error,maximum_gap_ms=max_gap,p99_interval_jitter_ms=p99,p95_capture_age_ms=_percentile(capture_ages,.95),non_monotonic_frames=nonmono,sequence_gaps=gaps,frozen_frames=frozen,dark_frames=dark,blurred_frames=blurred,occluded_frames=occluded,resolution_consistent=len(resolutions)==1,preprocessing_profile_sha256=sha256_bytes(canonical_json_bytes(profile)),reason_codes=tuple(sorted(set(reasons))) if reasons else ('physical_camera_commissioned',))
