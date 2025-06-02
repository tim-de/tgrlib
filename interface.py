# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 14:36:45 2025

@author: sceadu37
"""

from PyQt5 import QtCore, QtWidgets, QtGui
from pathlib import Path
from argparse import Namespace
from io import BytesIO

import tgrtool
import tgrlib

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
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
            self.tgr = tgrlib.tgrFile(self.filename, is_sprite=False)
            self.tgr.iff.load()
            if self.tgr.iff.data.formtype != "TGAR":
                print(f"Error: invalid file type: {self.iff.data.formtype}")
            self.tgr.read_header()
            self.settings.frame_index.setMaximum(self.tgr.framecount-1)
            
    
    def unpackTGR(self):
        args = Namespace(color=self.settings.color.currentIndex()+1,
                         no_align_frames=(not self.settings.align_frames.isChecked()),
                         fx_error_fix=self.settings.fx_error_fix.isChecked(),
                         single_frame=(self.settings.frame_index.value() if self.settings.single_frame.isChecked() else -1),
                         output=None,
                         config=None,
                         verbose=False,
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
        self.settings.select_folder.clicked.connect(self.selectFolder)
        self.settings.select_folder.clicked.connect(self.preview.render)
        self.settings.pack_button.clicked.connect(self.packTGR)
    
    def selectFolder(self):
        filename = FileDialog(isFolder=True)
        print(f'filename: {filename}')
        if filename:
            print('valid file')
            self.filename = Path(filename[0])
            print(self.filename)
            self.settings.select_folder.setText(self.filename.stem)
            # get frame count from header to update frame_index max value
            self.tgr = tgrlib.tgrFile(self.filename)
            
    
    def packTGR(self):
        args = Namespace(color=self.settings.color.currentIndex()+1,
                         no_crop=(not self.settings.crop.isChecked()),
                         portrait=(self.settings.portrait_size.value() if self.settings.portrait_mode.isChecked() else None),
                         output=None,
                         config=None,
                         verbose=False,
                         source=self.filename)
        
        print(f"args: {args}")
        tgrtool.unpack(args)


class PackSettings(QtWidgets.QWidget):
    def __init__(self, parent):
        super(PackSettings, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        
        self.select_folder = QtWidgets.QPushButton('Select Source Folder')
        layout.addWidget(self.select_folder)
        
        self.color = QtWidgets.QComboBox()
        self.color.addItems(['Red', 'Blue', 'Green', 'Black', 'Orange', 'Purple', 'Cyan', 'Brown', 'Light Gray', 'Gold', 'Dark Gray',])
        row1 = QtWidgets.QHBoxLayout()
        row1.addWidget(QtWidgets.QLabel('Sprite Color'))
        row1.addWidget(self.color)
        layout.addLayout(row1)
        
        self.crop = QtWidgets.QCheckBox(text="Crop Transparency", parent=self)
        self.crop.setChecked(True)
        self.fx_error_fix = QtWidgets.QCheckBox(text='FX Error Fix', parent=self)
        self.fx_error_fix.setChecked(False)
        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(self.crop)
        row2.addWidget(self.fx_error_fix)
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


class Preview(QtWidgets.QWidget):
    def __init__(self, parent):
        super(Preview, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Preview'))
        self.sprite_display = QtWidgets.QLabel()
        layout.addWidget(self.sprite_display)
        self.setLayout(layout)
        
    def render(self):
        # prevent attempt to render when no file has been selected
        if not hasattr(self.parent(), 'tgr'):
            return
        print('Rendering thumbnail ... ', end='')
        mode = self.parent().tgr.read_from
        if mode == '.TGR':
            self.parent().tgr.load()
            preview = tgrtool.unpack_frame(self.parent().tgr,
                                         0,
                                         color=self.parent().settings.color.currentIndex()+1,
                                         )
        elif mode in ('.PNG', '', ):
            preview = self.parent().tgr.imgs[0]
            
        img_buffer = BytesIO()
        preview.save(img_buffer, format='PNG')
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(img_buffer.getvalue())
        self.sprite_display.setPixmap(pixmap)
        print('finished!')


def FileDialog(directory=None, forOpen=True, isFolder=False, multiple=False, filters=("Kohan Graphical Assets (*.tgr)",), default_name=None, default_extension=None):
    print(directory)
    print(f"isFolder: {isFolder}")
    options = QtWidgets.QFileDialog.Options()
    options |= QtWidgets.QFileDialog.DontUseCustomDirectoryIcons
    dialog = QtWidgets.QFileDialog()

    dialog.setFilter(dialog.filter() | QtCore.QDir.Hidden)

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
