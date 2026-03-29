import gc
import sys
import types


class ReferrerPrinter:
    """
    Prints the referrer graph of an object recursively using gc.get_referrers().
    Useful for diagnosing why __del__ isn't being called — i.e. what's keeping
    your object alive.

    Usage:
        rp = ReferrerPrinter(max_depth=5)
        rp.print_referrers(your_object)
    """

    # Types that are noise — skip them to keep output readable
    _SKIP_TYPES = (
        types.FrameType,
        types.ModuleType,
        type,           # class objects
    )

    def __init__(self, max_depth: int = 5, skip_types: tuple = ()):
        self.max_depth = max_depth
        self._extra_skip = skip_types
        self._seen: set[int] = set()

    def print_referrers(self, obj, label: str = "<target>") -> None:
        """Print the full referrer tree for obj to stdout."""
        self._seen = {id(self), id(self.__dict__), id(self._seen)}
        print(f"Referrer graph for {label} (id={id(obj)}, type={type(obj).__name__})")
        self._walk(obj, depth=0)

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------

    def _walk(self, obj, depth: int) -> None:
        if depth >= self.max_depth:
            print(self._indent(depth) + "... (max depth reached)")
            return

        referrers = gc.get_referrers(obj)

        # Filter out the referrers list itself and anything already visited
        referrers = [
            r for r in referrers
            if id(r) not in self._seen
            and not self._is_skipped(r)
        ]

        if not referrers:
            print(self._indent(depth) + "(no further referrers)")
            return

        for ref in referrers:
            self._seen.add(id(ref))
            desc = self._describe(ref, obj)
            print(self._indent(depth) + desc)
            self._walk(ref, depth + 1)

    def _is_skipped(self, ref) -> bool:
        return isinstance(ref, (self._SKIP_TYPES + self._extra_skip))

    @staticmethod
    def _indent(depth: int) -> str:
        return "  " * depth + ("└─ " if depth > 0 else "")

    @staticmethod
    def _describe(ref, child) -> str:
        """Return a human-readable description of ref and how it holds child."""
        ref_type = type(ref).__name__
        ref_id = id(ref)

        if isinstance(ref, dict):
            # Find the key(s) under which child is stored
            keys = [k for k, v in ref.items() if v is child]
            key_str = ", ".join(repr(k) for k in keys) if keys else "?"
            # Try to name the owning object via gc
            owners = [
                o for o in gc.get_referrers(ref)
                if hasattr(o, "__dict__") and o.__dict__ is ref
            ]
            if owners:
                owner = owners[0]
                return (
                    f"dict (id={ref_id}) — __dict__ of "
                    f"{type(owner).__name__} id={id(owner)}  "
                    f"[key: {key_str}]"
                )
            return f"dict (id={ref_id})  [key: {key_str}]"

        if isinstance(ref, list):
            indices = [i for i, v in enumerate(ref) if v is child]
            idx_str = ", ".join(str(i) for i in indices) if indices else "?"
            return f"list (id={ref_id})  [index: {idx_str}]"

        if isinstance(ref, tuple):
            indices = [i for i, v in enumerate(ref) if v is child]
            idx_str = ", ".join(str(i) for i in indices) if indices else "?"
            return f"tuple (id={ref_id})  [index: {idx_str}]"

        if isinstance(ref, set):
            return f"set (id={ref_id})"

        # Generic object
        try:
            short_repr = repr(ref)[:80]
        except Exception:
            short_repr = "<repr failed>"
        return f"{ref_type} (id={ref_id})  repr={short_repr}"
