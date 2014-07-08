_# ##### BEGIN GPL LICENSE BLOCK #####
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

# <pep8-80 compliant>

bl_info = {
    "name": "Import VSFM format",
    "author": "Konrad Koelzer, Brad Stansell",
    "version": (1, 0),
    "blender": (2, 6, 2),
    "location": "File > Import",
    "description": "Import Bundler cameras, images and point cloud from a "
                   "bundled scene",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": 'TESTING',
    "category": "Import-Export"}

# Copyright (C) 2012: Konrad Koelzer, koelzk at web dot de

# To support reload properly, try to access a package var,
# if it's there, reload everything



import bpy
from bpy.props import CollectionProperty, StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy_extras.object_utils import AddObjectHelper, object_data_add
import math
from math import radians, degrees
from mathutils import Matrix, Vector
import os
import os.path

class BundlePoint:
    def __init__(self, bfr):
        self.position = bfr.readFloatItems()
        self.color = bfr.readIntItems()
        bfr.readLine() # Skip mapped image features

class BundleCamera:
    def __init__(self, bfr):
            self.focal_length, self.k1, self.k2 = bfr.readFloatItems()
            self.rotation = [bfr.readFloatItems(),
                             bfr.readFloatItems(),
                             bfr.readFloatItems()]
            self.translation = bfr.readFloatItems()
            self.image_path = ""
            self.world = self.getWorld()
            # Set if camera contains valid data:
            self.valid = self.focal_length > 0.0

    def getWorld(self):
        t = Vector(self.translation).to_4d()
        mr = Matrix()
        for row in range(3):
            mr[row][0:3] = self.rotation[row]

        mr.transpose() # = Inverse rotation

        p = -(mr * t) # Camera position in world coordinates
        p[3] = 1.0

        m = mr.copy()
        m.col[3] = p # Set translation to camera position
        return m


class BundleFileReader:
    def __init__(self, filepath):
        f = open(filepath, "r")
        self.lines = list(map(lambda x: x.strip(), f.readlines()))
        self.row = 0
        self.cameras = []
        self.points = []

        # Read file content:
        self.readContent()

    def readLine(self):
        while self.row < len(self.lines):
            self.line = self.lines[self.row]
            self.row += 1
            # Skip empty lines and comments:
            if len(self.line) > 0 and not self.line.startswith("#"):
                return self.line
        return None # Reached end

    def readItems(self):
        return self.readLine().split(" ")

    def readIntItems(self):
        return tuple(map(int, self.readLine().split(" ")))

    def readFloatItems(self):
        return tuple(map(float, self.readLine().split(" ")))

    def readCameras(self, cameraCount):
        for index in range(cameraCount):
            # Add cameras:
            camera = BundleCamera(self)
            if camera.valid:
                self.cameras.append(camera) # Only add valid cameras


    def readPoints(self, pointCount):
        for index in range(pointCount):
            # Add points:
            self.points.append(BundlePoint(self))

    def readContent(self):
        cameraCount, pointCount = map(int, self.readItems())
        self.readCameras(cameraCount)
        self.readPoints(pointCount)
        print("Found %d valid cameras and %d points." % (len(self.cameras),
              len(self.points)))


    def addImageListFile(self, filepath):
        # Load image paths:
        f = open(filepath, "r")
        paths = list(map(
            lambda x: os.path.basename(x.split()[0]), f.readlines()))
        f.close()

        # Map to cameras:
        for index in range(len(self.cameras)):
            self.cameras[index].image_path = paths[index]

def load_scene(filepath):
    # Load bundle file:
    bfr = BundleFileReader(os.path.join(filepath, "bundle", "bundle.out"))
    image_list_path = os.path.join(filepath, "list.txt")
    bfr.addImageListFile(image_list_path)
    return bfr

#### BLENDER SCENE MANIPULATION ####

xrot = Matrix.Rotation(radians(90.0), 4, 'X')

def add_obj(data, objName):
    scn = bpy.context.scene

    for o in scn.objects:
        o.select = False

    nobj = bpy.data.objects.new(objName, data)
    #nobj.rotation_euler = [radians(90.0), 0.0, 0.0]
    scn.objects.link(nobj)
    nobj.select = True

    if scn.objects.active is None or scn.objects.active.mode == 'OBJECT':
        scn.objects.active = nobj
    return nobj


