# Final Manual Submission Checklist

Technical work in the repository should be complete before this list becomes the only remaining work.

- [ ] On the **exact final Git revision**, run `python scripts/dev.py submission-preflight` in an environment with Docker/QEMU `linux/arm64` support; verify every local and `arm64-*` command is green.
- [ ] Run `python scripts/dev.py release-candidate`; verify `release_admitted: true`, H0 240/240 and all G0 packs are `pass` or a defensible declared limitation.
- [ ] Run `python scripts/dev.py package`; for an admitted candidate it automatically performs an isolated fresh-copy Judge smoke verification before final distribution.
- [ ] Run `python scripts/dev.py ui` and capture candidate screenshots according to `SCREENSHOT_PLAN.md`; do **not** use `docs/design/reference-mockups/` as product evidence.
- [ ] Verify the public repository is reachable without restriction, Apache-2.0 is detected/displayed, and the Judge Guide works from a clean checkout.
- [ ] Verify `README.md`, `DEVPOST_SUBMISSION.md`, screenshots and video use only the final Claim Registry values and preserve `simulated` / Arm64-emulated labels.
- [ ] Record/edit the sub-three-minute video using `VIDEO_SCRIPT.md`, `VIDEO_SHOT_LIST.md` and `VIDEO_OVERLAYS.md`; upload publicly to the permitted video host.
- [ ] Register screenshot/video hashes and candidate IDs in `provenance/submission-media/` and run the package/privacy/secret checks again.
- [ ] Replace repository/video URL placeholders in the Devpost form/materials.
- [ ] Describe only hackathon-period work supported by `HACKATHON_WORKLOG.md` and Git history.
- [ ] Review the live Devpost page before the deadline; confirm Physical AI track selection and English setup instructions.
- [ ] Perform the final human Devpost submission.

Do not fabricate or imply physical Raspberry Pi/sensor evidence. If a candidate-affecting change is made after final preflight/media capture, create a new candidate and repeat the affected evidence/media steps.
