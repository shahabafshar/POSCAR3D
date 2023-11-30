import sys
import json
import numpy as np
import pyqtgraph.opengl as gl
from PyQt5 import QtGui
from PyQt5.QtWidgets import QFileDialog, QVBoxLayout, QPushButton, QMainWindow, QApplication, QStatusBar, QWidget, QLabel
from PyQt5.QtCore import Qt
from pyqtgraph import Vector

# Load atomic data from a JSON file
with open('atomic_data.json', 'r') as f:
    atomic_data = json.load(f)

class CustomGLViewWidget(gl.GLViewWidget):
    def __init__(self, *args, **kwargs):
        super(CustomGLViewWidget, self).__init__(*args, **kwargs)
        self.initial_dist = 200  # Adjusted for better initial zoom
        self.setCameraPosition(distance=self.initial_dist)
        self.initialCameraPosition = self.cameraPosition()
        self.mousePos = None

    def mousePressEvent(self, ev):
        self.mousePos = ev.pos()
        super(CustomGLViewWidget, self).mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if ev.buttons() == Qt.LeftButton and QtGui.QGuiApplication.keyboardModifiers() == Qt.ShiftModifier:
            diff = ev.pos().y() - self.mousePos.y()
            self.pan(0, 0, diff)
            self.mousePos = ev.pos()
        else:
            super(CustomGLViewWidget, self).mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        super(CustomGLViewWidget, self).mouseReleaseEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        self.setCameraPosition(distance=self.initial_dist, elevation=30, azimuth=45)
        self.opts['center'] = QtGui.QVector3D(*self.centerOfRotation)

class POSCAR3DViewer(QMainWindow):
    def __init__(self, parent=None):
        super(POSCAR3DViewer, self).__init__(parent)
        self.setWindowTitle('POSCAR3D Viewer')
        self.setGeometry(100, 100, 800, 900)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.view = CustomGLViewWidget()
        self.layout.addWidget(self.view)

        # Label for instructions
        self.instructions_label = QLabel()
        self.instructions_label.setText("<b>Zoom</b>: Scroll middle mouse button, "
                                       "<b>Rotate</b>: Left-click and drag, "
                                       "<b>Pan</b>: Right-click and drag, "
                                       "<b>Vertical Pan</b>: Shift + Left-click and drag")
        self.instructions_label.setMaximumHeight(20)
        self.instructions_label.setWordWrap(False)  # Ensure label uses only one line
        self.layout.addWidget(self.instructions_label)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.load_button = QPushButton('Load POSCAR')
        self.load_button.clicked.connect(self.load_poscar)
        self.layout.addWidget(self.load_button)

        # This will hold the center of rotation (the center of the lattice)
        self.view.centerOfRotation = [0, 0, 0]

    def load_poscar(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open POSCAR File", "", "POSCAR Files (*)", options=options)
        if file_path:
            try:
                atom_types, atom_counts, positions, lattice_vectors = self.parse_poscar(file_path)
                self.update_plot(atom_types, atom_counts, positions, lattice_vectors)
                self.status_bar.showMessage("Loaded POSCAR file successfully.")
            except Exception as e:
                self.status_bar.showMessage(f"Error loading POSCAR file: {str(e)}")

    def parse_poscar(self, filename):
        with open(filename, 'r') as file:
            lines = file.readlines()

        scale_factor = float(lines[1].strip())
        lattice_vectors = np.array([list(map(float, line.split())) for line in lines[2:5]]) * scale_factor
        atom_types = lines[5].split()
        atom_counts = list(map(int, lines[6].split()))
        coordinates_start_line = 9 if lines[8].strip() == 'Selective dynamics' else 8

        positions = []
        for i, line in enumerate(lines[coordinates_start_line + 1:coordinates_start_line + 1 + sum(atom_counts)]):
            if line.strip():
                positions.append(np.array(list(map(float, line.split()[:3]))))

        if lines[coordinates_start_line].strip() == 'Direct':
            positions = [np.dot(pos, lattice_vectors) for pos in positions]

        self.view.centerOfRotation = np.mean(lattice_vectors, axis=0)
        return atom_types, atom_counts, positions, lattice_vectors

    def update_plot(self, atom_types, atom_counts, positions, lattice_vectors):
        self.view.clear()
        offset = 0
        for atom_type, count in zip(atom_types, atom_counts):
            for i in range(count):
                pos = positions[offset + i]
                color = atomic_data[atom_type]['color']
                color = [c / 255.0 for c in color]  # Convert from 0-255 to 0-1 scale
                radius = atomic_data[atom_type]['van_der_waals_radius']
                self.draw_atom(pos, radius, color)
            offset += count
        self.draw_lattice_box(lattice_vectors)
        self.view.opts['center'] = Vector(*self.view.centerOfRotation)

    def draw_atom(self, pos, radius, color):
        sphere_mesh = gl.MeshData.sphere(rows=10, cols=20, radius=radius)
        sphere = gl.GLMeshItem(meshdata=sphere_mesh, smooth=True, color=color, shader='shaded', glOptions='opaque')
        sphere.translate(*pos, 0)
        self.view.addItem(sphere)

    def draw_lattice_box(self, lattice_vectors):
        # Calculate lattice corners
        a, b, c = lattice_vectors
        # Define vertices of the lattice box
        vertices = np.array([
            [0, 0, 0], a, b, a+b, c, a+c, b+c, a+b+c
        ])
        # Define the edges connecting the vertices
        edges = [(0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3),
                 (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7)]
        # Create a line item for each edge
        for edge in edges:
            line = np.array([vertices[edge[0]], vertices[edge[1]]])
            line_item = gl.GLLinePlotItem(pos=line, color=(1, 1, 1, 1), width=1.5, antialias=True)
            self.view.addItem(line_item)


def main():
    app = QApplication(sys.argv)
    viewer = POSCAR3DViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
