class Greeter:
    def __init__(self, name, greeting="Hello"):
        self.name = name
        self.greeting = greeting

    def greet(self) -> str:
        return f"{self.greeting}, {self.name}!"
