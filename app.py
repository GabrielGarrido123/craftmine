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

        self.skyColor = np.array([0.2,0.55,0.85])
        self.WORLD_SIZE = 8

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

def get_atlas_uv(offsets, atlas, resolution=16):
    (xoff, yoff) = offsets
    dx = resolution / atlas.width
    dy = resolution / atlas.height
    return [
        dx*xoff         ,dy*yoff,
        dx*(xoff+1)     ,dy*yoff,
        dx*(xoff+1)     ,dy*(yoff+1),
        dx*xoff         ,dy*(yoff+1)
    ]

DEFAULT_MATERIALS = {
    "basic": Material(specular=[0.4,0.4,0.4]),
    "metal": Material(shininess=64)
}

BLOCKS_UV = {
    "air": [],
    "grass": [(27, 20), (27, 20), (27, 20), (27, 20), (28, 18), (23, 23)]
}

class Block:
    def __init__(self, id="air") -> None:
        self.id = id
        self.position = np.zeros(3)

class Chunk(Model):
    #La idea de crear una clase chunk, al igual que en el aux 10, es crear meshes que agrupen varios bloques, para asi optimizar el renderizado.
    #Esto significa que los chunks deben heredar metodos de utils.drawables.Model
    #Codigo sacado de aux 10, con leves modificaciones

    #tamaño del chunk, por cada eje
    COUNT = 16
    SIZE = 16
    def __init__(self, id, atlas):
        super().__init__([],[],[],[]) #informacion que se le da a Model
        self.index_data = []
        self.blocks = np.full((Chunk.COUNT, Chunk.COUNT, Chunk.COUNT), None, dtype=object) #forma, dato con el que rellenar, tipo de dato

        for y in range(Chunk.COUNT):
            for z in range(Chunk.COUNT):
                for x in range(Chunk.COUNT):
                    self.blocks[y][z][x] = Block("air") #rellenamos la matriz de bloques con aire (bloque invisible)
        
        self.atlas = atlas
        self.id = id
    
    #la clase (Chunk) modifica la funcion init_gpu_data de Model
    def init_gpu_data(self, pipeline):
        delta = Chunk.SIZE / Chunk.COUNT
        cube_pos = [(coord + 0.5)*delta for coord in shapes.Cube["position"]]
        cube_pos = np.reshape(cube_pos, (len(cube_pos) // 3, 3))
        deltaV = cube_pos.shape[0]
        vcount = 0

        #armado del mesh. Al modelo se le añaden los vertices de cada bloque del chunk (que si sea renderizado)
        for y in range(Chunk.COUNT):
            for z in range(Chunk.COUNT):
                for x in range(Chunk.COUNT):
                    block = self.blocks[y][z][x]
                    block.position = np.array([x * delta, y * delta, z * delta])

                    if block.id == "air":
                        #se skippea el bloque de aire, o bloque vacio.
                        continue
                    
                    for p in cube_pos:
                        self.position_data.extend(p + block.position)
                    
                    for uv in BLOCKS_UV[block.id]:
                        self.uv_data.extend(get_atlas_uv(uv, self.atlas))
                    
                    self.normal_data.extend(shapes.Cube["normal"])
                    self.index_data.extend([vcount + i for i in shapes.Cube["indices"]])
                    vcount += deltaV
        
        #se ejecuta el resto de la funcion init_gpu_data() de Model
        super().init_gpu_data(pipeline)


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

    #Para mostrar la posicion en el espacio. Tambien es del Debug
    pos_label = text.Label(
        text="XYZ: 0.00, 0.00, 0.00",
        font_name="Arial",
        font_size=16,
        x=10,
        y=controller.height - 10,
        anchor_x="left",
        anchor_y="top",
        color=(255,255,255,255)
    )

    game_shaders = os.path.join(os.path.dirname(__file__), "game_shaders")
    pipeline = init_pipeline(game_shaders + "/blinn_phong.vert", game_shaders + "/blinn_phong.frag")

    assets_folder = os.path.join(os.path.dirname(__file__), "assets")
    atlas = Texture(assets_folder + "/atlas.png", minFilterMode=GL_NEAREST, maxFilterMode=GL_NEAREST)

    cam = MyCam([0,5,0])

    world = SceneGraph(cam)

    #GENERACION DE MUNDO
    chunks=[]
    for z in range(controller.WORLD_SIZE):
        for x in range(controller.WORLD_SIZE):
            (posX,posZ) = (x-controller.WORLD_SIZE//2,z-controller.WORLD_SIZE//2)
            chunks.append(Chunk((posX,posZ),atlas))
    
    for c in chunks:
        for z in range(Chunk.COUNT):
            for x in range(Chunk.COUNT):
                c.blocks[0][z][x] = Block("grass")
        
        #agregamos el chunk al grafo de escena
        world.add_node(
            name=f"chunk{c.id[0]},{c.id[1]}",
            mesh=c,
            pipeline=pipeline,
            material=DEFAULT_MATERIALS["basic"],
            texture=c.atlas,
            position=[c.id[0]*Chunk.SIZE,0,c.id[1]*Chunk.SIZE]
            )

    world.add_node("sun", light=DirectionalLight(ambient=[0.2,0.2,0.2]), pipeline=pipeline, rotation=[-np.pi/4, -np.pi/4, 0])

    @controller.event
    def on_draw():
        controller.clear()

        glClearColor(*controller.skyColor,1)
        glEnable(GL_DEPTH_TEST)

        if controller.wireframe:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        
        world.draw()
        glDisable(GL_DEPTH_TEST)

        #Renderizar UI
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        if controller.debug:
            fps_label.draw()
            pos_label.draw()
    
    @controller.event
    def on_key_press(symbol, modifiers):
        if symbol == key.M:
            #Accion para poder recuperar el mouse y que no este anclado al programa (sin tener que cerrarlo o apretar la tecla Super para esto)
            controller.mouseLocked = not controller.mouseLocked
            controller.set_exclusive_mouse(controller.mouseLocked)
        
        if symbol == key.F3:
            #Activa/Desactiva el Debug
            controller.debug = not controller.debug

        if symbol == key.F5:
            #Activa/desactiva el Wireframe
            controller.wireframe = not controller.wireframe
        
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
            fps_label.text = f"FPS: {fps:.2f}"

            pos = cam.position
            pos_label.text = f"XYZ: {pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}"

    clock.schedule_interval(update, 1/600)
    run()