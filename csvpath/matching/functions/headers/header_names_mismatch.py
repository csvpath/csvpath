# pylint: disable=C0114
from ..function_focus import ValueProducer


class HeaderNamesMismatch(ValueProducer):
    """
    given a delimited list of headers, checks that they all exist and
    optionally are in the same order. seems like a match decision activity
    and you have to dig for the generated data but given how much
    good information we're creating the function's pretty clearly a val
    producer.
    """

    def _produce_value(self, skip=None) -> None:  # pylint: disable=R0912
        # re: R0912: not pretty, but tested, can come back
        varname = self.first_non_term_qualifier(self.name)
        present = self.matcher.get_variable(f"{varname}_present")
        if present and len(present) == len(self.matcher.csvpath.headers):
            self.value = True
        elif present:  # pylint: disable=R1702
            self.value = False
        else:
            header_names = self._value_one(skip=skip)
            names = header_names.split("|")
            present = []
            unmatched = []
            misordered = []
            duplicated = []
            for i, name in enumerate(names):
                name = name.strip()
                found = False
                for j, header in enumerate(self.matcher.csvpath.headers):
                    if name == header:
                        found = True
                        if i == j:
                            present.append(header)
                        else:
                            if header in misordered or header in present:
                                if header not in duplicated:
                                    duplicated.append(header)
                            if header not in misordered:
                                misordered.append(header)
                if found is False:
                    unmatched.append(name)
            if len(present) != len(self.matcher.csvpath.headers):
                for name in self.matcher.csvpath.headers:
                    if name not in names:
                        unmatched.append(name)
            self.matcher.set_variable(f"{varname}_present", value=present)
            self.matcher.set_variable(f"{varname}_unmatched", value=unmatched)
            self.matcher.set_variable(f"{varname}_misordered", value=misordered)
            self.matcher.set_variable(f"{varname}_duplicated", value=duplicated)
            self.value = len(present) != len(self.matcher.csvpath.headers)

    def _decide_match(self, skip=None) -> None:
        self.matches = self.to_value(skip=skip)
