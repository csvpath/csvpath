from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import (
    HSplit,
    VSplit,
    Window,
    ConditionalContainer,
)
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.completion import WordCompleter


class Asker:
    def __init__(self, cli, *, name_type, prompt=None) -> None:
        self._cli = cli
        names = None
        self.name_type = name_type
        if name_type == "files":
            names = self._cli.csvpaths.file_manager.named_file_names
            names.sort()
        elif name_type == "paths":
            names = self._cli.csvpaths.paths_manager.named_paths_names
            names.sort()
        elif name_type == "none":
            names = []
        else:
            raise ValueError("Name type must be files or paths")
        self.completer = WordCompleter(names, ignore_case=True)
        self.result = None
        self.prompt = prompt

    def create_prompt_application(self, prompt_text=None):
        if prompt_text is None:
            if self.prompt is None:
                prompt_text = (
                    "Named-file name? "
                    if self.name_type == "files"
                    else "Named-paths name? "
                )
            else:
                prompt_text = self.prompt
        # Create a buffer to store input
        buffer = Buffer(completer=self.completer, complete_while_typing=True)
        # Create key bindings
        kb = KeyBindings()

        @kb.add("enter")
        def _(event):
            self.result = buffer.text
            event.app.exit()

        @kb.add("c-c")
        @kb.add("c-q")
        def _(event):
            event.app.exit()

        # Create the layout
        layout = Layout(
            HSplit(
                [
                    # The actual prompt layout
                    VSplit(
                        [
                            # Prompt text
                            Window(
                                content=FormattedTextControl(prompt_text),
                                width=len(prompt_text),
                                dont_extend_width=True,
                            ),
                            # Input field with completions menu wrapped in a Window
                            Window(content=BufferControl(buffer=buffer)),
                        ]
                    )
                ]
                # , align_right=False
            )
        )

        # Create and return the application
        return Application(
            layout=layout,
            key_bindings=kb,
            mouse_support=True,
            full_screen=False,
            erase_when_done=True,
            # complete_while_typing=True
        )

    def ask(self, prompt=None) -> str:
        try:
            self.prompt = prompt
            app = self.create_prompt_application()
            app.run()
            return self.result
        except Exception as e:
            self._cli.csvpaths.logger.error(e)
            import traceback

            print(traceback.format_exc())
            return None
