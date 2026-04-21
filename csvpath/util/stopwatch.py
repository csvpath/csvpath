import time


class Stopwatch:
    #
    # slow is the slow threshold as a number of ms
    #
    def __init__(self, slow=150) -> None:
        self.start = time.perf_counter()
        self.last = time.perf_counter()
        self.clicks = 0
        self.slow = slow
        print(f"stopwatch start: {self.start}, {self.last}, {self.clicks}")

    def show(self, mark: str = ""):
        self.click(mark, show=True)

    def click(self, mark: str = "", *, show=False) -> None:
        self.clicks = self.clicks + 1
        t = time.perf_counter()
        c = t - self.last
        if show or c > self.slow:
            s = t - self.start
            space = " " if mark else ""
            print(f"slow click: {mark}{space}{self.clicks}: {c} at time: {s}  ")
        self.last = t
