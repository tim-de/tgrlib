# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 14:36:45 2025

@author: sceadu37
"""

#from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QByteArray, QBuffer, QDir, QSize
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QMovie
from pathlib import Path
from argparse import Namespace
from io import BytesIO

import tgrtool
import tgrlib

START_FRAME = 0
FRAMES_PER_VIEW = 1
CT_VIEWS = 2

PlayerColorNames = {
    "None": tgrlib.PlayerColor.NONE.value,
    "Red": tgrlib.PlayerColor.RED.value,
    "Blue": tgrlib.PlayerColor.BLUE.value,
    "Green": tgrlib.PlayerColor.GREEN.value,
    "Black": tgrlib.PlayerColor.BLACK.value,
    "Orange": tgrlib.PlayerColor.ORANGE.value,
    "Purple": tgrlib.PlayerColor.PURPLE.value,
    "Cyan": tgrlib.PlayerColor.CYAN.value,
    "Brown": tgrlib.PlayerColor.BROWN.value,
    "Light Gray": tgrlib.PlayerColor.LIGHT_GRAY.value,
    "Gold": tgrlib.PlayerColor.GOLD.value,
    "Dark Gray": tgrlib.PlayerColor.DARK_GRAY.value
}

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("tgrtool v1.2.1")
        
        self.central_widget = QtWidgets.QWidget()
        central_layout = QtWidgets.QVBoxLayout()
        self.menu_bar = MenuBar(self)
        self.widget_switcher = QtWidgets.QStackedWidget()
        central_layout.addWidget(self.menu_bar)
        central_layout.addWidget(self.widget_switcher)
        self.central_widget.setLayout(central_layout)
        self.setCentralWidget(self.central_widget)
        
        self.unpack_widget = UnpackWidget(self)
        self.widget_switcher.addWidget(self.unpack_widget)
        self.pack_widget = PackWidget(self)
        self.widget_switcher.addWidget(self.pack_widget)
        
        self.menu_bar.unpack_button.clicked.connect(lambda: self.switchWidget('unpack_widget'))
        self.menu_bar.pack_button.clicked.connect(lambda: self.switchWidget('pack_widget'))
        
        self.switchWidget('unpack_widget')
    
    def switchWidget(self, target):
        self.widget_switcher.setCurrentWidget(getattr(self, target, self.unpack_widget))
        

class MenuBar(QtWidgets.QWidget) :
    def __init__(self, parent):
        super(MenuBar, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        
        self.unpack_button = QtWidgets.QPushButton('Unpack')
        self.pack_button = QtWidgets.QPushButton('Pack')
        layout.addWidget(self.unpack_button)
        layout.addWidget(self.pack_button)
        
        self.setLayout(layout)
        

class UnpackWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super(UnpackWidget, self).__init__(parent)
        self.settings = UnpackSettings(self)
        self.preview = Preview(self)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.settings)
        layout.addWidget(self.preview)
        self.setLayout(layout)
        self.settings.select_tgr.clicked.connect(self.selectTGR)
        self.settings.select_tgr.clicked.connect(self.preview.render)
        self.settings.color.currentIndexChanged.connect(self.preview.render)
        self.settings.single_frame.stateChanged.connect(self.preview.render)
        self.settings.frame_index.valueChanged.connect(self.preview.render)
        self.settings.unpack_button.clicked.connect(self.unpackTGR)
    
    def selectTGR(self):
        filename = FileDialog()
        print(f'filename: {filename}')
        if filename:
            print('valid file')
            self.filename = Path(filename[0])
            print(self.filename)
            self.settings.select_tgr.setText(self.filename.stem)
            # get frame count from header to update frame_index max value
            self.tgr = tgrlib.tgrFile(self.filename)
            self.tgr.iff.load()
            if self.tgr.iff.data.formtype != "TGAR":
                print(f"Error: invalid file type: {self.iff.data.formtype}")
            self.tgr.read_header()
            self.settings.frame_index.setMaximum(self.tgr.framecount-1)
            
    
    def unpackTGR(self):
        args = Namespace(color=PlayerColorNames.get(self.settings.color.currentText(), tgrlib.PlayerColor.NONE),
                         no_align_frames=(not self.settings.align_frames.isChecked()),
                         fx_error_fix=self.settings.fx_error_fix.isChecked(),
                         single_frame=(self.settings.frame_index.value() if self.settings.single_frame.isChecked() else -1),
                         sprite_sheet=self.settings.sprite_sheet.isChecked(),
                         output=None,
                         config=None,
                         verbose=1,
                         source=self.filename)
        
        print(f"args: {args}")
        tgrtool.unpack(args)
# =============================================================================
#         if not self.settings.align_frames.isChecked():
#             args.append('--no-align-frames')
#         if self.settings.single_frame.isChecked():
#             args.append(f"--single-frame {self.settings.frame_index.value()}")
#         if :
#             args.append("--fx-error-fix")
#         args.append(str(self.filename))
#         print(f"args: {args}")
#         
#         parsed_args = tgrtool.main_parse.parse_args(args)
#         print(f"parsed args: {parsed_args}")
#         parsed_args.func(parsed_args)
# =============================================================================
        
class UnpackSettings(QtWidgets.QWidget):
    def __init__(self, parent):
        super(UnpackSettings, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        
        self.select_tgr = QtWidgets.QPushButton('Select TGR File')
        layout.addWidget(self.select_tgr)
        
        self.color = QtWidgets.QComboBox()
        self.color.addItems(['Red', 'Blue', 'Green', 'Black', 'Orange', 'Purple', 'Cyan', 'Brown', 'Light Gray', 'Gold', 'Dark Gray',])
        row1 = QtWidgets.QHBoxLayout()
        row1.addWidget(QtWidgets.QLabel('Sprite Color'))
        row1.addWidget(self.color)
        layout.addLayout(row1)
        
        self.align_frames = QtWidgets.QCheckBox(text="Align Frames", parent=self)
        self.align_frames.setChecked(True)
        self.fx_error_fix = QtWidgets.QCheckBox(text='FX Error Fix', parent=self)
        self.fx_error_fix.setChecked(False)
        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(self.align_frames)
        row2.addWidget(self.fx_error_fix)
        layout.addLayout(row2)
        
        self.single_frame = QtWidgets.QCheckBox(text='Single Frame', parent=self)
        self.single_frame.setChecked(False)
        self.single_frame.stateChanged.connect(self.toggle_single_frame)
        self.frame_index = QtWidgets.QSpinBox()
        self.frame_index.setRange(0,300)
        self.frame_index.setEnabled(False)
        row3 = QtWidgets.QHBoxLayout()
        row3.addWidget(self.single_frame)
        row3.addWidget(self.frame_index)
        layout.addLayout(row3)
        
        self.sprite_sheet = QtWidgets.QCheckBox(text="Save to Sprite Sheet", parent=self)
        self.sprite_sheet.setChecked(False)
        layout.addWidget(self.sprite_sheet)
        
        self.unpack_button = QtWidgets.QPushButton('Unpack TGR File')
        layout.addWidget(self.unpack_button)
        
        self.setLayout(layout)
    
    def toggle_single_frame(self, state):
        if state == 2:
            self.frame_index.setEnabled(True)
        else:
            self.frame_index.setEnabled(False)
        

class PackWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super(PackWidget, self).__init__(parent)
        self.settings = PackSettings(self)
        self.preview = Preview(self)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.settings)
        layout.addWidget(self.preview)
        self.setLayout(layout)
        self.settings.select_source.clicked.connect(self.selectSource)
        self.settings.select_source.clicked.connect(self.preview.render)
        self.settings.pack_button.clicked.connect(self.packTGR)
    
    def selectSource(self):
        from_sprite_sheet = self.settings.sprite_sheet.isChecked()
        if from_sprite_sheet:
            filename =  FileDialog(isFolder=False, filters=("Kohan Sprite Sheet (*.png)",))
        else:
            filename = FileDialog(isFolder=True)
        print(f'filename: {filename}')
        if filename:
            print('valid file')
            self.filename = Path(filename[0])
            print(self.filename)
            self.settings.select_source.setText(self.filename.stem)
            self.tgr = tgrlib.tgrFile(self.filename, from_sprite_sheet=from_sprite_sheet)
            self.preview.current_frame = 0
            self.preview.movie = None
            
    
    def packTGR(self):
        output = FileDialog(forOpen=False, default_name=self.filename.stem, default_extension=".tgr")
        if not output:
            return
        args = Namespace(color=PlayerColorNames.get(self.settings.color.currentText(), tgrlib.PlayerColor.NONE),
                         no_crop=(not self.settings.crop.isChecked()),
                         portrait=(self.settings.portrait_size.currentText() if self.settings.portrait_mode.isChecked() else None),
                         output=Path(output[0]),
                         config=None,
                         verbose=1,
                         source=self.filename,
                         sprite_sheet=(self.settings.sprite_sheet.isChecked()))
        
        print(f"args: {args}")
        tgrtool.pack(args)


class PackSettings(QtWidgets.QWidget):
    def __init__(self, parent):
        super(PackSettings, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        
        self.sprite_sheet = QtWidgets.QCheckBox(text="Pack from Sprite Sheet", parent=self)
        self.sprite_sheet.setChecked(False)
        self.sprite_sheet.stateChanged.connect(self.toggle_sprite_sheet_mode)
        layout.addWidget(self.sprite_sheet)
        
        self.select_source = QtWidgets.QPushButton('Select Source Folder')
        layout.addWidget(self.select_source)
        
        self.color = QtWidgets.QComboBox()
        self.color.addItems(['None', 'Red', 'Blue', 'Green', 'Black', 'Orange', 'Purple', 'Cyan', 'Brown', 'Light Gray', 'Gold', 'Dark Gray',])
        row1 = QtWidgets.QHBoxLayout()
        row1.addWidget(QtWidgets.QLabel('Sprite Color'))
        row1.addWidget(self.color)
        layout.addLayout(row1)
        
        self.crop = QtWidgets.QCheckBox(text="Crop Transparency", parent=self)
        self.crop.setChecked(True)
        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(self.crop)
        layout.addLayout(row2)
        
        self.portrait_mode = QtWidgets.QCheckBox(text='Portrait Mode', parent=self)
        self.portrait_mode.setChecked(False)
        self.portrait_mode.stateChanged.connect(self.toggle_portrait_mode)
        self.portrait_size = QtWidgets.QComboBox()
        self.portrait_size.addItems(["small", "large",])
        self.portrait_size.setEnabled(False)
        row3 = QtWidgets.QHBoxLayout()
        row3.addWidget(self.portrait_mode)
        row3.addWidget(self.portrait_size)
        layout.addLayout(row3)
        
        self.pack_button = QtWidgets.QPushButton('Pack to TGR File')
        layout.addWidget(self.pack_button)
        
        self.setLayout(layout)
    
    def toggle_portrait_mode(self, state):
        if state == 2:
            self.portrait_size.setEnabled(True)
        else:
            self.portrait_size.setEnabled(False)
    
    def toggle_sprite_sheet_mode(self, state):
        # remove tgr when switching modes to avoid accidentally packing a sprite sheet as a directry
        self.parent().tgr = None
        self.parent().filename = None
        self.parent().preview.render()
        if state == 2:
            self.select_source.setText('Select Sprite Sheet')
        else:
            self.select_source.setText('Select Source Folder')


class Preview(QtWidgets.QWidget):
    def __init__(self, parent):
        super(Preview, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Preview'))
        self.sprite_display = QtWidgets.QLabel()
        self.sprite_display.setMinimumSize(QSize(100, 100))
        self.sprite_display.setMaximumSize(QSize(300, 300))
        #self.sprite_display.setStyleSheet("QLabel { background-color : red; color : blue; }")
        layout.addWidget(self.sprite_display)
        self.buttons = PreviewButtons(self)
        layout.addWidget(self.buttons)
        self.setLayout(layout)
        
        self.current_frame = 0
        
        self.buttons.next_frame.clicked.connect(lambda: self.switch_frame("frame", absolute=False, step=1))
        self.buttons.prev_frame.clicked.connect(lambda: self.switch_frame("frame", absolute=False, step=-1))
        self.buttons.next_view.clicked.connect(lambda: self.switch_frame("view", absolute=False, step=1))
        self.buttons.prev_view.clicked.connect(lambda: self.switch_frame("view", absolute=False, step=-1))
        self.buttons.next_anim.clicked.connect(lambda: self.switch_frame("animation", absolute=False, step=1))
        self.buttons.prev_anim.clicked.connect(lambda: self.switch_frame("animation", absolute=False, step=-1))
        self.buttons.play.toggled.connect(self.play_current_view)
        
        self.movie = None
        
        
    def render(self):
        # prevent attempt to render when no file has been selected
        if not getattr(self.parent(), 'tgr', None):
            self.sprite_display.clear()
            return
        print('Rendering thumbnail ... ', end='')
        mode = self.parent().tgr.read_from
        if mode == '.TGR':
            if not self.parent().tgr.loaded:
                self.parent().tgr.load()
            preview = tgrtool.unpack_frame(self.parent().tgr,
                                         (self.parent().settings.frame_index.value() if self.parent().settings.single_frame.isChecked() else self.current_frame),
                                         color=self.parent().settings.color.currentIndex()+1,
                                         )
        elif mode in ('.PNG', '', ):
            preview = self.parent().tgr.imgs[self.current_frame]
            
        img_buffer = BytesIO()
        preview.save(img_buffer, format='PNG')
        pixmap = QPixmap()
        pixmap.loadFromData(img_buffer.getvalue())
        self.sprite_display.setPixmap(pixmap)
        print('finished!')
    
    def play_current_view(self, state):
        print(f"state: {state}")
        if state == True:
            if self.movie:
                self.movie.setPaused(False)
            else:
                stream = self.make_gif_from_view()   
                byte_array = QByteArray(stream.getvalue())
                self.buffer = QBuffer()
                self.buffer.setData(byte_array)
                self.movie = QMovie(self.buffer, QByteArray())
                self.sprite_display.setMovie(self.movie)
                self.sprite_display.setMargin(20)
            self.movie.start()
        elif state == False:
            self.movie.setPaused(True)
        
    
    def make_gif_from_view(self):
        tgr = self.parent().tgr
        anim_index, view_index = self.get_anim_data(self.current_frame)
        start_frame_index = self.get_frame_from_view(anim_index, view_index)
        gif_length = tgr.animations[anim_index][FRAMES_PER_VIEW]
        imgs = []
        img_buffer = BytesIO()
        for i in range(start_frame_index, start_frame_index+gif_length):
            imgs.append(tgrtool.unpack_frame(tgr, i, color=self.parent().settings.color.currentIndex()+1))
        imgs[0].save(img_buffer, format="gif", save_all=True, append_images=imgs[1:], duration=100, loop=0, disposal=2)
        imgs[0].save("out.gif", save_all=True, append_images=imgs[1:], duration=100, loop=0, disposal=2)
        return img_buffer
        
    
    
    def switch_frame(self, scope: str="frame", absolute: bool=False, step: int=1):
        """
        Switches the current preview frame.

        Parameters
        ----------
        scope : str, (default : "frame")
            Specifies the scope of the step argument. Can be "animation", "view", or "frame"
        absolute : bool, (default : False)
            If True, step will be interpreted as absolute. If False, step will be interpreted as relative to the current position
        step : int, optional
            Specifies how many frames/views/animations to go forward or back.

        Returns
        -------
        None.

        """
        self.buttons.play.setChecked(False)
        self.movie = None
        init_frame = self.current_frame
        init_anim, init_view = self.get_anim_data(init_frame)
        match scope:
            case "frame":
                self.current_frame = self.constrain_frame(
                    (step if absolute else self.current_frame + step))
            case "view":
                anim_index, view_index = self.get_anim_data(self.current_frame)
                self.current_frame = self.change_view(anim_index, view_index + step)
                # get the current view index and animation index from the current frame
                # ignore absolute flag for now
                # therefore, create new view index using step size and current view index.
                # while the new index in negative, step back 1 animation and add the number of view in it to the new index
                # while the new index is greater than the number of views in the current animation, subtract the current number of views and add 1 to the animation index
                # return the 0th frame of the new view
            case "animation":
                anim_index, view_index = self.get_anim_data(self.current_frame)
                self.current_frame = self.change_anim((step if absolute else anim_index + step))
            case _:
                print(f"invalid scope \"{scope}\" for switch_frame")
        
        tgrlib.log(1,
                   "Info",
                   "started at frame {0}, anim {1}, view {2}; ended at frame {3}, anim {4}, view {5}",
                   init_frame,
                   init_anim,
                   init_view,
                   self.current_frame,
                   *self.get_anim_data(self.current_frame))
        self.render()
                
    
    def constrain_frame(self, frame_index):
        if frame_index in range(self.parent().tgr.framecount):
            return frame_index
        elif frame_index >= self.parent().tgr.framecount:
            return self.parent().tgr.framecount - 1
        else:
            return 0
    
    def change_view(self, anim_index, view_index, ):
        anims = self.parent().tgr.animations
        while view_index < 0:
            if anim_index > 0:
                anim_index -= 1
                view_index += anims[anim_index][CT_VIEWS]
            else:
                view_index = 0 # prevents view index from staying negative when attempting to step below frame 0
                break
            
        while view_index >= anims[anim_index][CT_VIEWS]:
            #view_index -= anims[anim_index][CT_VIEWS]
            if anim_index < len(anims) - 1:
                view_index -= anims[anim_index][CT_VIEWS]
                anim_index += 1
            else:
                view_index = anims[anim_index][CT_VIEWS] - 1
                break
            
        return self.get_frame_from_view(anim_index, view_index)
    
    def change_anim(self, anim_index):
        if anim_index in range(self.parent().tgr.anim_count):
            return self.get_frame_from_view(anim_index, 0)
        elif anim_index >= self.parent().tgr.anim_count:
            return self.get_frame_from_view(self.parent().tgr.anim_count - 1, 0)
        else:
            return 0
            
    def get_anim_data(self, frame_index):
        anims = self.parent().tgr.animations
        for i in range(len(anims)):
            cur_anim = anims[i]
            next_anim = anims[i+1] if i+1 < len(anims) else None
                
            if (frame_index >= cur_anim[START_FRAME] and (next_anim is None or frame_index < next_anim[START_FRAME])):
                view = int((frame_index - cur_anim[START_FRAME]) / cur_anim[FRAMES_PER_VIEW])
                return (i, view)
        return (len(anims) - 1, 0) # return a valid value in case something goes wrong
        
    def get_frame_from_view(self, anim_index, view_index):
        anim = self.parent().tgr.animations[anim_index]
        return self.constrain_frame(anim[START_FRAME] + view_index * anim[FRAMES_PER_VIEW])
            

class PreviewButtons(QtWidgets.QWidget):
    def __init__(self, parent):
        super(PreviewButtons, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout()
        self.play = QtWidgets.QPushButton("Play")
        self.play.setCheckable(True)
        self.play.setChecked(False)
        self.next_frame = QtWidgets.QPushButton("Next Frame")
        self.next_view = QtWidgets.QPushButton("Next View")
        self.next_anim = QtWidgets.QPushButton("Next Animation")
        self.prev_frame = QtWidgets.QPushButton("Prev Frame")
        self.prev_view = QtWidgets.QPushButton("Prev View")
        self.prev_anim = QtWidgets.QPushButton("Prev Animation")
        layout.addWidget(self.prev_anim)
        layout.addWidget(self.prev_view)
        layout.addWidget(self.prev_frame)
        layout.addWidget(self.play)
        layout.addWidget(self.next_frame)
        layout.addWidget(self.next_view)
        layout.addWidget(self.next_anim)
        self.setLayout(layout)
        
        



def FileDialog(directory=None, forOpen=True, isFolder=False, multiple=False, filters=("Kohan Graphical Assets (*.tgr)",), default_name=None, default_extension=None):
    print(directory)
    print(f"isFolder: {isFolder}")
    options = QtWidgets.QFileDialog.Options()
    options |= QtWidgets.QFileDialog.DontUseCustomDirectoryIcons
    dialog = QtWidgets.QFileDialog()

    dialog.setFilter(dialog.filter() | QDir.Hidden)

    # ARE WE TALKING ABOUT FILES OR FOLDERS
    if isFolder:
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        options |= QtWidgets.QFileDialog.ShowDirsOnly
    else:
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles if multiple else QtWidgets.QFileDialog.AnyFile)
    # OPENING OR SAVING
    dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptOpen) if forOpen else dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)

    # SET FILTERS, IF SPECIFIED
    if filters and isFolder is False:
        if type(filters) is str:
            filters = (filters,)
        dialog.setNameFilters(filters)
    
    if default_name:
        dialog.selectFile(str(default_name))
    
    if default_extension:
        dialog.setDefaultSuffix(default_extension)

    # SET THE STARTING DIRECTORY
    if directory:
        dialog.setDirectory(str(directory))

    dialog.setOptions(options)    
    if isFolder:
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)

    if dialog.exec() == QtWidgets.QDialog.Accepted:
        paths = dialog.selectedFiles()  # returns a list
        return paths
    else:
        return None
