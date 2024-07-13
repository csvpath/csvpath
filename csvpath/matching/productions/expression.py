from csvpath.matching.productions.matchable import Matchable


class Expression(Matchable):
    def matches(self, *, skip=[]) -> bool:
        if not skip:
            skip = []
        if self in skip:
            return True
        if not self.value:
            ret = True
            for i, child in enumerate(self.children):
                if not child.matches(skip=skip):
                    ret = False
            self.value = ret
        return self.value

    def reset(self) -> None:
        self.value = None
        super().reset()