def addImagePlane(camera, bimage, width, height, focal_length, name):
    global xrot
    # Create mesh for image plane:
    mesh = bpy.data.meshes.new(name)
    mesh.update()
    mesh.validate()
    w = camera.world
    plane_distance = 1.0 # Distance from camera position
    position = w.col[3]
    # Right vector in view frustum at plane_distance:
    right = Vector((1, 0, 0)) * (width / focal_length) * plane_distance
    # Up vector in view frustum at plane_distance:
    up = Vector((0, 1, 0)) * (height / focal_length) * plane_distance
    # Camera view direction:
    view_dir = -Vector((0, 0, 1)) * plane_distance
    plane_center = view_dir

    corners = ((-0.5, -0.5),
               (+0.5, -0.5),
               (+0.5, +0.5),
               (-0.5, +0.5))
    points = [(plane_center + c[0] * right + c[1] * up)[0:3] for c in corners]
    mesh.from_pydata(points, [], [[0, 1, 2, 3]])

    # Assign image to face of image plane:
    uvmap = mesh.uv_textures.new()
    face = uvmap.data[0]
    face.image = bimage

    # Add mesh to new image plane object:
    meshobj = add_obj(mesh, name)
    meshobj.matrix_world = xrot * w
    mesh.update()
    mesh.validate()
    return meshobj


#Rewrite this portion to handle camera addition using bpy.ops.object.camera_add()
def addCameratoCurrentScene():
    bpy.ops.object.camera_add(view_align=False, enter_editmode=False, location=(0, 0, 0), rotation=(0, 0, 0), layers=(False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))


def addToBlenderScene(bfr, scene_path):
    global xrot
    print("Adding point cloud...")
    name = "VSFM Point Cloud"
    number = int[0]
    while True:
        if bpy.data.meshes.find(name) != '-1':
            number += 1
            name = (name + ' ' + number)
        else:
            break
    mesh = bpy.data.meshes.new(name)
    mesh.update()
    mesh.validate()

    points = [point.position for point in bfr.points]
    mesh.from_pydata(points, [], [])
    meshobj = add_obj(mesh, name)
    meshobj.matrix_world = xrot


    # Adding cameras and image planes:

    # if option is set, add as an image sequence with a driver-based camera

    for index, camera in enumerate(bfr.cameras):

        # Load image:
        bimage = bpy.data.images.load(
            os.path.join(scene_path, camera.image_path))
        if addAsDriver:
            bpy.ops.sequencer.image_strip_add(directory="", files=[bimage], frame_start=index, frame_end=[index + 1])
            camera_name = 'VSFM Data'
            if camera_name is not in bpy.data.cameras:


        else
            camera_name = "Camera %d" % index
            bcamera = bpy.data.cameras.new(camera_name)
            bcamera.angle_x = math.atan(width / (camera.focal_length * 2.0)) * 2.0
            bcamera.angle_y = math.atan(height / (camera.focal_length * 2.0)) * 2.0
            cameraObj = add_obj(bcamera, camera_name)
            cameraObj.matrix_world = xrot * camera.world
        width, height = bimage.size




        # Add image frame:
            bpy.ops.sequencer.image_strip_add(directory="", files=[bimage], frame_start=index, frame_end=[index + 1])
        # Add image plane:
        planeObj = addImagePlane(camera, bimage, width, height,
                                 camera.focal_length, "Image Plane %d" % index)

        # Group image plane and camera:
        #Instead, add keyframe to driver
        group = bpy.data.groups.new("Camera Group %d" % index)
        group.objects.link(cameraObj)
        group.objects.link(planeObj)


def load(operator, context, filepath = ""):
    # Set the path to one directory above bundle.rd.out
    # VSFM dumps the undistorted images into a directory named 'data'
    scene_path = os.path.pardir()
    bfr = load_scene(scene_path)
    addToBlenderScene(bfr, scene_path)
    return {'FINISHED'}


class ImportBundler(bpy.types.Operator, ImportHelper):
    '''Load a Bundler scene'''
    bl_idname = "bundle.rd.out"
    bl_label = "Import VSFM Bundle"
    bl_options = {'UNDO'}

    files = CollectionProperty(name="File Path",
                          description="File path to bundle.out used for " +
                                      "importing the Bundler scene",
                          type=bpy.types.OperatorFileListElement)

    directory = StringProperty()

    filename_ext = ".rd.out"
    filter_glob = StringProperty(default="bundle.rd.out", options={'HIDDEN'})

    def execute(self, context):
        paths = [os.path.join(self.directory, name.name)
                 for name in self.files]
        if not paths:
            paths.append(self.filepath)

        for path in paths:
            load(self, context, path)

        return {'FINISHED'}




def menu_func_import(self, context):
    self.layout.operator(ImportBundler.bl_idname, text="VSFM Bundle (bundle.rd.out)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
    #load(None, None, 'scenes/hanau_images_800/bundle/bundle.out')

