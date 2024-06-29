
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
        import hashlib
        id = hashlib.sha256(id.encode('utf-8')).hexdigest()
        return id



