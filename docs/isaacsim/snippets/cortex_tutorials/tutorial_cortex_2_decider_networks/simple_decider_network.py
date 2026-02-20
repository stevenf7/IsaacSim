class Dispatch(DfDecider):
    def __init__(self):
        super().__init__()
        self.add_child("print_left", PrintAction("<left>"))
        self.add_child("print_right", PrintAction("<right>"))
        self.add_child("print", PrintAction())

    def decide(self):
        if self.context.is_middle:
            return DfDecision("print", "<middle>")  # Send parameters down to generic print.

        if self.context.is_left:
            return DfDecision("print_left")
        else:
            return DfDecision("print_right")
