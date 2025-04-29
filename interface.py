# -*- coding: utf-8 -*-
"""
Created on Mon Apr 28 14:36:45 2025

@author: sceadu37
"""

from PyQt5 import QtCore, QtWidgets, QtGui
from pathlib import Path
from argparse import Namespace

import tgrtool

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
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.settings)
        self.setLayout(layout)
        self.settings.select_tgr.clicked.connect(self.selectTGR)
        self.settings.unpack_button.clicked.connect(self.unpackTGR)
    
    def selectTGR(self):
        filename = FileDialog()
        print(f'filename: {filename}')
        if filename:
            print('valid file')
            self.filename = Path(filename[0])
            print(self.filename)
            self.settings.select_tgr.setText(self.filename.stem)
    
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
            
        

class PackWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super(PackWidget, self).__init__(parent)
        self.settings = UnpackSettings(self)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.settings)
        self.setLayout(layout)

        
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
