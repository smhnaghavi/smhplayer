import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

class FileChooser(Gtk.Window):
    def __init__(self):
        dialog = Gtk.FileChooserDialog(title="Choose Files", action=Gtk.FileChooserAction.OPEN)
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        dialog.set_select_multiple(True)
        self.add_filters(dialog)
        self.selected = []
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.onSelect(dialog)
        elif response == Gtk.ResponseType.CANCEL:
            self.onCancel(dialog)

    def add_filters(self, dialog):
        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

    def onSelect(self, dialog):
        self.selected = dialog.get_filenames()
        dialog.destroy()

    def onCancel(self, dialog):
        dialog.destroy()

class DialogWindow(Gtk.Window):
    def on_warn_clicked(self, widget, text, description):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text=text,
        )
        dialog.format_secondary_text(description)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            dialog.destroy()