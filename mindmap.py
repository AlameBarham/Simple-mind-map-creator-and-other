import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, colorchooser
import json
import os
import math
import copy
import random

class MindMapNode:
    def __init__(self, text, x, y, parent=None, color="lightblue"):
        self.text = text
        self.x = x
        self.y = y
        self.parent = parent
        self.children = []
        self.id = None
        self.text_id = None
        self.connector_id = None
        self.color = color

class MindMapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mind Map Creator")
        self.root.geometry("800x600")

        self.timer_label = tk.Label(self.root, text="Timer: 00:00:00", font=("Arial", 10))
        self.timer_label.pack(side=tk.TOP, anchor="e")

        self.timer_running = False
        self.timer_seconds = 0

        self.setup_timer_canvas()

        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.nodes = []
        self.selected_node = None
        self.drag_data = {"x": 0, "y": 0, "item": None}

        self.current_file = None
        self.recent_files = []

        self.undo_stack = []
        self.redo_stack = []

        self.setup_menu()
        self.setup_bindings()
        self.create_central_node()

        self.bubbles = []

        self.add_logo()

    def add_logo(self):
        pass

    def setup_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_mindmap)
        file_menu.add_command(label="Save", command=self.save_mindmap)
        file_menu.add_command(label="Save As", command=self.save_as_mindmap)
        file_menu.add_command(label="Load", command=self.load_mindmap)
        file_menu.add_command(label="Open Recent", command=self.open_recent_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Export as PNG", command=self.export_as_png)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Add Child", command=self.add_child_node)
        edit_menu.add_command(label="Delete Node", command=self.delete_node)
        edit_menu.add_command(label="Edit Text", command=self.edit_node_text)
        edit_menu.add_command(label="Change Node Color", command=self.change_node_color)
        edit_menu.add_separator()
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Center View on Node", command=self.center_view_on_node)
        edit_menu.add_separator()
        edit_menu.add_command(label="Search Node", command=self.search_node, accelerator="Ctrl+F")
        menubar.add_cascade(label="Edit", menu=edit_menu)

        nn_menu = tk.Menu(menubar, tearoff=0)
        nn_menu.add_command(label="Show Info", command=self.show_nn_info)
        nn_menu.add_command(label="Add Example Node", command=self.add_nn_example_node)
        menubar.add_cascade(label="Neural Networks", menu=nn_menu)

        timer_menu = tk.Menu(menubar, tearoff=0)
        timer_menu.add_command(label="Start Timer", command=self.start_timer)
        timer_menu.add_command(label="Stop Timer", command=self.stop_timer)
        timer_menu.add_command(label="Reset Timer", command=self.reset_timer)
        menubar.add_cascade(label="Timer", menu=timer_menu)

        self.root.config(menu=menubar)

    def setup_bindings(self):
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.bind("<Control-f>", lambda e: self.search_node())

    def create_central_node(self):
        center_x = self.canvas.winfo_width() // 2 or 400
        center_y = self.canvas.winfo_height() // 2 or 300
        central_node = MindMapNode("Central Idea", center_x, center_y)
        self.draw_node(central_node)
        self.nodes.append(central_node)

    def draw_node(self, node):
        node_width = 100
        node_height = 60
        try:
            font_family = "Vazirmatn"
            self.canvas.create_text(0, 0, text="", font=(font_family, 10))
        except tk.TclError:
            font_family = "Tahoma"
        node.id = self.canvas.create_oval(
            node.x - node_width // 2, node.y - node_height // 2,
            node.x + node_width // 2, node.y + node_height // 2,
            fill=node.color, outline="black", width=2
        )
        node.text_id = self.canvas.create_text(
            node.x, node.y, text=node.text, font=(font_family, 12), width=90
        )
        if node.parent:
            start = self.get_edge_point(node.parent, node)
            end = self.get_edge_point(node, node.parent)
            node.connector_id = self.canvas.create_line(
                start[0], start[1], end[0], end[1],
                fill="black", width=2
            )

    def get_edge_point(self, node_from, node_to):
        dx = node_to.x - node_from.x
        dy = node_to.y - node_from.y
        angle = math.atan2(dy, dx)
        node_width = 100
        node_height = 60
        x = node_from.x + (node_width // 2) * math.cos(angle)
        y = node_from.y + (node_height // 2) * math.sin(angle)
        return (x, y)

    def on_click(self, event):
        clicked_node = self.find_node_at_position(event.x, event.y)
        if clicked_node:
            self.selected_node = clicked_node
            self.drag_data["item"] = clicked_node
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            self.canvas.itemconfig(clicked_node.id, fill="lightgreen")
        else:
            self.selected_node = None

    def on_drag(self, event):
        if self.drag_data["item"]:
            node = self.drag_data["item"]
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]

            self.canvas.move(node.id, dx, dy)
            self.canvas.move(node.text_id, dx, dy)
            node.x += dx
            node.y += dy

            if node.parent and node.connector_id:
                self.canvas.delete(node.connector_id)
                start = self.get_edge_point(node.parent, node)
                end = self.get_edge_point(node, node.parent)
                node.connector_id = self.canvas.create_line(
                    start[0], start[1], end[0], end[1],
                    fill="black", width=2
                )

            for child in node.children:
                if child.connector_id:
                    self.canvas.delete(child.connector_id)
                start = self.get_edge_point(node, child)
                end = self.get_edge_point(child, node)
                child.connector_id = self.canvas.create_line(
                    start[0], start[1], end[0], end[1],
                    fill="black", width=2
                )

            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def on_release(self, event):
        if self.drag_data["item"]:
            node = self.drag_data["item"]
            self.canvas.itemconfig(node.id, fill=node.color)
            self.drag_data["item"] = None
            self.push_undo_state()

    def on_double_click(self, event):
        clicked_node = self.find_node_at_position(event.x, event.y)
        if clicked_node:
            self.edit_node_text()
        else:
            self.add_child_node()

    def find_node_at_position(self, x, y):
        for node in self.nodes:
            if (node.x - 50 <= x <= node.x + 50 and
                node.y - 30 <= y <= node.y + 30):
                return node
        return None

    def add_child_node(self):
        if not self.selected_node:
            messagebox.showwarning("Warning", "Please select a node first!")
            return

        parent = self.selected_node
        child_text = simpledialog.askstring("Add Child", "Enter child node text:")

        if child_text:
            num_children = len(parent.children)
            angle = (num_children * 60) % 360
            rad = math.radians(angle)
            distance = 150

            child_x = parent.x + distance * math.cos(rad)
            child_y = parent.y + distance * math.sin(rad)
            child_x = max(60, min(self.canvas.winfo_width() - 60, child_x))
            child_y = max(40, min(self.canvas.winfo_height() - 40, child_y))

            child_node = MindMapNode(child_text, child_x, child_y, parent)
            parent.children.append(child_node)
            self.nodes.append(child_node)
            self.draw_node(child_node)
            self.push_undo_state()

    def delete_node(self):
        if not self.selected_node:
            messagebox.showwarning("Warning", "Please select a node first!")
            return
        if self.selected_node.parent is None:
            messagebox.showwarning("Warning", "Cannot delete the central node!")
            return

        node = self.selected_node
        self.push_undo_state()

        for child in node.children[:]:
            self.selected_node = child
            self.delete_node()

        if node.parent:
            node.parent.children.remove(node)
        self.nodes.remove(node)
        self.canvas.delete(node.id)
        self.canvas.delete(node.text_id)
        if node.connector_id:
            self.canvas.delete(node.connector_id)
        self.selected_node = None

    def edit_node_text(self):
        if not self.selected_node:
            messagebox.showwarning("Warning", "Please select a node first!")
            return
        new_text = simpledialog.askstring("Edit Text", "Enter new text:",
                                          initialvalue=self.selected_node.text)
        if new_text:
            self.push_undo_state()
            self.selected_node.text = new_text
            self.canvas.itemconfig(self.selected_node.text_id, text=new_text)

    def change_node_color(self):
        if not self.selected_node:
            messagebox.showwarning("Warning", "Please select a node first!")
            return
        color = colorchooser.askcolor(title="Choose node color", initialcolor=self.selected_node.color)[1]
        if color:
            self.push_undo_state()
            self.selected_node.color = color
            self.canvas.itemconfig(self.selected_node.id, fill=color)

    def new_mindmap(self):
        self.push_undo_state()
        self.canvas.delete("all")
        self.nodes = []
        self.selected_node = None
        self.create_central_node()

    def save_mindmap(self):
        if not self.current_file:
            self.save_as_mindmap()
            return
        data = {
            "nodes": self.serialize_nodes(self.nodes)
        }
        with open(self.current_file, "w") as f:
            json.dump(data, f, indent=2)
        self.add_to_recent(self.current_file)

    def save_as_mindmap(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return
        self.current_file = file_path
        self.save_mindmap()

    def load_mindmap(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return
        self.current_file = file_path
        with open(file_path, "r") as f:
            data = json.load(f)
        self.canvas.delete("all")
        self.nodes = []
        self.selected_node = None
        self.deserialize_nodes(data["nodes"])
        self.add_to_recent(file_path)
        self.push_undo_state(clear_redo=True)

    def add_to_recent(self, file_path):
        if file_path not in self.recent_files:
            self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:5]

    def open_recent_menu(self):
        menu = tk.Menu(self.root, tearoff=0)
        for file in self.recent_files:
            menu.add_command(label=file, command=lambda f=file: self.load_recent_file(f))
        try:
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            menu.grab_release()

    def load_recent_file(self, file_path):
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "File not found!")
            return
        self.current_file = file_path
        with open(file_path, "r") as f:
            data = json.load(f)
        self.canvas.delete("all")
        self.nodes = []
        self.selected_node = None
        self.deserialize_nodes(data["nodes"])
        self.push_undo_state(clear_redo=True)

    def export_as_png(self):
        try:
            import pyscreenshot as ImageGrab
        except ImportError:
            messagebox.showerror("Error", "Please install pyscreenshot:\npip install pyscreenshot")
            return
        x = self.root.winfo_rootx() + self.canvas.winfo_x()
        y = self.root.winfo_rooty() + self.canvas.winfo_y()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        img = ImageGrab.grab(bbox=(x, y, x1, y1))
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if file_path:
            img.save(file_path)
            messagebox.showinfo("Exported", f"Mind map exported as {file_path}")

    def serialize_nodes(self, nodes):
        serialized = []
        for node in nodes:
            if node.parent is None or node in node.parent.children:
                serialized_node = {
                    "text": node.text,
                    "x": node.x,
                    "y": node.y,
                    "color": node.color,
                    "children": self.serialize_nodes(node.children)
                }
                serialized.append(serialized_node)
        return serialized

    def deserialize_nodes(self, nodes_data, parent=None):
        for node_data in nodes_data:
            node = MindMapNode(
                node_data["text"],
                node_data["x"],
                node_data["y"],
                parent,
                node_data.get("color", "lightblue")
            )
            if parent:
                parent.children.append(node)
            self.nodes.append(node)
            self.draw_node(node)
            if "children" in node_data:
                self.deserialize_nodes(node_data["children"], node)

    def center_view_on_node(self):
        if not self.selected_node:
            messagebox.showwarning("Warning", "Please select a node first!")
            return
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x = self.selected_node.x
        y = self.selected_node.y
        self.canvas.xview_moveto(max(0, x - canvas_width // 2) / self.canvas.winfo_width())
        self.canvas.yview_moveto(max(0, y - canvas_height // 2) / self.canvas.winfo_height())

    def push_undo_state(self, clear_redo=True):
        state = json.dumps(self.serialize_nodes(self.nodes))
        self.undo_stack.append(state)
        if clear_redo:
            self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        if len(self.undo_stack) == 1:
            return
        state = self.undo_stack.pop()
        self.redo_stack.append(state)
        prev_state = self.undo_stack[-1]
        self.restore_state(prev_state)

    def redo(self):
        if not self.redo_stack:
            return
        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        self.restore_state(state)

    def restore_state(self, state_json):
        nodes_data = json.loads(state_json)
        self.canvas.delete("all")
        self.nodes = []
        self.selected_node = None
        self.deserialize_nodes(nodes_data)

    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.update_timer()

    def stop_timer(self):
        self.timer_running = False

    def reset_timer(self):
        self.timer_running = False
        self.timer_seconds = 0
        self.timer_label.config(text="Timer: 00:00:00")
        self.update_timer_bubbles()

    def setup_timer_canvas(self):
        self.timer_canvas = tk.Canvas(self.root, width=160, height=36, bg="white", highlightthickness=0)
        self.timer_canvas.pack(side=tk.TOP, anchor="w", padx=5, pady=2)

    def add_timer_bubble(self):
        bubble = {
            "x": random.randint(20, 140),
            "y": 30,
            "vx": random.uniform(-0.7, 0.7),
            "vy": random.uniform(-1.5, -0.5),
            "r": random.randint(8, 14),
            "color": random.choice(["#6ec6ff", "#1976d2", "#ff9800", "#90caf9", "#81c784", "#f06292"]),
            "alpha": 1.0,
            "life": random.randint(60, 90)
        }
        if len(self.bubbles) < 18:
            self.bubbles.append(bubble)

    def update_timer_bubbles(self):
        self.timer_canvas.delete("all")
        new_bubbles = []
        for bubble in self.bubbles:
            bubble["x"] += bubble["vx"]
            bubble["y"] += bubble["vy"]
            bubble["r"] *= 0.992
            bubble["life"] -= 1
            bubble["alpha"] = max(0, bubble["life"] / 90)
            base_color = self._hex_to_rgb(bubble["color"])
            fade_color = tuple(int(255 * (1 - bubble["alpha"]) + c * bubble["alpha"]) for c in base_color)
            color = self._rgb_to_hex(fade_color)
            if bubble["life"] > 0 and bubble["r"] > 2:
                self.timer_canvas.create_oval(
                    bubble["x"]-bubble["r"], bubble["y"]-bubble["r"],
                    bubble["x"]+bubble["r"], bubble["y"]+bubble["r"],
                    fill=color, outline="", width=0
                )
                new_bubbles.append(bubble)
        self.bubbles = new_bubbles

        h = self.timer_seconds // 3600
        m = (self.timer_seconds % 3600) // 60
        s = self.timer_seconds % 60
        self.timer_canvas.create_text(80, 18, text=f"{h:02d}:{m:02d}:{s:02d}", font=("Arial", 11, "bold"), fill="#333")

    def update_timer(self):
        if self.timer_running:
            self.timer_seconds += 1
            self.timer_label.config(text=f"Timer: {self.timer_seconds//3600:02d}:{(self.timer_seconds%3600)//60:02d}:{self.timer_seconds%60:02d}")
            self.add_timer_bubble()
            self.update_timer_bubbles()
            self.root.after(1000, self.update_timer)
        else:
            self.update_timer_bubbles()

    def show_nn_info(self):
        messagebox.showinfo("Neural Networks", "Neural networks are a set of algorithms, modeled loosely after the human brain, that are designed to recognize patterns.")

    def add_nn_example_node(self):
        if not self.selected_node:
            messagebox.showwarning("Warning", "Please select a node first!")
            return
        try:
            num_layers = int(simpledialog.askstring("Neural Network", "How many layers?"))
            if num_layers < 1:
                raise ValueError
        except Exception:
            messagebox.showerror("Error", "Invalid number of layers.")
            return

        layers_nodes = []
        parent_layer = [self.selected_node]

        for layer in range(1, num_layers + 1):
            weights_str = simpledialog.askstring(
                "Layer Weights",
                f"Enter weights for layer {layer} (comma separated, one row per neuron, separate rows with ';'):\nExample: 0.5,0.2,0.1; -0.3,0.7,0.8"
            )
            bias_str = simpledialog.askstring(
                "Layer Bias",
                f"Enter biases for layer {layer} (comma separated, one per neuron):\nExample: 0.1, -0.2, 0.3"
            )
            if not weights_str or not bias_str:
                continue

            weights_rows = [row.strip() for row in weights_str.split(";") if row.strip()]
            biases = [b.strip() for b in bias_str.split(",") if b.strip()]
            num_neurons = len(weights_rows)
            if num_neurons != len(biases):
                messagebox.showerror("Error", f"Number of neurons and biases do not match in layer {layer}!")
                return

            angle_start = -90
            angle_step = 180 / max(1, num_neurons - 1) if num_neurons > 1 else 0
            distance = 150 + (layer - 1) * 60

            layer_nodes = []
            for i, (weights, bias) in enumerate(zip(weights_rows, biases)):
                angle = angle_start + i * angle_step
                rad = math.radians(angle)
                child_x = self.selected_node.x + distance * math.cos(rad)
                child_y = self.selected_node.y + distance * math.sin(rad)
                child_x = max(60, min(self.canvas.winfo_width() - 60, child_x))
                child_y = max(40, min(self.canvas.winfo_height() - 40, child_y))
                child_text = f"Layer {layer}\nWeights: {weights}\nBias: {bias}"
                child_node = MindMapNode(child_text, child_x, child_y, None)
                self.nodes.append(child_node)
                self.draw_node(child_node)
                layer_nodes.append(child_node)

            for child_node in layer_nodes:
                for parent_node in parent_layer:
                    start = self.get_edge_point(parent_node, child_node)
                    end = self.get_edge_point(child_node, parent_node)
                    self.canvas.create_line(
                        start[0], start[1], end[0], end[1],
                        fill="#888", width=2, dash=(2, 2)
                    )
            parent_layer = layer_nodes
            layers_nodes.append(layer_nodes)

        self.push_undo_state()
        self.animate_bubbles()

    def animate_bubbles(self):
        self.update_timer_bubbles()
        self.root.after(50, self.animate_bubbles)

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb):
        return '#%02x%02x%02x' % rgb

    def search_node(self):
        query = simpledialog.askstring("Search Node", "Enter text to search for:")
        if not query:
            return
        found = []
        for node in self.nodes:
            if query.lower() in node.text.lower():
                found.append(node)
                self.canvas.itemconfig(node.id, outline="red", width=4)
            else:
                self.canvas.itemconfig(node.id, outline="black", width=2)
        if found:
            node = found[0]
            self.canvas.xview_moveto(max(0, node.x - 200) / self.canvas.winfo_width())
            self.canvas.yview_moveto(max(0, node.y - 150) / self.canvas.winfo_height())
            messagebox.showinfo("Search", f"{len(found)} node(s) found and highlighted.")
        else:
            messagebox.showinfo("Search", "No node found with that text.")


if __name__ == "__main__":
    root = tk.Tk()
    app = MindMapApp(root)
    root.mainloop()

__pycache__/
*.pyc
*.pyo
*.pyd
*.swp
*.swo
*.bak
*.tmp
.DS_Store
.idea/
.vscode/
.env