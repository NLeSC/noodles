import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')

from gi.repository import (Gtk, GtkSource)

class Editor(Gtk.ScrolledWindow):
    def __init__(self):
        super(Editor, self).__init__()

        self._buffer = GtkSource.Buffer.new()
        text = open("./udon.py", "r").read()
        self._buffer.set_text(text)

        slm = GtkSource.LanguageManager.new()
        language = slm.get_language("python")
        self._buffer.set_language(language)

        ssm = GtkSource.StyleSchemeManager.get_default()
        scheme = ssm.get_scheme('cobalt')
        self._buffer.set_style_scheme(scheme)

        self._source_editor = GtkSource.View.new_with_buffer(self._buffer)
        self._source_editor.set_show_line_numbers(True)
        self._source_editor.set_monospace(True)
        self._source_editor.set_right_margin_position(80)
        self._source_editor.set_show_right_margin(True)

        self.add(self._source_editor)
        self._source_editor.get_style_context().add_class("Editor")


