from operations import Operation


class SetOperation(Operation):
    def _run(self, environment) -> None:
        for key, value in self.definition.items():
            environment.set(key, value)
