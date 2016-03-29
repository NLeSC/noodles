import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')

from gi.repository import (Gtk, Gdk, GtkSource)
# import pandas

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


def idx_letters(i):
    s = ''
    while i != 0:
        i -= 1
        s = chr((i % 26) + ord('A')) + s
        i //= 26
    return s


class WorkSheet(Gtk.VBox):
    def __init__(self, shape=(1, 1)):
        super(WorkSheet, self).__init__()
        self._scrolled_window = Gtk.ScrolledWindow()
        self._scrolled_window.set_hexpand(True)
        self._scrolled_window.set_vexpand(True)

        self._grid = Gtk.Grid()
        self._scrolled_window.add(self._grid)

        self._entry = Gtk.Entry()
        self.pack_start(self._scrolled_window, expand=True, fill=True, padding=0)
        self.pack_end(self._entry, expand=False, fill=True, padding=2)
        self.show_all()

        self.shape = shape
        self.create_cells()

    def create_cells(self):
        for i in range(1, self.shape[0]):
            label = Gtk.Label.new(idx_letters(i))
            label.props.width_request = 100
            label.props.height_request = 12
            self._grid.attach(label, i, 0, 1, 1)

        for j in range(1, self.shape[1]):
            label = Gtk.Label.new(str(j))
            label.set_alignment(1, 0.5)
            label.props.width_request = 100
            label.props.halign = Gtk.Align.END
            label.props.hexpand = True
            label.props.height_request = 25
            self._grid.attach(label, 0, j, 1, 1)

        self.show_all()

class Window(Gtk.Window):
    def __init__(self):
        super(Window, self).__init__(title='Udon')
        self.set_default_size(1024, 720);

        # header bar
        self._header_bar = Gtk.HeaderBar()
        self._header_bar.set_show_close_button(True)
        self._header_bar.props.title = 'Udon Noodles'
        self._header_bar.props.subtitle = 'your reactive functional thought assistant'
        self.set_titlebar(self._header_bar)

        # work sheet
        self._work_sheet = WorkSheet(shape=(100, 100))

        # editor
        self._editor = Editor()

        # notebook
        self._notebook = Gtk.Notebook()
        self._notebook.append_page(self._work_sheet, Gtk.Label.new('Work sheet'))
        self._notebook.append_page(self._editor, Gtk.Label.new('Editor'))

        self._vbox = Gtk.VBox()
        self._status_bar = Gtk.Statusbar()
        self._vbox.pack_start(self._notebook, expand=True, fill=True, padding=0)
        self._vbox.pack_end(self._status_bar, expand=False, fill=True, padding=0)

        self.add(self._vbox)
        self.show_all()


if __name__ == '__main__':
    window = Window()
    window.connect('delete-event', Gtk.main_quit)
    Gtk.main()
