class ValidationMode:
    COLLECT = "collect"
    NO_COLLECT = "no-collect"
    PRINT = "print"
    NO_PRINT = "no-print"
    RAISE = "raise"
    NO_RAISE = "no-raise"
    MATCH = "match"
    NO_MATCH = "no-match"
    STOP = "stop"
    NO_STOP = "no-stop"
    FAIL = "fail"
    NO_FAIL = "no-fail"
    LOG = "log"
    NO_LOG = "no-log"
    MODE = "validation-mode"

    #
    # validation error handling overrides the error policy in config. this
    # is because the validation handling is:
    #   - different. it is built-in. it deals with programmatic decisions
    #     about how functions work and is the basis for structural (schema)
    #     validation.
    #   - set on a per csvpath basis in comments
    #
    # by default, validation errors do not impact matching. they are print
    # and raise only. however, you can set them to raise or match/not-match
    # and/or suppress printing.
    #
    def __init__(self, controller):
        self.controller = controller
        self._validation_mode = None
        self._log_validation_errors = True
        self._print_validation_errors = True
        self._raise_validation_errors = None
        self._match_validation_errors = None
        self._stop_on_validation_errors = None
        self._fail_on_validation_errors = None
        self._collect_validation_errors = None

    def update(self) -> None:
        self._validation_mode = None
        self.value

    @property
    def value(self) -> str:
        if self._validation_mode is None:
            vm = self.controller.get(ValidationMode.MODE)
            if vm is None:
                self.value = "print, collect"
            self._validation_mode = vm
            self._update_settings(vm)
        return self._validation_mode

    @value.setter
    def value(self, veh: str) -> None:
        if veh is None:
            veh = self.controller.get(ValidationMode.MODE)
            if veh is None:
                veh = "log, print"
                self.controller.set(ValidationMode.MODE, veh)
        self._validation_mode = veh
        self._update_settings(veh)

    #
    # these settings determine how we report function args validation
    # errors. e.g. if print(True) the validation check fails because
    # print() expects a string. the more recent trend is to get all
    # the errors and print statements in the same place controlled by
    # the same properties. for now this stays because there is a minor
    # benefit to being able to suppress runtime arg validation and only
    # use match component rules and exceptions to generate validation
    # info. but long term this capability may go away.
    #
    def _update_settings(self, veh: str) -> None:
        self.set_print_validation_errors(veh)
        self.set_raise_validation_errors(veh)
        self.set_match_validation_errors(veh)
        self.set_stop_validation_errors(veh)
        self.set_fail_validation_errors(veh)
        self.set_log_validation_errors(veh)
        self.set_collect_validation_errors(veh)

    # ===========================
    # the setters are not really setters because the arg
    # mismatches the getter return
    #
    def set_match_validation_errors(self, veh: str) -> None:
        # match, no-match, and None do:
        #   match: return True on error
        #   no-match: return False on error
        #   None: default behavior: default_match() or result of matches()
        if veh and veh.find(ValidationMode.NO_MATCH) > -1:
            self._match_validation_errors = False
        elif veh and veh.find(ValidationMode.MATCH) > -1:
            self._match_validation_errors = True
        else:
            self._match_validation_errors = None

    def set_raise_validation_errors(self, veh: str) -> None:
        if veh and veh.find(ValidationMode.NO_RAISE) > -1:
            self._raise_validation_errors = False
        elif veh and veh.find(ValidationMode.RAISE) > -1:
            self._raise_validation_errors = True
        else:
            self._raise_validation_errors = None

    def set_print_validation_errors(self, veh: str) -> None:
        # print prints to the Printer(s), not direct to std.out. atm, no
        # customization of messages is possible, so there is likely
        # to be stylistic mismatch with other output.
        if veh and veh.find(ValidationMode.NO_PRINT) > -1:
            self._print_validation_errors = False
        elif veh and veh.find(ValidationMode.PRINT) > -1:
            self._print_validation_errors = True
        else:
            self._print_validation_errors = None

    def set_stop_validation_errors(self, veh: str) -> None:
        if veh and veh.find(ValidationMode.NO_STOP) > -1:
            self._stop_on_validation_errors = False
        elif veh and veh.find(ValidationMode.STOP) > -1:
            self._stop_on_validation_errors = True
        else:
            self._stop_on_validation_errors = None

    def set_fail_validation_errors(self, veh: str) -> None:
        if veh and veh.find(ValidationMode.NO_FAIL) > -1:
            self._fail_on_validation_errors = False
        elif veh and veh.find(ValidationMode.FAIL) > -1:
            self._fail_on_validation_errors = True
        else:
            self._fail_on_validation_errors = None

    def set_collect_validation_errors(self, veh: str) -> None:
        if veh and veh.find(ValidationMode.NO_COLLECT) > -1:
            self._collect_validation_errors = False
        elif veh and veh.find(ValidationMode.COLLECT) > -1:
            self._collect_validation_errors = True
        else:
            self._collect_validation_errors = None

    def set_log_validation_errors(self, veh: str) -> None:
        if veh and veh.find(ValidationMode.NO_LOG) > -1:
            self._log_on_validation_errors = False
        elif veh and veh.find(ValidationMode.LOG) > -1:
            self._log_on_validation_errors = True
        else:
            #
            # default is True, not None. we don't expect to
            # turn off logging except in rare cases.
            #
            self._log_on_validation_errors = True

    @property
    def stop_on_validation_errors(self) -> bool:
        return self._stop_on_validation_errors

    @property
    def fail_on_validation_errors(self) -> bool:
        return self._fail_on_validation_errors

    @property
    def collect_validation_errors(self) -> bool:
        return self._collect_validation_errors

    @property
    def print_validation_errors(self) -> bool:
        return self._print_validation_errors

    @property
    def log_validation_errors(self) -> bool:
        return self._log_validation_errors

    @property
    def raise_validation_errors(self) -> bool:
        return self._raise_validation_errors

    @property
    def match_validation_errors(self) -> bool:
        return self._match_validation_errors
