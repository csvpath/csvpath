# pylint: disable=C0114
from csvpath.matching.productions import Term
from ..function_focus import ValueProducer
from ..args import Args


class HeaderNamesMismatch(ValueProducer):
    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Given a | delimited list of headers, checks that all exist and
                are in the same order.

                While the function is intended for matching, substantial data is
                created in variables. The following variables containing header names
                may be useful:

                - N_present

                - N_unmatched

                - N_misordered

                - N_duplicated

                (Where 'N' is a name qualifier, if given, or 'header_names_mismatch')

                If you have: header_names_mismatch.m("Alpha|Beta|Cappa|Delta")
                and your headers are: Alpha,Delta,Beta
                you will have @m_present == ["Alpha"], @m_unmatched == ["Cappa"], @m_misordered = ["Delta"]
                and header_names_mismatch() will return False; i.e. not match.
        """
            ),
        ]
        self.name_qualifier = True
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(name="pipe delimited headers", types=[Term], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:  # pylint: disable=R0912
        # re: R0912: not pretty, but tested, can come back
        varname = self.first_non_term_qualifier(self.name)
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
        #
        # add: and misordered == 0?
        #   don't need ^^^^ because present doesn't include any misordered so if present
        #   doesn't equal the current headers we have the right answer
        #
        self.value = len(present) != len(
            self.matcher.csvpath.headers
        )  # or len(misordered) > 0

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip)
