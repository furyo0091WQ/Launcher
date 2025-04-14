import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import os
import sys
import threading
import time
import json
import webbrowser
import random
import subprocess
import urllib.request
import urllib.parse
import re
import shutil
import ssl
from PIL import Image, ImageTk
from io import BytesIO
from datetime import datetime

# Configuración de CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Constantes - Rutas específicas
LAUNCHER_DIR = r"C:\Users\furyo\AppData\Roaming\.LauncherClient"
INSTANCES_DIR = os.path.join(LAUNCHER_DIR, "versions")  # Cambiado de "instances" a "versions"
ASSETS_DIR = os.path.join(LAUNCHER_DIR, "assets")
VERSIONS_DIR = os.path.join(LAUNCHER_DIR, "versions")  # Cambiado para usar la ruta directa
ACCOUNTS_FILE = os.path.join(LAUNCHER_DIR, "accounts.json")
CONFIG_FILE = os.path.join(LAUNCHER_DIR, "config.json")
MINECRAFT_VERSIONS_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

# Asegurar que los directorios existan
for directory in [LAUNCHER_DIR, INSTANCES_DIR, ASSETS_DIR, VERSIONS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Clase principal del launcher
class MinecraftLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana
        self.title("Minecraft Launcher")
        self.geometry("1000x700")
        self.minsize(900, 600)
        
        # Cargar configuración
        self.config = self.load_config()
        self.accounts = self.load_accounts()
        self.minecraft_versions = []
        self.version_images = {}
        
        # Descargar versiones de Minecraft en un hilo separado
        threading.Thread(target=self.fetch_minecraft_versions, daemon=True).start()
        
        # Descargar imágenes para versiones
        threading.Thread(target=self.download_version_images, daemon=True).start()
        
        # Crear la interfaz
        self.create_main_layout()
        
        # Establecer fondo
        self.set_background()
    
    def load_config(self):
        # Cargar configuración o crear una por defecto
        default_config = {
            "java_path": self.find_java_path(),
            "min_memory": 2,
            "max_memory": 4,
            "theme": "dark",
            "last_selected_instance": "",
            "instances": [
                {"name": "Adelina 1.20.2", "version": "1.20.2", "loader": "Fabric", "last_played": "2024-04-07"},
                {"name": "Instance 2", "version": "1.19.4", "loader": "Vanilla", "last_played": "2024-03-15"},
                {"name": "Instance 3", "version": "1.18.2", "loader": "Forge", "last_played": "2024-02-20"},
                {"name": "Instance 4", "version": "1.20.2", "loader": "Quilt", "last_played": "2024-01-10"}
            ]
        }
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return default_config
        else:
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config=None):
        # Guardar configuración
        if config is None:
            config = self.config
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_accounts(self):
        # Cargar cuentas o crear una lista vacía
        default_accounts = [
            {"username": "Adela", "uuid": "00000000-0000-0000-0000-000000000000", "type": "DEMO"},
            {"username": "Adela", "uuid": "00000000-0000-0000-0000-000000000001", "type": "DEMO"}
        ]
        
        if os.path.exists(ACCOUNTS_FILE):
            try:
                with open(ACCOUNTS_FILE, 'r') as f:
                    return json.load(f)
            except:
                return default_accounts
        else:
            with open(ACCOUNTS_FILE, 'w') as f:
                json.dump(default_accounts, f, indent=2)
            return default_accounts
    
    def find_java_path(self):
        # Intentar encontrar la ruta de Java
        if sys.platform == "win32":
            # Buscar en Program Files
            java_dirs = [
                os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "Java"),
                os.path.join(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"), "Java")
            ]
            
            for java_dir in java_dirs:
                if os.path.exists(java_dir):
                    for root, dirs, files in os.walk(java_dir):
                        if "java.exe" in files:
                            return os.path.join(root, "java.exe")
            
            # Buscar en PATH
            for path in os.environ.get("PATH", "").split(os.pathsep):
                java_exe = os.path.join(path, "java.exe")
                if os.path.exists(java_exe):
                    return java_exe
        else:
            # Linux/Mac
            try:
                return subprocess.check_output(["which", "java"]).decode().strip()
            except:
                pass
        
        # Valor por defecto
        return "java"
    
    def set_background(self):
        # Establecer un fondo para la aplicación
        try:
            # Crear un fondo azul oscuro con degradado
            self.configure(fg_color="#0A0E14")
        except Exception as e:
            print(f"Error al establecer fondo: {e}")
    
    def fetch_minecraft_versions(self):
        # Descargar lista de versiones de Minecraft
        try:
            # Crear un contexto SSL que no verifique certificados
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(MINECRAFT_VERSIONS_URL, context=ctx) as response:
                data = json.loads(response.read().decode())
                self.minecraft_versions = data["versions"]
                print(f"Descargadas {len(self.minecraft_versions)} versiones de Minecraft")
                
                # Guardar versiones en un archivo
                with open(os.path.join(ASSETS_DIR, "versions.json"), 'w') as f:
                    json.dump(self.minecraft_versions, f, indent=2)
                
                # Actualizar UI si ya está creada
                if hasattr(self, 'instances_frame'):
                    self.after(100, self.refresh_instances)
        except Exception as e:
            print(f"Error al descargar versiones de Minecraft: {e}")
    
    def download_version_images(self):
        # Descargar imágenes para las versiones de Minecraft
        version_images = {
            "1.20": "https://static.wikia.nocookie.net/minecraft_gamepedia/images/c/c1/Trails_%26_Tales_Key_Art.jpg",
            "1.19": "https://static.wikia.nocookie.net/minecraft_gamepedia/images/d/d3/The_Wild_Update_Key_Art.jpg",
            "1.18": "https://static.wikia.nocookie.net/minecraft_gamepedia/images/0/0e/Caves_%26_Cliffs_Update_Key_Art.jpg",
            "1.17": "https://static.wikia.nocookie.net/minecraft_gamepedia/images/0/0e/Caves_%26_Cliffs_Update_Key_Art.jpg",
            "1.16": "https://static.wikia.nocookie.net/minecraft_gamepedia/images/9/9d/Nether_Update_Key_Art.jpg",
            "default": "https://www.minecraft.net/content/dam/games/minecraft/key-art/MC_The-Wild-Update_1170x500.jpg"
        }
        
        # Crear directorio para imágenes de versiones si no existe
        version_images_dir = os.path.join(VERSIONS_DIR, "images")
        if not os.path.exists(version_images_dir):
            os.makedirs(version_images_dir)
        
        # Crear un contexto SSL que no verifique certificados
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # Descargar cada imagen
        for version, url in self.version_images.items():
            img_path = self.download_image(url, version)

            # If downloading fails, fall back to a local image
            if img_path is None:
                fallback_path = os.path.join(self.assets_dir, "backgrounds", "background.jpg")
                if os.path.exists(fallback_path):
                    img_path = fallback_path
                    print(f"Usando imagen de respaldo para versión {version}")

            # Load image into memory (assuming `self.version_images` is a dict of version -> image path)
            self.version_images[version] = img_path
        
        # Actualizar UI si ya está creada
        if hasattr(self, 'instances_frame'):
            self.after(100, self.refresh_instances)
    
    def get_version_image(self, version):
        # Obtener imagen para una versión específica
        for ver_prefix, img_path in self.version_images.items():
            if version.startswith(ver_prefix):
                return img_path
        
        # Si no se encuentra, usar la imagen por defecto
        return self.version_images.get("default", "")
    
    def create_main_layout(self):
        # Crear el layout principal con pestañas
        
        # Barra lateral
        self.sidebar = ctk.CTkFrame(self, width=60, corner_radius=0, fg_color="#0A0E14")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(20, 30))
        logo_label = ctk.CTkLabel(logo_frame, text="M", font=ctk.CTkFont(size=24, weight="bold"), 
                                 text_color="#3080FF")
        logo_label.pack()
        
        # Botones de navegación
        self.nav_buttons = []
        
        # Instancias
        self.instances_btn = self.create_sidebar_button("Instances", "instances", 0)
        
        # Consola
        self.console_btn = self.create_sidebar_button("Console", "console", 1)
        
        # Cuentas
        self.accounts_btn = self.create_sidebar_button("Accounts", "accounts", 2)
        
        # Mods
        self.mods_btn = self.create_sidebar_button("Mods", "mods", 3)
        
        # Paquetes de recursos
        self.packs_btn = self.create_sidebar_button("Packs", "packs", 4)
        
        # Mundos
        self.worlds_btn = self.create_sidebar_button("Worlds", "worlds", 5)
        
        # Ajustes
        self.settings_btn = self.create_sidebar_button("Settings", "settings", 6)
        
        # Marco principal para las pestañas
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#1A1A1A")
        self.main_frame.pack(side="right", fill="both", expand=True)
        
        # Crear frames para cada pestaña
        self.frames = {}
        self.frames["instances"] = self.create_instances_frame()
        self.frames["console"] = self.create_console_frame()
        self.frames["accounts"] = self.create_accounts_frame()
        self.frames["mods"] = self.create_mods_frame()
        self.frames["packs"] = self.create_packs_frame()
        self.frames["worlds"] = self.create_worlds_frame()
        self.frames["settings"] = self.create_settings_frame()
        
        # Mostrar la pestaña de instancias por defecto
        self.show_frame("instances")
    
    def create_sidebar_button(self, text, frame_name, index):
        btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        btn = ctk.CTkButton(
            btn_frame, 
            text="", 
            width=40, 
            height=40,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#333333",
            command=lambda name=frame_name: self.show_frame(name)
        )
        btn.pack()
        
        label = ctk.CTkLabel(btn_frame, text=text, font=("Arial", 10), text_color="#CCCCCC")
        label.pack(pady=(5, 0))
        
        self.nav_buttons.append((btn, frame_name))
        return btn
    
    def show_frame(self, frame_name):
        # Mostrar el frame seleccionado y ocultar los demás
        for name, frame in self.frames.items():
            if name == frame_name:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        
        # Actualizar botones de navegación
        for btn, name in self.nav_buttons:
            if name == frame_name:
                btn.configure(fg_color="#444444")
            else:
                btn.configure(fg_color="transparent")
    
    def create_instances_frame(self):
        # Frame para las instancias de Minecraft
        frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="#1A1A1A")
        
        # Barra superior
        top_bar = ctk.CTkFrame(frame, height=50, corner_radius=0, fg_color="#1A1A1A")
        top_bar.pack(fill="x")
        
        # Título
        title = ctk.CTkLabel(top_bar, text="Instances", font=ctk.CTkFont(size=16, weight="bold"), 
                            text_color="#CCCCCC")
        title.pack(side="left", padx=20)
        
        # Botones de acción
        add_instance_btn = ctk.CTkButton(
            top_bar, 
            text="+ Create Instance", 
            width=120,
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444",
            command=self.create_new_instance
        )
        add_instance_btn.pack(side="left", padx=10)
        
        create_group_btn = ctk.CTkButton(
            top_bar, 
            text="+ Create Group", 
            width=120,
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444"
        )
        create_group_btn.pack(side="left", padx=10)
        
        # Contenido principal
        content = ctk.CTkFrame(frame, fg_color="#1A1A1A")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Grupo de instancias
        group_frame = ctk.CTkFrame(content, fg_color="#1A1A1A")
        group_frame.pack(fill="x")
        
        group_header = ctk.CTkFrame(group_frame, height=30, fg_color="#252525")
        group_header.pack(fill="x")
        
        group_label = ctk.CTkLabel(group_header, text="Group 1 ▼", text_color="#CCCCCC")
        group_label.pack(side="left", padx=15)
        
        # Contenedor para las instancias
        self.instances_container = ctk.CTkScrollableFrame(group_frame, fg_color="#1A1A1A")
        self.instances_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Grid para las instancias
        self.instances_grid = ctk.CTkFrame(self.instances_container, fg_color="#1A1A1A")
        self.instances_grid.pack(fill="both", expand=True)
        
        # Cargar instancias
        self.refresh_instances()
        
        return frame
    
    def refresh_instances(self):
        # Limpiar grid de instancias
        for widget in self.instances_grid.winfo_children():
            widget.destroy()
        
        # Configurar grid
        self.instances_grid.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Cargar instancias desde la configuración
        instances = self.config.get("instances", [])
        
        # Mostrar instancias
        for i, instance in enumerate(instances):
            row = i // 3
            col = i % 3
            self.create_instance_card(
                self.instances_grid, 
                instance["name"], 
                instance["version"], 
                instance["loader"],
                row, 
                col
            )
    
    def create_instance_card(self, parent, name, version, loader, row, col):
        # Crear tarjeta para una instancia
        card = ctk.CTkFrame(parent, width=150, height=150, fg_color="#1A1A1A")
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        card.grid_propagate(False)
        
        # Obtener imagen para la versión
        img_path = self.get_version_image(version)
        
        if img_path and os.path.exists(img_path):
            try:
                # Cargar imagen y redimensionar
                img = Image.open(img_path)
                img = img.resize((150, 150), Image.LANCZOS)
                
                # Oscurecer la imagen para mejorar la legibilidad
                overlay = Image.new('RGBA', img.size, (0, 0, 0, 128))
                img = Image.alpha_composite(img.convert('RGBA'), overlay)
                
                # Convertir a PhotoImage
                photo = ImageTk.PhotoImage(img)
                
                # Crear canvas para la imagen
                canvas = tk.Canvas(card, width=150, height=150, highlightthickness=0, bg="#222222")
                canvas.place(x=0, y=0)
                canvas.create_image(0, 0, image=photo, anchor="nw")
                
                # Guardar referencia para evitar que el recolector de basura la elimine
                canvas.image = photo
            except Exception as e:
                print(f"Error al cargar imagen para {name}: {e}")
                # Si hay error, usar el fondo de ajedrez
                self.create_checkered_background(card)
        else:
            # Si no hay imagen, usar el fondo de ajedrez
            self.create_checkered_background(card)
        
        # Nombre de la instancia
        name_label = ctk.CTkLabel(card, text=name, bg_color="#000000", fg_color="#000000", 
                                 text_color="white", corner_radius=0)
        name_label.place(relx=0.5, rely=0.9, anchor="center")
        
        # Versión y loader (pequeño texto en la esquina)
        version_label = ctk.CTkLabel(card, text=f"{version} - {loader}", bg_color="#000000", 
                                    fg_color="#000000", text_color="#AAAAAA", 
                                    corner_radius=0, font=("Arial", 9))
        version_label.place(relx=0.5, rely=0.8, anchor="center")
        
        # Hacer que la tarjeta sea clickeable
        card.bind("<Button-1>", lambda e, n=name: self.select_instance(n))
        
        # Menú contextual
        card.bind("<Button-3>", lambda e, n=name: self.show_instance_context_menu(e, n))
        
        return card
    
    def create_checkered_background(self, parent):
        # Crear fondo de ajedrez para las tarjetas de instancias
        checker = ctk.CTkCanvas(parent, width=150, height=150, highlightthickness=0, bg="#222222")
        checker.place(x=0, y=0)
        
        # Dibujar patrón de ajedrez
        size = 25
        for i in range(6):
            for j in range(6):
                if (i + j) % 2 == 0:
                    color = "#000000"
                else:
                    color = "#555555"
                checker.create_rectangle(i*size, j*size, (i+1)*size, (j+1)*size, fill=color, outline="")
    
    def show_instance_context_menu(self, event, instance_name):
        # Mostrar menú contextual para una instancia
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="Launch", command=lambda: self.launch_instance(instance_name))
        context_menu.add_command(label="Edit", command=lambda: self.edit_instance(instance_name))
        context_menu.add_separator()
        context_menu.add_command(label="Delete", command=lambda: self.delete_instance(instance_name))
        
        # Mostrar menú en la posición del clic
        context_menu.tk_popup(event.x_root, event.y_root)
    
    def select_instance(self, instance_name):
        # Seleccionar instancia
        self.config["last_selected_instance"] = instance_name
        self.save_config()
        
        # Lanzar instancia
        self.launch_instance(instance_name)
    
    def create_new_instance(self):
        # Crear una nueva ventana para crear instancia
        create_window = ctk.CTkToplevel(self)
        create_window.title("Create New Instance")
        create_window.geometry("500x400")
        create_window.resizable(False, False)
        create_window.grab_set()  # Modal
        
        # Formulario
        form_frame = ctk.CTkFrame(create_window, fg_color="#1A1A1A")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Nombre
        name_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        
        name_label = ctk.CTkLabel(name_frame, text="Instance Name:", text_color="#CCCCCC")
        name_label.pack(side="left", padx=10)
        
        name_entry = ctk.CTkEntry(name_frame, width=300, fg_color="#333333", text_color="#FFFFFF")
        name_entry.pack(side="left", padx=10)
        name_entry.insert(0, f"Instance {len(self.config.get('instances', [])) + 1}")
        
        # Versión
        version_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        version_frame.pack(fill="x", pady=10)
        
        version_label = ctk.CTkLabel(version_frame, text="Minecraft Version:", text_color="#CCCCCC")
        version_label.pack(side="left", padx=10)
        
        # Obtener versiones disponibles
        versions = ["1.20.2", "1.19.4", "1.18.2", "1.17.1", "1.16.5"]
        if self.minecraft_versions:
            versions = [v["id"] for v in self.minecraft_versions[:10]]  # Mostrar las 10 más recientes
        
        version_var = ctk.StringVar(value=versions[0])
        version_dropdown = ctk.CTkOptionMenu(
            version_frame, 
            values=versions, 
            variable=version_var,
            fg_color="#333333",
            button_color="#444444",
            button_hover_color="#555555",
            dropdown_fg_color="#333333",
            dropdown_hover_color="#444444",
            text_color="#FFFFFF"
        )
        version_dropdown.pack(side="left", padx=10)
        
        # Loader (Fabric, Forge, etc.)
        loader_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        loader_frame.pack(fill="x", pady=10)
        
        loader_label = ctk.CTkLabel(loader_frame, text="Mod Loader:", text_color="#CCCCCC")
        loader_label.pack(side="left", padx=10)
        
        loader_var = ctk.StringVar(value="Vanilla")
        loader_dropdown = ctk.CTkOptionMenu(
            loader_frame, 
            values=["Vanilla", "Fabric", "Forge", "Quilt"], 
            variable=loader_var,
            fg_color="#333333",
            button_color="#444444",
            button_hover_color="#555555",
            dropdown_fg_color="#333333",
            dropdown_hover_color="#444444",
            text_color="#FFFFFF"
        )
        loader_dropdown.pack(side="left", padx=10)
        
        # Memoria
        memory_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        memory_frame.pack(fill="x", pady=10)
        
        memory_label = ctk.CTkLabel(memory_frame, text="Memory (GB):", text_color="#CCCCCC")
        memory_label.pack(side="left", padx=10)
        
        memory_min_label = ctk.CTkLabel(memory_frame, text="Min:", text_color="#CCCCCC")
        memory_min_label.pack(side="left", padx=10)
        
        memory_min = ctk.CTkEntry(memory_frame, width=60, fg_color="#333333", text_color="#FFFFFF")
        memory_min.pack(side="left", padx=5)
        memory_min.insert(0, str(self.config.get("min_memory", 2)))
        
        memory_max_label = ctk.CTkLabel(memory_frame, text="Max:", text_color="#CCCCCC")
        memory_max_label.pack(side="left", padx=10)
        
        memory_max = ctk.CTkEntry(memory_frame, width=60, fg_color="#333333", text_color="#FFFFFF")
        memory_max.pack(side="left", padx=5)
        memory_max.insert(0, str(self.config.get("max_memory", 4)))
        
        # Botones
        buttons_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=20)
        
        create_btn = ctk.CTkButton(
            buttons_frame, 
            text="Create", 
            width=120,
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444",
            command=lambda: self.add_instance(
                name_entry.get(),
                version_var.get(),
                loader_var.get(),
                int(memory_min.get()),
                int(memory_max.get()),
                create_window
            )
        )
        create_btn.pack(side="right", padx=10)
        
        cancel_btn = ctk.CTkButton(
            buttons_frame, 
            text="Cancel", 
            width=120, 
            height=30,
            corner_radius=3,
            fg_color="#555555",
            hover_color="#666666",
            command=create_window.destroy
        )
        cancel_btn.pack(side="right", padx=10)
    
    def add_instance(self, name, version, loader, min_memory, max_memory, window):
        # Validar datos
        if not name:
            messagebox.showerror("Error", "Instance name cannot be empty", parent=window)
            return
        
        # Crear directorio para la instancia
        instance_dir = os.path.join(INSTANCES_DIR, name)
        if os.path.exists(instance_dir):
            messagebox.showerror("Error", f"Instance '{name}' already exists", parent=window)
            return
        
        os.makedirs(instance_dir)
        
        # Crear archivo de configuración para la instancia
        instance_config = {
            "name": name,
            "version": version,
            "loader": loader,
            "min_memory": min_memory,
            "max_memory": max_memory,
            "created_at": datetime.now().isoformat(),
            "last_played": None
        }
        
        with open(os.path.join(instance_dir, "instance.json"), 'w') as f:
            json.dump(instance_config, f, indent=2)
        
        # Actualizar configuración global
        instances = self.config.get("instances", [])
        instances.append(instance_config)
        self.config["instances"] = instances
        self.save_config()
        
        # Actualizar UI
        self.refresh_instances()
        
        # Cerrar ventana
        window.destroy()
        
        # Mostrar mensaje
        messagebox.showinfo("Success", f"Instance '{name}' created successfully")
    
    def edit_instance(self, instance_name):
        # Buscar instancia
        instances = self.config.get("instances", [])
        instance = next((i for i in instances if i["name"] == instance_name), None)
        
        if not instance:
            messagebox.showerror("Error", f"Instance '{instance_name}' not found")
            return
        
        # Crear ventana de edición (similar a create_new_instance)
        edit_window = ctk.CTkToplevel(self)
        edit_window.title(f"Edit Instance: {instance_name}")
        edit_window.geometry("500x400")
        edit_window.resizable(False, False)
        edit_window.grab_set()  # Modal
        
        # Formulario
        form_frame = ctk.CTkFrame(edit_window, fg_color="#1A1A1A")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Nombre
        form_frame = ctk.CTkFrame(edit_window, fg_color="#1A1A1A")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Nombre
        name_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        
        name_label = ctk.CTkLabel(name_frame, text="Instance Name:", text_color="#CCCCCC")
        name_label.pack(side="left", padx=10)
        
        name_entry = ctk.CTkEntry(name_frame, width=300, fg_color="#333333", text_color="#FFFFFF")
        name_entry.pack(side="left", padx=10)
        name_entry.insert(0, instance["name"])
        
        # Versión (solo mostrar, no editar)
        version_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        version_frame.pack(fill="x", pady=10)
        
        version_label = ctk.CTkLabel(version_frame, text="Minecraft Version:", text_color="#CCCCCC")
        version_label.pack(side="left", padx=10)
        
        version_value = ctk.CTkLabel(version_frame, text=instance["version"], text_color="#FFFFFF")
        version_value.pack(side="left", padx=10)
        
        # Loader (solo mostrar, no editar)
        loader_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        loader_frame.pack(fill="x", pady=10)
        
        loader_label = ctk.CTkLabel(loader_frame, text="Mod Loader:", text_color="#CCCCCC")
        loader_label.pack(side="left", padx=10)
        
        loader_value = ctk.CTkLabel(loader_frame, text=instance["loader"], text_color="#FFFFFF")
        loader_value.pack(side="left", padx=10)
        
        # Memoria
        memory_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        memory_frame.pack(fill="x", pady=10)
        
        memory_label = ctk.CTkLabel(memory_frame, text="Memory (GB):", text_color="#CCCCCC")
        memory_label.pack(side="left", padx=10)
        
        memory_min_label = ctk.CTkLabel(memory_frame, text="Min:", text_color="#CCCCCC")
        memory_min_label.pack(side="left", padx=10)
        
        memory_min = ctk.CTkEntry(memory_frame, width=60, fg_color="#333333", text_color="#FFFFFF")
        memory_min.pack(side="left", padx=5)
        memory_min.insert(0, str(instance.get("min_memory", 2)))
        
        memory_max_label = ctk.CTkLabel(memory_frame, text="Max:", text_color="#CCCCCC")
        memory_max_label.pack(side="left", padx=10)
        
        memory_max = ctk.CTkEntry(memory_frame, width=60, fg_color="#333333", text_color="#FFFFFF")
        memory_max.pack(side="left", padx=5)
        memory_max.insert(0, str(instance.get("max_memory", 4)))
        
        # Botones
        buttons_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=20)
        
        save_btn = ctk.CTkButton(
            buttons_frame, 
            text="Save", 
            width=120,
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444",
            command=lambda: self.update_instance(
                instance_name,
                name_entry.get(),
                int(memory_min.get()),
                int(memory_max.get()),
                edit_window
            )
        )
        save_btn.pack(side="right", padx=10)
        
        cancel_btn = ctk.CTkButton(
            buttons_frame, 
            text="Cancel", 
            width=120, 
            height=30,
            corner_radius=3,
            fg_color="#555555",
            hover_color="#666666",
            command=edit_window.destroy
        )
        cancel_btn.pack(side="right", padx=10)
    
    def update_instance(self, old_name, new_name, min_memory, max_memory, window):
        # Validar datos
        if not new_name:
            messagebox.showerror("Error", "Instance name cannot be empty", parent=window)
            return
        
        # Actualizar configuración
        instances = self.config.get("instances", [])
        for i, instance in enumerate(instances):
            if instance["name"] == old_name:
                # Actualizar valores
                instances[i]["name"] = new_name
                instances[i]["min_memory"] = min_memory
                instances[i]["max_memory"] = max_memory
                
                # Renombrar directorio si el nombre cambió
                if old_name != new_name:
                    old_dir = os.path.join(INSTANCES_DIR, old_name)
                    new_dir = os.path.join(INSTANCES_DIR, new_name)
                    if os.path.exists(old_dir):
                        os.rename(old_dir, new_dir)
                
                # Actualizar archivo de configuración de la instancia
                instance_config_path = os.path.join(INSTANCES_DIR, new_name, "instance.json")
                if os.path.exists(instance_config_path):
                    with open(instance_config_path, 'r') as f:
                        instance_config = json.load(f)
                    
                    instance_config["name"] = new_name
                    instance_config["min_memory"] = min_memory
                    instance_config["max_memory"] = max_memory
                    
                    with open(instance_config_path, 'w') as f:
                        json.dump(instance_config, f, indent=2)
                
                break
        
        # Guardar configuración global
        self.config["instances"] = instances
        self.save_config()
        
        # Actualizar UI
        self.refresh_instances()
        
        # Cerrar ventana
        window.destroy()
        
        # Mostrar mensaje
        messagebox.showinfo("Success", f"Instance '{new_name}' updated successfully")
    
    def delete_instance(self, instance_name):
        # Confirmar eliminación
        if not messagebox.askyesno("Confirm", f"Are you sure you want to delete instance '{instance_name}'?"):
            return
        
        # Eliminar directorio
        instance_dir = os.path.join(INSTANCES_DIR, instance_name)
        if os.path.exists(instance_dir):
            try:
                shutil.rmtree(instance_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete instance directory: {e}")
                return
        
        # Actualizar configuración
        instances = self.config.get("instances", [])
        self.config["instances"] = [i for i in instances if i["name"] != instance_name]
        self.save_config()
        
        # Actualizar UI
        self.refresh_instances()
        
        # Mostrar mensaje
        messagebox.showinfo("Success", f"Instance '{instance_name}' deleted successfully")
    
    def create_console_frame(self):
        # Frame para la consola
        frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="#1A1A1A")
        
        # Barra superior
        top_bar = ctk.CTkFrame(frame, height=50, corner_radius=0, fg_color="#1A1A1A")
        top_bar.pack(fill="x")
        
        # Botón de Back
        back_btn = ctk.CTkButton(
            top_bar, 
            text="Back", 
            width=60, 
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444",
            command=lambda: self.show_frame("instances")
        )
        back_btn.pack(side="left", padx=10)
        
        # Título
        self.console_title = ctk.CTkLabel(top_bar, text="Console", font=ctk.CTkFont(size=16, weight="bold"), 
                                        text_color="#CCCCCC")
        self.console_title.pack(side="left", padx=10)
        
        # Botón Kill
        self.kill_btn = ctk.CTkButton(
            top_bar, 
            text="Kill", 
            width=60, 
            height=30,
            corner_radius=3,
            fg_color="#FF5555",
            hover_color="#FF7777",
            command=self.kill_minecraft
        )
        self.kill_btn.pack(side="right", padx=10)
        self.kill_btn.configure(state="disabled")
        
        # Subtítulo
        self.subtitle_frame = ctk.CTkFrame(frame, height=30, corner_radius=0, fg_color="#252525")
        self.subtitle_frame.pack(fill="x")
        
        self.console_subtitle = ctk.CTkLabel(self.subtitle_frame, text="No instance running", 
                                           text_color="#CCCCCC")
        self.console_subtitle.pack(side="left", padx=20)
        
        # Consola
        console_frame = ctk.CTkFrame(frame, fg_color="#000000")
        console_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Área de texto para la consola
        self.console_text = ctk.CTkTextbox(console_frame, font=("Courier New", 11), fg_color="#000000", 
                                         text_color="#CCCCCC", border_width=0)
        self.console_text.pack(fill="both", expand=True)
        
        return frame
    
    def create_accounts_frame(self):
        # Frame para las cuentas
        frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="#1A1A1A")
        
        # Barra superior
        top_bar = ctk.CTkFrame(frame, height=50, corner_radius=0, fg_color="#1A1A1A")
        top_bar.pack(fill="x")
        
        # Título
        title = ctk.CTkLabel(top_bar, text="Accounts", font=ctk.CTkFont(size=16, weight="bold"), 
                            text_color="#CCCCCC")
        title.pack(side="left", padx=20)
        
        # Botones de acción
        add_account_btn = ctk.CTkButton(
            top_bar, 
            text="+ Add Account", 
            width=120,
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444",
            command=self.add_account_dialog
        )
        add_account_btn.pack(side="left", padx=10)
        
        login_demo_btn = ctk.CTkButton(
            top_bar, 
            text="Login Demo", 
            width=120,
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444"
        )
        login_demo_btn.pack(side="left", padx=10)
        
        play_offline_btn = ctk.CTkButton(
            top_bar, 
            text="Play Offline", 
            width=120,
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444"
        )
        play_offline_btn.pack(side="left", padx=10)
        
        # Tabla de cuentas
        table_frame = ctk.CTkFrame(frame, fg_color="#1A1A1A")
        table_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Encabezados de la tabla
        headers_frame = ctk.CTkFrame(table_frame, height=30, fg_color="#252525")
        headers_frame.pack(fill="x")
        
        # Configurar columnas
        headers_frame.grid_columnconfigure(0, weight=1)
        headers_frame.grid_columnconfigure(1, weight=2)
        headers_frame.grid_columnconfigure(2, weight=3)
        
        # Encabezados
        ctk.CTkLabel(headers_frame, text="Icon", text_color="#CCCCCC").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(headers_frame, text="Display Name", text_color="#CCCCCC").grid(row=0, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(headers_frame, text="UUID", text_color="#CCCCCC").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        
        # Contenido de la tabla
        self.accounts_content_frame = ctk.CTkFrame(table_frame, fg_color="#1A1A1A")
        self.accounts_content_frame.pack(fill="both", expand=True)
        
        # Configurar columnas
        self.accounts_content_frame.grid_columnconfigure(0, weight=1)
        self.accounts_content_frame.grid_columnconfigure(1, weight=2)
        self.accounts_content_frame.grid_columnconfigure(2, weight=3)
        
        # Cargar cuentas
        self.load_account_rows()
        
        return frame
    
    def load_account_rows(self):
        # Limpiar tabla
        for widget in self.accounts_content_frame.winfo_children():
            widget.destroy()
        
        # Cargar cuentas
        for i, account in enumerate(self.accounts):
            self.add_account_row(self.accounts_content_frame, i, account["username"], account.get("uuid", "N/A"))
    
    def add_account_row(self, parent, row, username, uuid):
        # Crear fila para una cuenta
        row_frame = ctk.CTkFrame(parent, height=50, fg_color="#222222")
        row_frame.grid(row=row, column=0, columnspan=3, sticky="ew", pady=1)
        
        # Configurar columnas
        row_frame.grid_columnconfigure(0, weight=1)
        row_frame.grid_columnconfigure(1, weight=2)
        row_frame.grid_columnconfigure(2, weight=3)
        
        # Icono (placeholder)
        icon_frame = ctk.CTkFrame(row_frame, width=32, height=32, fg_color="#555555", corner_radius=5)
        icon_frame.grid(row=0, column=0, padx=10, pady=10)
        
        # Nombre de usuario
        username_label = ctk.CTkLabel(row_frame, text=username, text_color="#CCCCCC")
        username_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # UUID
        uuid_label = ctk.CTkLabel(row_frame, text=uuid, text_color="#CCCCCC")
        uuid_label.grid(row=0, column=2, padx=10, pady=10, sticky="w")
    
    def add_account_dialog(self):
        # Crear ventana para añadir cuenta
        account_window = ctk.CTkToplevel(self)
        account_window.title("Add Account")
        account_window.geometry("400x200")
        account_window.resizable(False, False)
        account_window.grab_set()  # Modal
        
        # Formulario
        form_frame = ctk.CTkFrame(account_window, fg_color="#1A1A1A")
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Nombre de usuario
        username_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        username_frame.pack(fill="x", pady=10)
        
        username_label = ctk.CTkLabel(username_frame, text="Username:", text_color="#CCCCCC")
        username_label.pack(side="left", padx=10)
        
        username_entry = ctk.CTkEntry(username_frame, width=250, fg_color="#333333", text_color="#FFFFFF")
        username_entry.pack(side="left", padx=10)
        
        # Botones
        buttons_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=20)
        
        add_btn = ctk.CTkButton(
            buttons_frame, 
            text="Add", 
            width=120,
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444",
            command=lambda: self.add_account(username_entry.get(), account_window)
        )
        add_btn.pack(side="right", padx=10)
        
        cancel_btn = ctk.CTkButton(
            buttons_frame, 
            text="Cancel", 
            width=120, 
            height=30,
            corner_radius=3,
            fg_color="#555555",
            hover_color="#666666",
            command=account_window.destroy
        )
        cancel_btn.pack(side="right", padx=10)
    
    def add_account(self, username, window):
        # Validar datos
        if not username:
            messagebox.showerror("Error", "Username cannot be empty", parent=window)
            return
        
        # Verificar si ya existe
        if any(a["username"] == username for a in self.accounts):
            messagebox.showerror("Error", f"Account '{username}' already exists", parent=window)
            return
        
        # Añadir cuenta
        account = {
            "username": username,
            "uuid": f"00000000-0000-0000-0000-{random.randint(100000000000, 999999999999)}",
            "type": "DEMO"
        }
        
        self.accounts.append(account)
        
        # Guardar cuentas
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(self.accounts, f, indent=2)
        
        # Actualizar UI
        self.load_account_rows()
        
        # Cerrar ventana
        window.destroy()
        
        # Mostrar mensaje
        messagebox.showinfo("Success", f"Account '{username}' added successfully")
    
    def create_mods_frame(self):
        # Frame para los mods
        frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="#1A1A1A")
        
        # Barra superior
        top_bar = ctk.CTkFrame(frame, height=50, corner_radius=0, fg_color="#1A1A1A")
        top_bar.pack(fill="x")
        
        # Botón de Back
        back_btn = ctk.CTkButton(
            top_bar, 
            text="Back", 
            width=60, 
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444",
            command=lambda: self.show_frame("instances")
        )
        back_btn.pack(side="left", padx=10)
        
        # Título
        self.mods_title = ctk.CTkLabel(top_bar, text="Mods", font=ctk.CTkFont(size=16, weight="bold"), 
                                     text_color="#CCCCCC")
        self.mods_title.pack(side="left", padx=10)
        
        # Botones de acción
        refresh_btn = ctk.CTkButton(
            top_bar, 
            text="🔄 Refresh", 
            width=80,
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444"
        )
        refresh_btn.pack(side="right", padx=10)
        
        add_mod_btn = ctk.CTkButton(
            top_bar, 
            text="+ Add Mod", 
            width=80,
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444"
        )
        add_mod_btn.pack(side="right", padx=10)
        
        # Subtítulo
        self.mods_subtitle_frame = ctk.CTkFrame(frame, height=30, corner_radius=0, fg_color="#252525")
        self.mods_subtitle_frame.pack(fill="x")
        
        self.mods_subtitle = ctk.CTkLabel(self.mods_subtitle_frame, text="Select an instance to view mods", 
                                        text_color="#CCCCCC")
        self.mods_subtitle.pack(side="left", padx=20)
        
        # Tabla de mods
        table_frame = ctk.CTkFrame(frame, fg_color="#1A1A1A")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Encabezados de la tabla
        headers_frame = ctk.CTkFrame(table_frame, height=30, fg_color="#252525")
        headers_frame.pack(fill="x")
        
        # Configurar columnas
        headers_frame.grid_columnconfigure(0, weight=1)
        headers_frame.grid_columnconfigure(1, weight=2)
        headers_frame.grid_columnconfigure(2, weight=1)
        headers_frame.grid_columnconfigure(3, weight=1)
        headers_frame.grid_columnconfigure(4, weight=1)
        
        # Encabezados
        ctk.CTkLabel(headers_frame, text="Icon", text_color="#CCCCCC").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(headers_frame, text="Mod Name", text_color="#CCCCCC").grid(row=0, column=1, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(headers_frame, text="File Version", text_color="#CCCCCC").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(headers_frame, text="Requirement", text_color="#CCCCCC").grid(row=0, column=3, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(headers_frame, text="Last Updated", text_color="#CCCCCC").grid(row=0, column=4, padx=10, pady=5, sticky="w")
        
        # Contenido de la tabla
        self.mods_content_frame = ctk.CTkFrame(table_frame, fg_color="#1A1A1A")
        self.mods_content_frame.pack(fill="both", expand=True)
        
        # Configurar columnas
        self.mods_content_frame.grid_columnconfigure(0, weight=1)
        self.mods_content_frame.grid_columnconfigure(1, weight=2)
        self.mods_content_frame.grid_columnconfigure(2, weight=1)
        self.mods_content_frame.grid_columnconfigure(3, weight=1)
        self.mods_content_frame.grid_columnconfigure(4, weight=1)
        
        # Agregar mods de ejemplo
        self.add_mod_row(self.mods_content_frame, 0, "Sodium", "0.5.0", "1.20.2", "Required", "Jan 15, 2024")
        self.add_mod_row(self.mods_content_frame, 1, "Sodium", "0.5.0", "1.20.2", "Required", "Jan 15, 2024")
        self.add_mod_row(self.mods_content_frame, 2, "Sodium", "0.5.0", "1.20.2", "Required", "Jan 15, 2024")
        
        return frame
    
    def add_mod_row(self, parent, row, name, version, mc_version, requirement, last_updated):
        # Crear fila para un mod
        row_frame = ctk.CTkFrame(parent, height=50, fg_color="#222222")
        row_frame.grid(row=row, column=0, columnspan=5, sticky="ew", pady=1)
        
        # Configurar columnas
        row_frame.grid_columnconfigure(0, weight=1)
        row_frame.grid_columnconfigure(1, weight=2)
        row_frame.grid_columnconfigure(2, weight=1)
        row_frame.grid_columnconfigure(3, weight=1)
        row_frame.grid_columnconfigure(4, weight=1)
        
        # Icono (placeholder)
        icon_frame = ctk.CTkFrame(row_frame, width=32, height=32, fg_color="#55AA55", corner_radius=5)
        icon_frame.grid(row=0, column=0, padx=10, pady=10)
        
        # Nombre del mod
        name_label = ctk.CTkLabel(row_frame, text=name, text_color="#CCCCCC")
        name_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # Versión
        version_label = ctk.CTkLabel(row_frame, text=f"{version} - {mc_version}", text_color="#CCCCCC")
        version_label.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        
        # Requisito
        req_label = ctk.CTkLabel(row_frame, text=requirement, text_color="#CCCCCC")
        req_label.grid(row=0, column=3, padx=10, pady=10, sticky="w")
        
        # Última actualización
        date_label = ctk.CTkLabel(row_frame, text=last_updated, text_color="#CCCCCC")
        date_label.grid(row=0, column=4, padx=10, pady=10, sticky="w")
    
    def create_packs_frame(self):
        # Frame para los paquetes de recursos
        frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="#1A1A1A")
        
        # Contenido de ejemplo
        label = ctk.CTkLabel(frame, text="Resource Packs", font=ctk.CTkFont(size=20, weight="bold"), 
                            text_color="#CCCCCC")
        label.pack(pady=50)
        
        info = ctk.CTkLabel(frame, text="This section would contain resource packs management", 
                           text_color="#CCCCCC")
        info.pack()
        
        return frame
    
    def create_worlds_frame(self):
        # Frame para los mundos
        frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="#1A1A1A")
        
        # Contenido de ejemplo
        label = ctk.CTkLabel(frame, text="Worlds", font=ctk.CTkFont(size=20, weight="bold"), 
                            text_color="#CCCCCC")
        label.pack(pady=50)
        
        info = ctk.CTkLabel(frame, text="This section would contain worlds management", 
                           text_color="#CCCCCC")
        info.pack()
        
        return frame
    
    def create_settings_frame(self):
        # Frame para los ajustes
        frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="#1A1A1A")
        
        # Contenido de ejemplo
        label = ctk.CTkLabel(frame, text="Settings", font=ctk.CTkFont(size=20, weight="bold"), 
                            text_color="#CCCCCC")
        label.pack(pady=20)
        
        # Ajustes de ejemplo
        settings_frame = ctk.CTkFrame(frame, fg_color="#222222")
        settings_frame.pack(fill="x", padx=50, pady=20)
        
        # Java Path
        java_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        java_frame.pack(fill="x", pady=10)
        
        java_label = ctk.CTkLabel(java_frame, text="Java Path:", text_color="#CCCCCC")
        java_label.pack(side="left", padx=10)
        
        self.java_entry = ctk.CTkEntry(java_frame, width=400, fg_color="#333333", text_color="#FFFFFF")
        self.java_entry.pack(side="left", padx=10)
        self.java_entry.insert(0, self.config.get("java_path", "java"))
        
        java_browse = ctk.CTkButton(
            java_frame, 
            text="Browse", 
            width=80,
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444",
            command=self.browse_java_path
        )
        java_browse.pack(side="left", padx=10)
        
        # Memoria
        memory_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        memory_frame.pack(fill="x", pady=10)
        
        memory_label = ctk.CTkLabel(memory_frame, text="Memory (GB):", text_color="#CCCCCC")
        memory_label.pack(side="left", padx=10)
        
        memory_min_label = ctk.CTkLabel(memory_frame, text="Min:", text_color="#CCCCCC")
        memory_min_label.pack(side="left", padx=10)
        
        self.memory_min = ctk.CTkEntry(memory_frame, width=60, fg_color="#333333", text_color="#FFFFFF")
        self.memory_min.pack(side="left", padx=5)
        self.memory_min.insert(0, str(self.config.get("min_memory", 2)))
        
        memory_max_label = ctk.CTkLabel(memory_frame, text="Max:", text_color="#CCCCCC")
        memory_max_label.pack(side="left", padx=10)
        
        self.memory_max = ctk.CTkEntry(memory_frame, width=60, fg_color="#333333", text_color="#FFFFFF")
        self.memory_max.pack(side="left", padx=5)
        self.memory_max.insert(0, str(self.config.get("max_memory", 4)))
        
        # Tema
        theme_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        theme_frame.pack(fill="x", pady=10)
        
        theme_label = ctk.CTkLabel(theme_frame, text="Theme:", text_color="#CCCCCC")
        theme_label.pack(side="left", padx=10)
        
        self.theme_var = ctk.StringVar(value=self.config.get("theme", "dark").capitalize())
        theme_dropdown = ctk.CTkOptionMenu(
            theme_frame, 
            values=["Light", "Dark", "System"], 
            variable=self.theme_var,
            command=self.change_theme,
            fg_color="#333333",
            button_color="#444444",
            button_hover_color="#555555",
            dropdown_fg_color="#333333",
            dropdown_hover_color="#444444",
            text_color="#FFFFFF"
        )
        theme_dropdown.pack(side="left", padx=10)
        
        # Directorio del launcher
        launcher_dir_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        launcher_dir_frame.pack(fill="x", pady=10)
        
        launcher_dir_label = ctk.CTkLabel(launcher_dir_frame, text="Launcher Directory:", text_color="#CCCCCC")
        launcher_dir_label.pack(side="left", padx=10)
        
        launcher_dir_value = ctk.CTkLabel(launcher_dir_frame, text=LAUNCHER_DIR, text_color="#CCCCCC")
        launcher_dir_value.pack(side="left", padx=10)
        
        open_dir_btn = ctk.CTkButton(
            launcher_dir_frame, 
            text="Open", 
            width=80,
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444",
            command=self.open_launcher_dir
        )
        open_dir_btn.pack(side="left", padx=10)
        
        # Botones de guardar/cancelar
        buttons_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=20)
        
        save_btn = ctk.CTkButton(
            buttons_frame, 
            text="Save Settings", 
            width=120,
            height=30,
            corner_radius=3,
            fg_color="#333333",
            hover_color="#444444",
            command=self.save_settings
        )
        save_btn.pack(side="right", padx=10)
        
        cancel_btn = ctk.CTkButton(
            buttons_frame, 
            text="Cancel", 
            width=120, 
            height=30,
            corner_radius=3,
            fg_color="#555555",
            hover_color="#666666",
            command=lambda: self.show_frame("instances")
        )
        cancel_btn.pack(side="right", padx=10)
        
        return frame
    
    def browse_java_path(self):
        # Abrir diálogo para seleccionar ruta de Java
        if sys.platform == "win32":
            file_types = [("Executable files", "*.exe")]
            title = "Select Java Executable"
        else:
            file_types = [("All files", "*")]
            title = "Select Java Executable"
        
        java_path = filedialog.askopenfilename(
            title=title,
            filetypes=file_types
        )
        
        if java_path:
            self.java_entry.delete(0, "end")
            self.java_entry.insert(0, java_path)
    
    def open_launcher_dir(self):
        # Abrir directorio del launcher
        if os.path.exists(LAUNCHER_DIR):
            if sys.platform == "win32":
                os.startfile(LAUNCHER_DIR)
            else:
                subprocess.Popen(["xdg-open", LAUNCHER_DIR])
    
    def change_theme(self, theme):
        # Cambiar tema
        if theme == "Light":
            ctk.set_appearance_mode("light")
        elif theme == "Dark":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("system")
    
    def save_settings(self):
        # Guardar ajustes
        self.config["java_path"] = self.java_entry.get()
        self.config["min_memory"] = int(self.memory_min.get())
        self.config["max_memory"] = int(self.memory_max.get())
        self.config["theme"] = self.theme_var.get().lower()
        
        self.save_config()
        
        # Mostrar mensaje
        messagebox.showinfo("Success", "Settings saved successfully")
    
    def launch_instance(self, instance_name):
        # Buscar instancia
        instances = self.config.get("instances", [])
        instance = next((i for i in instances if i["name"] == instance_name), None)
        
        if not instance:
            messagebox.showerror("Error", f"Instance '{instance_name}' not found")
            return
        
        # Actualizar la última vez jugada
        for i, inst in enumerate(instances):
            if inst["name"] == instance_name:
                instances[i]["last_played"] = datetime.now().isoformat()
                break
        
        self.config["instances"] = instances
        self.save_config()
        
        # Actualizar UI de la consola
        self.console_title.configure(text=instance_name)
        self.console_subtitle.configure(text=f"{instance.get('version', '1.20.2')} - {instance.get('loader', 'Vanilla')}")
        self.kill_btn.configure(state="normal")
        
        # Limpiar consola
        self.console_text.delete("1.0", "end")
        
        # Mostrar la consola
        self.show_frame("console")
        
        # Iniciar el proceso de Minecraft en un hilo separado
        self.minecraft_process = None
        threading.Thread(target=self.run_minecraft, args=(instance_name, instance)).start()
    
    def run_minecraft(self, instance_name, instance):
        # Simular logs de consola en tiempo real
        
        self.log_to_console(f"[Launcher/INFO]: Java path: {self.config.get('java_path', 'java')}")
        self.log_to_console(f"[Launcher/INFO]: Instance directory: {os.path.join(INSTANCES_DIR, instance_name)}")
        
        # Verificar Java
        java_path = self.config.get("java_path", "java")
        self.log_to_console(f"[Launcher/INFO]: Checking Java...")
        
        try:
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                java_process = subprocess.Popen(
                    [java_path, "-version"], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo
                )
            else:
                java_process = subprocess.Popen(
                    [java_path, "-version"], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
            
            _, java_version = java_process.communicate()
            java_version = java_version.decode('utf-8', errors='ignore')
            
            self.log_to_console(f"[Launcher/INFO]: Java version: {java_version.splitlines()[0]}")
        except Exception as e:
            self.log_to_console(f"[Launcher/ERROR]: Failed to check Java: {e}")
            self.kill_btn.configure(state="disabled")
            return
        
        # Preparar argumentos de Java
        min_memory = instance.get("min_memory", self.config.get("min_memory", 2))
        max_memory = instance.get("max_memory", self.config.get("max_memory", 4))
        
        self.log_to_console(f"[Launcher/INFO]: Memory allocation: {min_memory}G to {max_memory}G")
        
        # En un launcher real, aquí descargaríamos los archivos necesarios
        # y prepararíamos los argumentos para lanzar Minecraft
        self.log_to_console(f"[Launcher/INFO]: Preparing to launch Minecraft {instance.get('version', '1.20.2')}...")
        self.log_to_console(f"[Launcher/INFO]: Checking for updates...")
        self.log_to_console(f"[Launcher/INFO]: Downloading libraries...")
        
        # Simular descarga
        for i in range(1, 6):
            self.log_to_console(f"[Launcher/INFO]: Downloading libraries... {i*20}%")
            time.sleep(0.5)
        
        self.log_to_console(f"[Launcher/INFO]: Verifying library integrity...")
        self.log_to_console(f"[Launcher/INFO]: All libraries are up to date")
        
        # En un launcher real, aquí lanzaríamos Minecraft
        self.log_to_console(f"[Launcher/INFO]: Launching game...")
        
        # Simular lanzamiento
        self.log_to_console(f"[Minecraft/INFO]: Setting up window...")
        self.log_to_console(f"[Minecraft/INFO]: LWJGL Version: 3.3.1")
        
        if instance.get("loader", "Vanilla") != "Vanilla":
            self.log_to_console(f"[Minecraft/INFO]: Loading {instance.get('loader', 'Fabric')} mods...")
            self.log_to_console(f"[Minecraft/INFO]: Found 12 mods to load")
            self.log_to_console(f"[Minecraft/INFO]: Successfully loaded 12 mods")
        
        self.log_to_console(f"[Minecraft/INFO]: Preparing integrated server")
        self.log_to_console(f"[Minecraft/INFO]: Loaded 16 chunks")
        self.log_to_console(f"[Minecraft/INFO]: Game ready!")
    
    def log_to_console(self, message):
        # Agregar mensaje a la consola
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.console_text.insert("end", f"{timestamp} {message}\n")
        self.console_text.see("end")
        
        # Actualizar UI
        self.update()
    
    def kill_minecraft(self):
        # Detener proceso de Minecraft
        if hasattr(self, 'minecraft_process') and self.minecraft_process:
            try:
                self.minecraft_process.terminate()
                self.log_to_console("[Launcher/INFO]: Game process terminated")
            except:
                self.log_to_console("[Launcher/WARNING]: Failed to terminate game process")
        
        self.kill_btn.configure(state="disabled")
        self.log_to_console("[Launcher/INFO]: Game stopped")

# Iniciar la aplicación
if __name__ == "__main__":
    app = MinecraftLauncher()
    app.mainloop()
