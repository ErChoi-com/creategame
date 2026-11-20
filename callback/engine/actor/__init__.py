"""The actor career's formulas (design/part-04-the-actor.md, design/part-05-the-work.md).

Built only on callback.engine.core — never imports callback.engine.simulation, and modules in
this package don't reach into each other's private state; they pass typed dataclasses/plain values
across the (state, rng) -> result Stage shape defined in core.pipeline.
"""
