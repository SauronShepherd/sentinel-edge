from enum import StrEnum

class PluginState(StrEnum):
    DISCOVERED="discovered"; VERIFIED="verified"; SELF_TESTED="self-tested"; ACTIVE="active"; DEGRADED="degraded"; ROLLED_BACK="rolled-back"

class Lifecycle:
    _allowed = {PluginState.DISCOVERED:{PluginState.VERIFIED,PluginState.ROLLED_BACK}, PluginState.VERIFIED:{PluginState.SELF_TESTED,PluginState.ROLLED_BACK}, PluginState.SELF_TESTED:{PluginState.ACTIVE,PluginState.ROLLED_BACK}, PluginState.ACTIVE:{PluginState.DEGRADED,PluginState.ROLLED_BACK}, PluginState.DEGRADED:{PluginState.ACTIVE,PluginState.ROLLED_BACK}, PluginState.ROLLED_BACK:set()}
    def __init__(self) -> None: self.state = PluginState.DISCOVERED
    def transition(self, target: PluginState) -> None:
        if target not in self._allowed[self.state]: raise ValueError(f"illegal transition: {self.state} -> {target}")
        self.state = target
    def verify(self, digest: str, signature: str | None = None) -> None:
        if not digest.startswith("sha256:") or len(digest) != 71: raise ValueError("invalid_digest")
        if not signature: raise ValueError("missing_signature")
        self.transition(PluginState.VERIFIED)
    def compatibility(self, supported: set[str], required: str) -> None:
        if required not in supported: raise ValueError("incompatible_api")
    def self_test(self, passed: bool) -> None:
        if not passed: raise ValueError("self_test_failed")
        self.transition(PluginState.SELF_TESTED)
