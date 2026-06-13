#Librerias externas
from pyglet.graphics.shader import Shader, ShaderProgram
from pyglet.window import Window, key
from pyglet.gl import *
from pyglet.app import run
from pyglet import math
from pyglet import clock
from pyglet import text

import numpy as np #recordar que en general usamos numpy 2.3.5
import trimesh as tm

#Librerias Oficiales de Python
import sys, os
import math as mathPY

#Codigos del curso CC3501
from utils.helpers import init_pipeline, mesh_from_file, init_axis
from utils.camera import FreeCamera
from utils.scene_graph import SceneGraph
from utils.drawables import Texture, Model, DirectionalLight, Material
from utils import shapes

class Controller(Window):
    #hereda caracteristicas de pyglet.window.Window
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args,**kwargs)

        self.time = 0

        self.wireframe = False
        self.mouseLocked = True
        self.debug = False

class MyCam(FreeCamera):
    #hereda caracteristicas de utils.camera.FreeCamera
    def __init__(self, position=np.array([0,0,0]), camera_type="perspective", direction=np.array([0,0,0]), speed=2):
        super().__init__(position, camera_type)
        self.direction = direction
        self.speed = speed
    
    def time_update(self,dt):
        self.update() #metodo update() heredado de FreeCamera
        dir = self.direction[0]*self.forward + self.direction[1]*self.right
        dir_norm = np.linalg.norm(dir)
        if dir_norm:
            dir /= dir_norm
        self.position += dir*self.speed*dt
        self.focus = self.position + self.forward

def get_atlas_uv(xoff, yoff, atlas, resolution=16):
    dx = resolution / atlas.width
    dy = resolution / atlas.height
    return [
        dx*xoff         ,dy*yoff,
        dx*(xoff+1)     ,dy*yoff,
        dx*(xoff+1)     ,dy*(yoff+1),
        dx*xoff         ,dy*(yoff+1)
    ]

BLOCKS_UV = {
    "air": [],
    "grass": [(27, 20), (27, 20), (27, 20), (27, 20), (28, 18), (23, 23)]
}

class Block:
    def __init__(self, id,  texture_id="grass") -> None:
        self.id = id
        self.position = np.zeros(3)
        self.texture_id = texture_id

if __name__ == "__main__":
    #Crear la ventana
    controller = Controller(800,600, "CraftMine")
    controller.set_exclusive_mouse(controller.mouseLocked)

    #Contador de FPS para el Debug. Sacado de Aux10 del repo de auxiliares del curso
    fps_label = text.Label(
        text="FPS: 0.00",
        font_name="Arial",
        font_size=16,
        x=controller.width - 10,
        y=controller.height - 10,
        anchor_x="right",
        anchor_y="top",
        color=(255,255,255,255)
    )

    game_shaders = os.path.join(os.path.dirname(__file__), "game_shaders")
    pipeline = init_pipeline(game_shaders + "/blinn_phong.vert", game_shaders + "/blinn_phong.frag")

    assets_folder = os.path.join(os.path.dirname(__file__), "assets")
    atlas = Texture(assets_folder + "/atlas.png", minFilterMode=GL_NEAREST, maxFilterMode=GL_NEAREST)

    cam = MyCam([5,5,5])

    world = SceneGraph(cam)

    grass = [
        *get_atlas_uv(23,23,atlas),
        *get_atlas_uv(23,23,atlas),
        *get_atlas_uv(23,23,atlas),
        *get_atlas_uv(23,23,atlas),
        *get_atlas_uv(23,23,atlas),
        *get_atlas_uv(23,23,atlas)
    ]

    block_mesh = Model(shapes.Cube["position"], grass, index_data=shapes.Cube["indices"], normal_data=shapes.Cube["normal"])

    world.add_node("grass", mesh= block_mesh, texture=atlas, pipeline=pipeline, material=Material())

    world.add_node("sun", light=DirectionalLight(ambient=[0.2,0.2,0.2]), pipeline=pipeline, rotation=[-np.pi/4, -np.pi/4, 0])

    @controller.event
    def on_draw():
        controller.clear()

        glClearColor(0.2,0.2,0.2,1)
        glEnable(GL_DEPTH_TEST)

        if controller.wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        
        world.draw()
        glDisable(GL_DEPTH_TEST)

        if controller.debug:
            fps_label.draw()
    
    @controller.event
    def on_key_press(symbol, modifiers):
        if symbol == key.M:
            #Accion para poder recuperar el mouse y que no este anclado al programa (sin tener que cerrarlo o apretar la tecla Super para esto)
            controller.mouseLocked = not controller.mouseLocked
            controller.set_exclusive_mouse(controller.mouseLocked)
        
        if symbol == key.F3:
            #Activa/Desactiva el Debug
            controller.debug = not controller.debug
        
        if symbol == key.W:
            cam.direction[0] = 1
        if symbol == key.S:
            cam.direction[0] = -1
        if symbol == key.A:
            cam.direction[1] = 1
        if symbol == key.D:
            cam.direction[1] = -1

    @controller.event
    def on_key_release(symbol, modifiers):
        if symbol == key.W or symbol == key.S:
            cam.direction[0] = 0
        if symbol == key.A or symbol == key.D:
            cam.direction[1] = 0

    @controller.event
    def on_mouse_motion(x, y, dx, dy):
        cam.yaw += dx * 0.001
        cam.pitch += dy * 0.001
        cam.pitch = math.clamp(cam.pitch, -(np.pi / 2 - 0.01), np.pi / 2 - 0.01)

    def update(dt):
        world.update()
        cam.time_update(dt)

        controller.time += dt

        if controller.debug:
            fps = 1/dt if dt>0 else 0
            fps_label.text = f"FPS {fps:.2f}"

    clock.schedule_interval(update, 1/60)
    run()