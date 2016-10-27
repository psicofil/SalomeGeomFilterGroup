# Create groups from filters

try:
    from PyQt4 import uic
except ImportError:
    from PyQt5 import uic

from qtsalome import Qt, QDialog, QMessageBox
from salome.geom.geomtools import getGeompy, GeomStudyTools
import math
import os
import salome_pluginsmanager


class GeomFilterGroupDialog(QDialog):
    
    def __init__(self, context):
        QDialog.__init__(self)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.context = context
        self.directory = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(os.path.join(self.directory, "geom_filter_group_dialog.ui"),
                   self)
        self.geomTool = GeomStudyTools()
        self.geompy = getGeompy()
        
        self.selobj = None
        self.type_o = ''
        self.shapetype = -1

        # Call selectGroupRef function
        self.selectGroupRef()

    # Selected Object
    def selectGroupRef(self):
        self.le_ref_g.setText('')
        self.selobj = None
        self.type_o = ''
        self.shapetype = -1
        self.cb_norm.setEnabled(False)
        try:
            self.selobj = self.geomTool.getGeomObjectSelected()
            # Is a group?
            isgroup = self.geompy.ShapeIdToType(self.selobj.GetType()) == 'GROUP'
            if not isgroup:
                return
            # Type of element
            self.type_o = str(self.selobj.GetTopologyType())
            if self.type_o == 'COMPOUND':
                return
            self.shapetype = self.geompy.ShapeType[self.type_o]
            # Set object Name
            self.le_ref_g.setText(self.selobj.GetName())
            # Set normal availble
            self.cb_norm.setEnabled(self.type_o == 'FACE')
        except Exception as e:
            print(e)
    
    # Run proceed
    def proceed(self):
        try:
            if self.selobj is None:
                return
            # The father of group
            father = self.geompy.GetMainShape(self.selobj)
            # Size
            props = self.geompy.BasicProperties(self.selobj)
            if self.type_o=="EDGE":
                Sref = props[0]
            if self.type_o=="FACE":
                Sref = props[1]
            if self.type_o=="SOLID":
                Sref = props[2]
            # Location
            cm_ref = self.geompy.MakeCDG(self.selobj)
            x_ref, y_ref, z_ref = self.geompy.PointCoordinates(cm_ref)
            # Normal (Element==Face)
            if self.type_o=="FACE":
                vnorm_ref = self.geompy.GetNormal(self.selobj)
            else:
                vnorm_ref = None
            # Create container group
            group = []
            # All Object elements of type self.type_o
            elements = self.geompy.ExtractShapes(father, self.shapetype, True)
            # Create group
            Group_f = self.geompy.CreateGroup(father, self.shapetype)
            # Set color of the group
            from salome import SALOMEDS
            Group_f.SetColor(SALOMEDS.Color(1,0,0))
            # Options
            name_g = str(self.le_nam_g.text())
            pr = eval(str(self.sb_tol.text()))
        except Exception as e:
            QMessageBox.critical(None,'Error', str(e),QMessageBox.Abort)
            return
        try:
            # Selected elements for the group whit the desired conditios
            for i in elements:
                props = self.geompy.BasicProperties(i)
                cm = self.geompy.MakeCDG(i)
                # Element i coordinates
                x, y, z = self.geompy.PointCoordinates(cm)
                # Element i size
                if self.type_o=="EDGE":
                    S = props[0]
                if self.type_o=="FACE":
                    S = props[1]
                if self.type_o=="SOLID":
                    S = props[2]
                # Element==Face i Normal
                if vnorm_ref is None:
                    vnorm = None
                else:
                    vnorm = self.geompy.GetNormal(i)
                    angle = self.geompy.GetAngle(vnorm_ref, vnorm)
                # Comparations
                cond = []
                if self.cb_size.isChecked():
                    cond.append(S<Sref*(1+pr) and S>Sref*(1-pr))
                else:
                    cond.append(True)
                if self.cb_locx.isChecked():
                    if x_ref>=0:
                        cond.append(x<x_ref*(1+pr) and x>x_ref*(1-pr))
                    else:
                        cond.append(x>x_ref*(1+pr) and x<x_ref*(1-pr))
                else:
                    cond.append(True)
                if self.cb_locy.isChecked():
                    if y_ref>=0:
                        cond.append(y<y_ref*(1+pr) and y>y_ref*(1-pr))
                    else:
                        cond.append(y>y_ref*(1+pr) and y<y_ref*(1-pr))
                else:
                    cond.append(True)
                if self.cb_locz.isChecked():
                    if z_ref>=0:
                        cond.append(z<z_ref*(1+pr) and z>z_ref*(1-pr))
                    else:
                        cond.append(z>z_ref*(1+pr) and z<z_ref*(1-pr))
                else:
                    cond.append(True)
                if  self.cb_norm.isChecked() and vnorm is not None:
                    cond.append(angle<0.0+0.001 and angle>0.0-0.001)
                else:
                    cond.append(True)
                if all(cond):
                    ID = self.geompy.GetSubShapeID(father,i)
                    group.append(ID)
#                     cond.append(cond)
        except Exception as e:
            QMessageBox.critical(None,'Error',str(e),QMessageBox.Abort)
            return
        # Add elements desired to Group
        try:
            self.geompy.UnionIDs(Group_f, group)
            # Add group in the gui
            resGroup = self.geompy.addToStudyInFather(father, Group_f, name_g)
            # View group
            self.geomTool.displayShapeByEntry(resGroup)
        except Exception as e:
            QMessageBox.critical(None,'Error',str(e),QMessageBox.Abort)
            return
        return

__dialog=None
def getDialog(context):
    """
    This function returns a singleton instance of the plugin dialog.
    It is mandatory in order to call show without a parent ...
    """
    global __dialog
    if __dialog is None:
      __dialog = GeomFilterGroupDialog(context)
    return __dialog
