import hashlib


class ExpressionUtility:
    @classmethod
    def get_id(self, thing):
        # gets a durable ID so funcs like count() can persist throughout the scan
        id = str(thing)
        p = thing.parent
        while p:
            id = id + str(p)
            if p.parent:
                p = p.parent
            else:
                break
        return hashlib.sha256(id.encode("utf-8")).hexdigest()

    @classmethod
    def _dotted(self, s, o):
        if o is None:
            return s
        cs = str(o.__class__)
        cs = cs[cs.rfind(".") :]
        c = cs[0 : cs.find("'")]
        s = f"{c}{s}"
        try:
            return self._dotted(s, o.parent)
        except Exception:
            return s
