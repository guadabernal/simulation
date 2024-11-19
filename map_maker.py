import tkinter as tk

# TODO: fix massive issue with pixels and cells confusion :(

class FloorPlanDesigner:
    def __init__(self, master):
        
        self.num_cells_width = 150  # num of cells in width (columns)
        self.num_cells_height = 105  # num of cells in height (rows)
        self.window_width = 1000    # Width of window in pixels

        self.grid_size = self.window_width / self.num_cells_width
        self.window_height = self.grid_size * self.num_cells_height
        self.wall_thickness = 2 * self.grid_size

        self.walls = []  # walls list: (x, y, width, height, id)
        self.actions = []  # Stack for undo

        self.start_point = None
        self.is_selecting_start = True
        self.is_creating_gap = False

        self.mode = 'wall'      # Modes: 'wall', 'pixel', 'gap'

        # debugging stuff
        self.gap_highlighted_wall = None
        self.gap_highlighted_items = []
        self.gap_click_position = None

        self.canvas = tk.Canvas(master, width=self.window_width, height=self.window_height)
        self.canvas.pack()

        self.draw_grid()
        self.draw_boundary_walls()

        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Mode selection
        self.mode_frame = tk.Frame(master)
        self.mode_frame.pack()
        self.wall_button = tk.Button(self.mode_frame, text="Wall Mode", command=self.set_wall_mode)
        self.wall_button.grid(row=0, column=0)
        self.pixel_button = tk.Button(self.mode_frame, text="Pixel Mode", command=self.set_pixel_mode)
        self.pixel_button.grid(row=0, column=1)
        self.gap_button = tk.Button(self.mode_frame, text="Gap Mode", command=self.set_gap_mode)
        self.gap_button.grid(row=0, column=2)

        # Undo & print
        self.undo_button = tk.Button(master, text="Undo", command=self.undo_action)
        self.undo_button.pack()
        self.print_button = tk.Button(master, text="Print Walls", command=self.print_walls)
        self.print_button.pack()

    def draw_grid(self):
        # Draw vertical grid lines
        for i in range(self.num_cells_width + 1):
            x = i * self.grid_size
            self.canvas.create_line(x, 0, x, self.window_height, fill='lightgrey')
        # Draw horizontal grid lines
        for i in range(self.num_cells_height + 1):
            y = i * self.grid_size
            self.canvas.create_line(0, y, self.window_width, y, fill='lightgrey')

    def draw_boundary_walls(self):
        # Left boundary wall
        rect = self.canvas.create_rectangle(0, 0, self.wall_thickness, self.window_height, fill='black')
        self.walls.append({'coords': (0, 0, self.wall_thickness, self.window_height), 'id': rect})
        self.actions.append(('add', self.walls[-1]))

        # Right boundary wall
        rect = self.canvas.create_rectangle(self.window_width - self.wall_thickness, 0,
                                            self.window_width, self.window_height, fill='black')
        self.walls.append({'coords': (self.window_width - self.wall_thickness, 0,
                                      self.wall_thickness, self.window_height), 'id': rect})
        self.actions.append(('add', self.walls[-1]))

        # Top boundary wall
        rect = self.canvas.create_rectangle(0, 0, self.window_width, self.wall_thickness, fill='black')
        self.walls.append({'coords': (0, 0, self.window_width, self.wall_thickness), 'id': rect})
        self.actions.append(('add', self.walls[-1]))

        # Bottom boundary wall
        rect = self.canvas.create_rectangle(0, self.window_height - self.wall_thickness,
                                            self.window_width, self.window_height, fill='black')
        self.walls.append({'coords': (0, self.window_height - self.wall_thickness,
                                      self.window_width, self.wall_thickness), 'id': rect})
        self.actions.append(('add', self.walls[-1]))

    def set_wall_mode(self):
        self.clear_gap_highlights()
        self.mode = 'wall'
        self.is_selecting_start = True
        self.start_point = None
        print("Switched to Wall Mode")

    def set_pixel_mode(self):
        self.clear_gap_highlights()
        self.mode = 'pixel'
        self.is_selecting_start = False
        self.start_point = None
        print("Switched to Pixel Mode")

    def set_gap_mode(self):
        if self.gap_highlighted_wall is not None:
            # If a wall is highlighted, confirm gap creation
            wall = self.gap_highlighted_wall
            x_click, y_click = self.gap_click_position
            # Remove highlights
            self.unhighlight_gap()
            # Create the gap
            self.create_gap_in_wall(wall, x_click, y_click)
            self.gap_highlighted_wall = None
            print("Gap created")
        else:
            # Switch to Gap Mode
            self.clear_gap_highlights()
            self.mode = 'gap'
            self.is_selecting_start = False
            self.start_point = None
            print("Switched to Gap Mode")

    def on_canvas_click(self, event):
        x = event.x
        y = event.y

        # Snap x and y to grid
        x = round(x / self.grid_size) * self.grid_size
        y = round(y / self.grid_size) * self.grid_size

        if self.mode == 'wall':
            self.handle_wall_mode(x, y)
        elif self.mode == 'pixel':
            print("Pixel mode is broke")
        elif self.mode == 'gap':
            self.handle_gap_mode(x, y)

    def handle_wall_mode(self, x, y):
        if self.is_selecting_start:
            # Check if start point is attached to an existing wall unless creating a gap
            if not self.is_creating_gap and not self.is_attached_to_wall(x, y):
                print("Attach start point to existing wall")
                return
            self.start_point = (x, y)
            self.is_selecting_start = False
            # print(f"Start point set at {self.start_point}")
        else:
            # Adjust end point to be aligned horizontally or vertically
            x1, y1 = self.start_point
            dx = abs(x - x1)
            dy = abs(y - y1)
            if dx < dy:
                x = x1  # Vertical wall
                # print(f"Drawing vertical wall from {self.start_point} to ({x}, {y})")
            else:
                y = y1  # Horizontal wall
                # print(f"Drawing horizontal wall from {self.start_point} to ({x}, {y})")
            self.draw_wall(self.start_point, (x, y))
            self.start_point = None
            self.is_selecting_start = True

    def handle_gap_mode(self, x, y):
        if self.gap_highlighted_wall is not None:
            # Wall already highlighted; do nothing
            print("Press the 'Gap Mode' button again to confirm the gap creation.")
        else:
            # First click, highlight wall and cells
            wall = self.find_wall_at_position(x, y)
            if wall is None:
                print("No wall found at this position to create a gap")
                return
            self.highlight_gap(wall, x, y)

    def highlight_gap(self, wall, x_click, y_click):
        # Snap the click position to the nearest cell boundary
        x_click = round(x_click / self.grid_size) * self.grid_size
        y_click = round(y_click / self.grid_size) * self.grid_size

        # Change the color of the wall to indicate selection
        self.canvas.itemconfig(wall['id'], fill='blue')  # For example, change to blue

        # Store the wall and click position
        self.gap_highlighted_wall = wall
        self.gap_click_position = (x_click, y_click)

        # Calculate the 5 cells in either direction along the wall's long edge
        gap_cells = 5
        if wall['coords'][2] > wall['coords'][3]:
            # Horizontal wall
            # Gap from x = x_click - 5 cells to x_click + 5 cells
            x_start = x_click - (gap_cells * self.grid_size)
            x_end = x_click + (gap_cells * self.grid_size)

            # Adjust to cell boundaries
            x_start = max(x_start, wall['coords'][0])
            x_end = min(x_end, wall['coords'][0] + wall['coords'][2])

            for i in range(int((x_end - x_start) / self.grid_size)):
                x = x_start + i * self.grid_size
                y = wall['coords'][1]
                width = self.grid_size
                height = wall['coords'][3]
                rect = self.canvas.create_rectangle(x, y, x + width, y + height, fill='red', stipple='gray25')
                self.gap_highlighted_items.append(rect)
        else:
            # Vertical wall
            # Gap from y = y_click - 5 cells to y_click + 5 cells
            y_start = y_click - (gap_cells * self.grid_size)
            y_end = y_click + (gap_cells * self.grid_size)

            # Adjust to cell boundaries
            y_start = max(y_start, wall['coords'][1])
            y_end = min(y_end, wall['coords'][1] + wall['coords'][3])

            for i in range(int((y_end - y_start) / self.grid_size)):
                x = wall['coords'][0]
                y = y_start + i * self.grid_size
                width = wall['coords'][2]
                height = self.grid_size
                rect = self.canvas.create_rectangle(x, y, x + width, y + height, fill='red', stipple='gray25')
                self.gap_highlighted_items.append(rect)

    def unhighlight_gap(self):
        if self.gap_highlighted_wall: self.canvas.itemconfig(self.gap_highlighted_wall['id'], fill='black')
        for item in self.gap_highlighted_items: self.canvas.delete(item)

        self.gap_highlighted_items.clear()
        self.gap_highlighted_wall = None
        self.gap_click_position = None

    def clear_gap_highlights(self):
        if self.gap_highlighted_wall or self.gap_highlighted_items:
            self.unhighlight_gap()

    def is_attached_to_wall(self, x, y):
        for wall in self.walls:
            wx, wy, wwidth, wheight = wall['coords']
            if wx <= x <= wx + wwidth and wy <= y <= wy + wheight:
                return True
        return False

    def draw_wall(self, start, end):
        x1, y1 = start
        x2, y2 = end

        if x1 == x2:
            # Vertical wall
            x = x1 - self.wall_thickness / 2
            y = min(y1, y2)
            width = self.wall_thickness
            height = abs(y2 - y1)
        else:
            # Horizontal wall
            x = min(x1, x2)
            y = y1 - self.wall_thickness / 2
            width = abs(x2 - x1)
            height = self.wall_thickness

        rect = self.canvas.create_rectangle(x, y, x + width, y + height, fill='black')
        wall_data = {'coords': (x, y, width, height), 'id': rect}
        self.walls.append(wall_data)
        self.actions.append(('add', wall_data))

    def find_wall_at_position(self, x, y):
        for wall in self.walls:
            wx, wy, wwidth, wheight = wall['coords']
            if wx <= x <= wx + wwidth and wy <= y <= wy + wheight:
                return wall
        return None

    def create_gap_in_wall(self, wall, x_click, y_click):
        wx, wy, wwidth, wheight = wall['coords']
        
        print(f"Wall to be split: x={wx}, y={wy}, width={wwidth}, height={wheight}, id={wall['id']}")
        
        self.canvas.delete(wall['id'])
        self.walls.remove(wall)
        self.actions.append(('remove', wall))

        self.is_creating_gap = True
        gap_cells = 3
        gap_size = gap_cells * self.grid_size

        # Horizontal wall
        if wwidth > wheight:

            x_click = round(x_click / self.grid_size) * self.grid_size
            x_gap_start = x_click - (gap_cells * self.grid_size)
            x_gap_end = x_click + (gap_cells * self.grid_size)
            x_gap_start = max(x_gap_start, wx)
            x_gap_end = min(x_gap_end, wx + wwidth)

            left_width = x_gap_start - wx
            if left_width > 0:
                left_coords_start = (wx, wy)
                left_coords_end = (wx + left_width, wy)
                
                print(f"Left sub-wall created from {left_coords_start} to {left_coords_end}")
                
                self.is_selecting_start = True
                self.handle_wall_mode(*left_coords_start)
                self.is_selecting_start = False
                self.handle_wall_mode(*left_coords_end)

            right_x = x_gap_end
            right_width = (wx + wwidth) - x_gap_end
            if right_width > 0:
                right_coords_start = (right_x, wy)
                right_coords_end = (right_x + right_width, wy)
                
                print(f"Right sub-wall created from {right_coords_start} to {right_coords_end}")
                
                self.is_selecting_start = True
                self.handle_wall_mode(*right_coords_start)
                self.is_selecting_start = False
                self.handle_wall_mode(*right_coords_end)
        
        # Vertical wall
        else:
            y_click = round(y_click / self.grid_size) * self.grid_size
            y_gap_start = y_click - (gap_cells * self.grid_size)
            y_gap_end = y_click + (gap_cells * self.grid_size)
            y_gap_start = max(y_gap_start, wy)
            y_gap_end = min(y_gap_end, wy + wheight)

            top_height = y_gap_start - wy
            if top_height > 0:
                top_coords_start = (wx, wy)
                top_coords_end = (wx, wy + top_height)
                
                print(f"Top sub-wall created from {top_coords_start} to {top_coords_end}")
                
                self.is_selecting_start = True
                self.handle_wall_mode(*top_coords_start)
                self.is_selecting_start = False
                self.handle_wall_mode(*top_coords_end)

            bottom_y = y_gap_end
            bottom_height = (wy + wheight) - y_gap_end
            if bottom_height > 0:
                bottom_coords_start = (wx, bottom_y)
                bottom_coords_end = (wx, bottom_y + bottom_height)

                print(f"Bottom sub-wall created from {bottom_coords_start} to {bottom_coords_end}")

                self.is_selecting_start = True
                self.handle_wall_mode(*bottom_coords_start)
                self.is_selecting_start = False
                self.handle_wall_mode(*bottom_coords_end)

        self.is_creating_gap = False

    def undo_action(self):
        if not self.actions: return

        action_type, wall = self.actions.pop()

        if action_type == 'add':
            self.canvas.delete(wall['id'])
            if wall in self.walls: self.walls.remove(wall)
        
        elif action_type == 'remove':
            rect = self.canvas.create_rectangle(*wall['coords'], fill='black')
            wall['id'] = rect
            self.walls.append(wall)

    def print_walls(self):
        walls_in_grid_units = []
        for wall in self.walls:
            x, y, width, height = wall['coords']
            x_grid = x / self.grid_size
            y_grid = y / self.grid_size
            width_grid = width / self.grid_size
            height_grid = height / self.grid_size
            walls_in_grid_units.append((x_grid, y_grid, width_grid, height_grid))
        print(walls_in_grid_units)

root = tk.Tk()
app = FloorPlanDesigner(root)
root.mainloop()
