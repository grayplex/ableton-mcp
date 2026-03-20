"""Groove pool handlers: list grooves, get/set groove params."""

from AbletonMCP_Remote_Script.registry import command


class GrooveHandlers:
    """Mixin class for groove pool command handlers."""

    @command("list_grooves")
    def _list_grooves(self, params=None):
        """List all grooves in the groove pool."""
        try:
            grooves = []
            for i, groove in enumerate(self._song.groove_pool.grooves):
                grooves.append({
                    "index": i,
                    "name": groove.name,
                })
            return {"grooves": grooves, "count": len(grooves)}
        except Exception as e:
            self.log_message(f"Error listing grooves: {e}")
            raise

    @command("get_groove_params")
    def _get_groove_params(self, params):
        """Get parameters of a groove by index."""
        groove_index = params.get("groove_index", 0)
        try:
            grooves = self._song.groove_pool.grooves
            if groove_index < 0 or groove_index >= len(grooves):
                raise IndexError(
                    f"Groove index {groove_index} out of range "
                    f"(0-{len(grooves) - 1})"
                )
            groove = grooves[groove_index]
            base_labels = {0: "1/4", 1: "1/8", 2: "1/8T", 3: "1/16", 4: "1/16T", 5: "1/32"}
            return {
                "index": groove_index,
                "name": groove.name,
                "base": groove.base,
                "base_label": base_labels.get(groove.base, f"unknown_{groove.base}"),
                "timing_amount": groove.timing_amount,
                "quantization_amount": groove.quantization_amount,
                "random_amount": groove.random_amount,
                "velocity_amount": groove.velocity_amount,
            }
        except Exception as e:
            self.log_message(f"Error getting groove params: {e}")
            raise

    @command("set_groove_params", write=True)
    def _set_groove_params(self, params):
        """Set parameters of a groove by index.

        Optional params: base (int 0-5), timing_amount (float),
        quantization_amount (float), random_amount (float),
        velocity_amount (float).
        """
        groove_index = params.get("groove_index", 0)
        try:
            grooves = self._song.groove_pool.grooves
            if groove_index < 0 or groove_index >= len(grooves):
                raise IndexError(
                    f"Groove index {groove_index} out of range "
                    f"(0-{len(grooves) - 1})"
                )
            groove = grooves[groove_index]

            base = params.get("base")
            if base is not None:
                if not (0 <= base <= 5):
                    raise ValueError(
                        f"base {base} out of range (0-5). "
                        f"0=1/4, 1=1/8, 2=1/8T, 3=1/16, 4=1/16T, 5=1/32"
                    )
                groove.base = base

            for float_param in ["timing_amount", "quantization_amount",
                                "random_amount", "velocity_amount"]:
                val = params.get(float_param)
                if val is not None:
                    setattr(groove, float_param, val)

            base_labels = {0: "1/4", 1: "1/8", 2: "1/8T", 3: "1/16", 4: "1/16T", 5: "1/32"}
            return {
                "index": groove_index,
                "name": groove.name,
                "base": groove.base,
                "base_label": base_labels.get(groove.base, f"unknown_{groove.base}"),
                "timing_amount": groove.timing_amount,
                "quantization_amount": groove.quantization_amount,
                "random_amount": groove.random_amount,
                "velocity_amount": groove.velocity_amount,
            }
        except Exception as e:
            self.log_message(f"Error setting groove params: {e}")
            raise
