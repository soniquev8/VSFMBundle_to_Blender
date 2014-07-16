# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Import VSFM camera",
    "author": "Brad Stansell",
    "version": (0, 8),
    "blender": (2, 63, 0),
    "location": "File > Import > VSFM camera",
    "description": "Imports a Blender (2.4x or 2.5x) Python script from VSFM",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

#"""
# This script loads a Blender Python script from the VSFM camera
# tracker program into Blender 2.5x+.
#
# It processes the script as a text file and not as a Python executable
# because of the incompatible Python APIs of Blender 2.4x/2.5x/2.6x.
# """

import bpy
from bpy.props import *
import mathutils
import os
import string
import math
from pathlib import *
import fileinput
from math import radians, degrees
from mathutils import Matrix, Vector

def voodoo_import(filepath,ld_cam,directory):

    #print(filepath)
    print("Importing camera data")
    # Setup new camera specifically for VSFM data
    bpy.ops.object.camera_add()
    bpy.context.active_object.name = "VSFM Camera"
    bpy.context.active_object.data.name = "VSFM Camera"
    VSFMObj = bpy.data.objects["VSFM Camera"]
    VSFMCam = bpy.data.cameras["VSFM Camera"]

    cameraDataLines = open(filepath,'r').readlines()
    directory = os.path.dirname(filepath)
    imagesDir = os.path.join(directory, 'visualize')
    imagelist = os.listdir(imagesDir)

    imageClip = bpy.ops.clip.open(directory=imagesDir,
                      files=[{"name":"00000000.jpg", "name":"00000000.jpg"}],
                      relative_path=True)

   
    
    # add an image size detection subroutine
    width = 3264.0
    height = 2448.0
    corresponding_frame = 1
    xrot = Matrix.Rotation(radians(90.0), 4, 'X')

#      code  for testing purposes
# f = os.path.abspath('/Volumes/Data/Desktop/church reconstruction/churchdense.nvm.cmvs/00/cameras_v2.txt')
# parent = os.path.dirname(f)
# imagedir = os.path.join(parent, 'visualize')
# print(f)
# print(parent)
# print(imagedir)
# imagelist = os.listdir(imagedir)
# print(imagelist)
# cameraDataLines = open(f, 'r').readlines()

# cameras_v2.txt file format (per camera)
# ==========================
# 0  Filename (of the undistorted image in visualize sub-folder)
# 1  Original filename
# 2  * Focal Length (of the undistorted image)
# 3  2-vec Principal Point (image center)
# 4  * 3-vec Translation T (as in P = K[R T])
# 5  3-vec Camera Position C (as in P = K[R -RC])
# 6  3-vec Axis Angle format of R
# 7  4-vec Quaternion format of R
# 8  * row1 Matrix format of R (3 items)
# 9  * row2 Matrix format of R (3 items)
# 10 * row3 Matrix format of R (3 items)
# 11 [Normalized radial distortion] = [radial distortion] * [focal length]^2
# 12 3-vec Lat/Lng/Alt from EXIF


    for filename in imagelist:
        # Find the line in cameras_v2.txt that correlates with the file name
        cameraStartLine = cameraDataLines.index(filename + '\n')
        
        temp = (cameraDataLines[cameraStartLine + 2].strip())
        focal_length = float(temp)

        temp = (cameraDataLines[cameraStartLine + 4].strip())
        translate = tuple(map(float, temp.split()))
        
        #temp = (cameraDataLines[cameraStartLine + 8].strip())
        #rot1 = tuple(map(float, temp.split()))
        #temp = (cameraDataLines[cameraStartLine + 9].strip())
        #rot2 = tuple(map(float, temp.split()))
        temp = (cameraDataLines[cameraStartLine + 7].strip())
        rot3 = tuple(map(float, temp.split()))
        #rotation = [rot1,
                  #  rot2,
                  #  rot3]
        #world = getWorld(translate, rotation)
        
        VSFMCam.angle_x = math.atan(width / (focal_length * 2.0)) * 2.0
        VSFMCam.angle_y = math.atan(height / (focal_length * 2.0)) * 2.0  
        VSFMObj.rotation_quaternion = rot3
        VSFMObj.location = translate
        #VSFMObj.matrix_world = world * xrot
        #VSFMCam.keyframe_insert(data_path='angle_x', frame=corresponding_frame)
        #VSFMCam.keyframe_insert(data_path='angle_y', frame=corresponding_frame)
        VSFMObj.keyframe_insert(data_path='location', frame=corresponding_frame)
        VSFMObj.keyframe_insert(data_path='rotation_quaternion', frame=corresponding_frame)
        VSFMCam.keyframe_insert(data_path='lens', frame=corresponding_frame)
        #VSFMObj.keyframe_insert(data_path='matrix_world', frame=corresponding_frame)
        corresponding_frame += 1
    return {'FINISHED'}

def getWorld(translation, rotation):
    t = Vector(translation).to_4d()
    mr = Matrix()
    for row in range(3):
        mr[row][0:3] = rotation[row]

    mr.transpose() # = Inverse rotation
        
    p = -(mr * t) # Camera position in world coordinates
    p[3] = 1.0

    m = mr.copy()
    m.col[3] = p # Set translation to camera position
    return m
     
#Operator
class ImportVoodooCamera(bpy.types.Operator):
    """"""
    bl_idname = "import.voodoo_camera"
    bl_label = "Import VSFM data"
    bl_description = "Load a Blender export script from the VSFM motion tracker"
    bl_options = {'REGISTER', 'UNDO'}

    filepath = StringProperty(name="File Path",
        description="Filepath used for processing the script",
        maxlen= 1024,default= "")

    # filter_python = BoolProperty(name="Filter python",
    # description="",default=True,options={'HIDDEN'})

    directory = StringProperty()

    load_camera = BoolProperty(name="Load camera",
        description="Load the camera",
        default=True)

    def execute(self, context):
        voodoo_import(self.filepath,self.load_camera,self.directory)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


# Registering / Unregister
def menu_func(self, context):
    self.layout.operator(ImportVoodooCamera.bl_idname, text="Voodoo camera", icon='PLUGIN')


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func)


if __name__ == "__main__":
    register()


