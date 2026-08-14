from pathlib import Path


def main() -> None:
    import numpy as np
    import onnx
    from onnx import TensorProto, helper

    weight = helper.make_tensor(
        "weight",
        TensorProto.FLOAT,
        [3, 1],
        np.zeros((3, 1), dtype=np.float32).flatten().tolist(),
    )
    graph = helper.make_graph(
        [
            helper.make_node("MatMul", ["features", "weight"], ["linear"]),
            helper.make_node("Sigmoid", ["linear"], ["score"]),
        ],
        "sentinel_seismic_fixture",
        [helper.make_tensor_value_info("features", TensorProto.FLOAT, [1, 3])],
        [helper.make_tensor_value_info("score", TensorProto.FLOAT, [1, 1])],
        [weight],
    )
    model = helper.make_model(graph, producer_name="sentinel-edge", opset_imports=[helper.make_opsetid("", 13)])
    onnx.checker.check_model(model)
    target = Path("artifacts/release-models/seismic-onnx-development/model.onnx")
    onnx.save(model, target)
    print(f"wrote {target} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
