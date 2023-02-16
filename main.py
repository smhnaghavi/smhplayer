import gi
import sys
gi.require_version("Gtk", "3.0")
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gtk, Gst, GLib, GstVideo
from pathlib import Path
from player import Player
from template.dialogs import FileChooser, DialogWindow
import time

SLIDER_REFRESH = 1000

class PlayerUI:
    def __init__(self):
        builder = Gtk.Builder()
        builder.add_from_file("template/smhplayer.glade")
        
        self.player = Player()
        self.player.cust_func = self.cust_func
        self.gtksink = Gst.ElementFactory.make("gtksink")
        self.player.playbin.set_property("video-sink", self.gtksink)

        window = builder.get_object("window")
        self.playBtn = builder.get_object("playBtn")
        chooserBtn = builder.get_object("chooserBtn")
        stopBtn = builder.get_object("stopBtn")
        nextBtn = builder.get_object("nextBtn")
        prevBtn = builder.get_object("prevBtn")
        
        self.playlistBox = builder.get_object("playlist")
        self.headerBar = builder.get_object("headerBar")
        playArea = builder.get_object("playArea")
        playArea.add(self.gtksink.props.widget)
        self.gtksink.props.widget.set_hexpand(True)
        self.gtksink.props.widget.set_vexpand(True)
        
        self.seeker = builder.get_object("seeker")
        self.durationText = builder.get_object("duration")

        self.volumeBar = builder.get_object("volume")
        self.volumeBar.set_value(self.player.getVolume())
        self.playIco = builder.get_object("playIco")
        self.pauseIco = builder.get_object("pauseIco")

        window.set_title("SMHPlayer")
        
        window.connect("destroy", self.onDestroy)
        self.playBtn.connect("clicked", self.onPlay)
        nextBtn.connect("clicked", self.onNext)
        prevBtn.connect("clicked", self.onPrev)
        stopBtn.connect("clicked", self.onStop)

        self.volumeBar.connect("value-changed", self.changeVolume)

        chooserBtn.connect("clicked", self.onChooseClick)

        self.playlistBox.connect("row-activated", self.onSelectionActivated)

        self.sliderHandlerId = self.seeker.connect("value-changed", self.onSliderSeek)
      
        self.player.bus.enable_sync_message_emission()
        self.player.bus.connect("sync-message::element", self.onSyncMessage)

        self.warning = DialogWindow()

        window.show()
        Gtk.main()

    def onSyncMessage(self, bus, message):
        pass

    def cust_func(self, next=True): 
        playlist = self.playlistBox.get_children()
        currentIndex = playlist.index(self.playlistBox.get_selected_row())
        if next:
            if currentIndex >= len(playlist)-1:
                currentIndex = 0
            else:
                currentIndex += 1
        else:
            if currentIndex == 0:
                currentIndex = len(playlist)-1
            else:
                currentIndex -= 1

        self.playlistBox.select_row(playlist[currentIndex])
        self.onSelectionActivated(self.playlistBox, playlist[currentIndex])

    def refreshPlaylist(self, playlist, listBox):
        for location in playlist:
            row = Gtk.ListBoxRow()
            hbox = Gtk.Box(spacing=50)
            setattr(row, "path", location)
            setattr(row, "name", Path(location).name)
            row.add(hbox)
            label = Gtk.Label(label=Path(location).name)
            hbox.pack_start(label, False, False, 1)
            listBox.add(row)
        listBox.show_all()

    def refreshIcons(self):
        if self.player.status == Gst.State.PLAYING:
            self.playBtn.set_label("Pause")
            self.playBtn.set_image(self.pauseIco)
        else:
            self.playBtn.set_image(self.playIco)
            self.playBtn.set_label("Play")
        
    def refreshSlider(self):  
        if self.player.status != Gst.State.PLAYING:
            return False
        else:
            try:
                success, duration = self.player.getDuration()
                d = float(duration) / Gst.SECOND
                if not success:
                    Exception("Error Occured when fetching duration")
                else:
                    self.seeker.set_range(0, d)
                success, position = self.player.getPosition()
                
                if not success:
                    Exception("Couldn't fetch current song position to update slider")
                                
                p = float(position) / Gst.SECOND

                durationToShow = str(time.strftime("%H:%M:%S", time.gmtime(d)))
                postionToShow = str(time.strftime("%H:%M:%S", time.gmtime(p)))
                self.durationText.set_label(postionToShow+"/"+durationToShow)

                self.seeker.handler_block(self.sliderHandlerId)
                self.seeker.set_value(p)
                self.seeker.handler_unblock(self.sliderHandlerId)
 
            except Exception as e:
                print(e)

            return True

    def onDestroy(self, *args):
        Gtk.main_quit()
        
    def onPlay(self, button=None):
        if not self.playlistBox.get_selected_row():
            self.warning.on_warn_clicked(widget=self.warning, text="No Media Selected!", description="Please select a media to play!")
        elif self.player.status != Gst.State.PLAYING:
            self.player.play()
            self.gtksink.props.widget.show()
            GLib.timeout_add(SLIDER_REFRESH, self.refreshSlider)
        else:
            self.player.pause()
        self.refreshIcons()

    def onChooseClick(self, window):
        choose = FileChooser()
        self.refreshPlaylist(choose.selected, self.playlistBox)    

    def onSelectionActivated(self, listbox, row): 
        selected_song = getattr(row, "path")
        name = getattr(row, "name")
        selected_song = Gst.filename_to_uri(selected_song)
        self.player.setUri(selected_song)
        self.headerBar.set_title(name)
        self.onPlay()
        
    def onSliderSeek(self, slider):
        self.player.seek(self.seeker.get_value())

    def onStop(self, button=None):
        self.player.changeState(Gst.State.NULL)
        self.seeker.set_value(0)
        self.gtksink.props.widget.hide()
        self.refreshIcons()

    def onPrev(self, button=None):
        if not self.playlistBox.get_selected_row():
            self.warning.on_warn_clicked(widget=self.warning, text="No Media Selected!", description="Please select a media!")
        else:
            self.cust_func(next=False)

    def onNext(self, button=None):
        if not self.playlistBox.get_selected_row():
            self.warning.on_warn_clicked(widget=self.warning, text="No Media Selected!", description="Please select a media!")
        else:
            self.cust_func(next=True)

    def changeVolume(self, widget, val):
        self.player.setVolume(val)


def main(args):
    PlayerUI()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
