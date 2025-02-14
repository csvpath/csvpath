# from __future__ import unicode_literals
from typing import Sequence, Tuple, Optional, TypeVar
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import KeyBindings, merge_key_bindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.widgets import RadioList, Label
from prompt_toolkit.keys import Keys
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.styles import BaseStyle
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from prompt_toolkit.formatted_text.base import StyleAndTextTuples, to_formatted_text
from .const import Const

T = TypeVar("T")


class CRadioList(RadioList):
    def _get_text_fragments(self) -> StyleAndTextTuples:
        result = super()._get_text_fragments()
        for i, _ in enumerate(result):
            if _[0].find("SetCursorPosition") > -1:
                _ = list(result[i + 1])
                _[1] = " "
                result[i + 1] = tuple(_)
            elif _[1].find("*") > -1:
                _ = list(result[i])
                _[1] = " "
                result[i] = tuple(_)
        return result


class Selecter:
    def ask(
        self,
        title: str = "",
        values: Sequence[Tuple[T, AnyFormattedText]] = None,
        default: Optional[T] = None,
        cancel_value: Optional[T] = None,
        style: Optional[BaseStyle] = None,
    ) -> T:
        #
        # based on https://github.com/prompt-toolkit/python-prompt-toolkit/issues/756
        #
        self.ref = False
        radio_list = CRadioList(values, default)
        radio_list.open_character = " "
        radio_list.close_character = " "
        radio_list.selected_style = " "

        #
        # Remove the enter key binding so that we can augment it
        #
        radio_list.control.key_bindings.remove("enter")
        bindings = KeyBindings()
        #
        # Replace the enter key binding to select the value and also submit it
        #

        @bindings.add("enter")
        def exit_with_value(event):
            #
            # enter exits the select, returning the highlighted value
            #
            radio_list._handle_enter()
            v = radio_list.current_value
            if self.ref is True:
                v = f"${v}"
            event.app.exit(result=v)

        @bindings.add("c-c")
        def backup_exit_with_value(event):
            #
            # ctrl-c exits the user interface with the cancel_value
            #
            event.app.exit(result=cancel_value)

        @bindings.add("$")
        def ref_indicator(event):
            #
            # $ indicates a reference
            #
            if self.ref and self.ref is True:
                print("", end="")
                self.ref = False
            else:
                print("$", end="")
                self.ref = True

        #
        # Create and run the mini inline application
        #
        application = Application(
            layout=Layout(HSplit([Label(title), radio_list])),
            key_bindings=merge_key_bindings([load_key_bindings(), bindings]),
            mouse_support=True,
            style=style,
            full_screen=False,
        )
        return application.run()
