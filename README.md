VSFMBundle_to_Blender
=====================

An attempt to create a script based on Konrad Koelzer's bundle import script that optimizes VSFM output for Blender

The original script expected a very specific directory structure and file names, 
and also imported the bundle in what I feel is an in-efficient format.  

The point cloud seems fine, but the original script wants to create a new camera and image plane
for every image that was originally referenced in VSFM.  

This approach takes up extreme amounts of memory and when using a large number of hi-res images (from VSFM), 
it can slow Blender to a crawl... not to mention the added drudgery of changing the active camera.

Goals
=====

1. Inspired by this tutorial: http://youtu.be/xjjW2yKjUDM my intent is to alter the script
    in order to import the referenced images as an image/movie sequence, 1 image per frame.
    
2. Instead of creating a seperate camera for each image, I intend to use one camera combined with drivers/keyframes
    for positioning, rotation, size, focal length, and possibly even lens distortion.
    
Advantages
==========

I see the workflow of this script as basically importing the data from a VSFM export (bundle.rd.out)
  as well as the images from the 'data' subdirectory without having to re-arrange anything.  
  The user could then cycle through the images using left and right on the keyboard in order to 'connect the dots'
  of the point-cloud and model any objects as they see fit.  
  
I've always found MeshLabs to be an obtuse intermediary with a very user-unfriendly interface, especially if
  a user (like me) is used to Blender.  Also, many times I've attempted to use Meshlabs to create an actual mesh, 
  the results have been less than staggering.  This is especially true for rooms and unsequenced imagery.
  
Caveats
=======

Unlike Meshlab, the current version of the bundle_importer script doesn't automatically texture anything or provide
  color data of any sort apart from the images themselves.  Perhaps this functionality could be added in the future
  however it is not what I'm focusing on at the moment.
  
I pine for the day when VSFM/Meshlab/Boujou and photogrammetry functionality is integrated into Blender (hell, if 
  my iPhone can do it with programs like Seene and 123DCatch, Why can't my computer???).
  But until then, my intent is simply to cut out the middle-man (Meshlab or the even more cumbersome Bundler or PPT)
  from the Blender photogrammetry workflow.
  
  
Any help would be much appreciated.
