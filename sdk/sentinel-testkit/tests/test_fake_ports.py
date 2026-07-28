import pytest
from sentinel_testkit.fake_ports import CommandPort
from sentinel_testkit import Scenario

def test_fault_injection_and_scenario_signature():
    port = CommandPort(capacity=1); port.send({"x": 1})
    with pytest.raises(TimeoutError): port.send({"x": 2})
    port.reorder(); port.corrupt = True; port.receive()
    scenario = Scenario("x", time_map={"start": 0.0}); scenario.sign("k")
    assert scenario.verify("k") and not scenario.verify("bad")
