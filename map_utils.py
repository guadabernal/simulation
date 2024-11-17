# map_utils.py

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors

def generate_floor_plan(grid_size, walls):
    """Generate a floor plan with predefined internal walls/rooms."""
    floor_plan = np.ones(grid_size)

    # Create walls around the perimeter
    floor_plan[0, :] = 0
    floor_plan[-1, :] = 0
    floor_plan[:, 0] = 0
    floor_plan[:, -1] = 0

    # Add predefined internal walls/rooms
    for wall in walls:
        x_start, y_start, width, height = wall
        floor_plan[x_start:x_start + height, y_start:y_start + width] = 0

    return floor_plan

def get_triangle_vertices(x, y, orientation, size=0.7):
    """Compute the vertices of a triangle pointing in the robot's orientation."""
    # Tip of the triangle
    tip_x = y + size * np.sin(orientation)
    tip_y = x + size * np.cos(orientation)

    # Base corners
    base_angle = orientation + np.pi
    base_left_x = y + (size / 2) * np.sin(base_angle + np.pi / 6)
    base_left_y = x + (size / 2) * np.cos(base_angle + np.pi / 6)
    base_right_x = y + (size / 2) * np.sin(base_angle - np.pi / 6)
    base_right_y = x + (size / 2) * np.cos(base_angle - np.pi / 6)

    return [(tip_x, tip_y), (base_left_x, base_left_y), (base_right_x, base_right_y)]

def plot_floor_plan(floor_plan, robots, vine_robot, ax, heat_map_enabled=False, heat_source_position=None):
    """Plot the floor plan, robots, vine robot, and optionally the heat map."""
    ax.clear()

    # Create a custom colormap for the floor plan
    cmap_floor = colors.ListedColormap(['black', 'white'])  # 0: black (obstacle), 1: white (free space)
    ax.imshow(floor_plan, cmap=cmap_floor, origin='lower')

    # Overlay the heat map if enabled
    if heat_map_enabled and heat_source_position is not None:
        heat_map = generate_heat_map(floor_plan.shape, heat_source_position)
        ax.imshow(heat_map, cmap='Reds', origin='lower', alpha=0.5)

    # Plot the vine robot if it has positions
    if len(vine_robot['positions']) > 1:
        vine_positions = np.array(vine_robot['positions'])
        ax.plot(vine_positions[:, 1], vine_positions[:, 0], color='darkgreen', linewidth=5, zorder=2)

    # Plot all robots
    for robot in robots:
        x, y = robot['position']
        orientation = robot['orientation']

        # Plot the robot circle
        ax.scatter(y, x, s=200, c='blue', edgecolors='black', zorder=3)

        # Triangle to indicate the robot's orientation
        vertices = get_triangle_vertices(x, y, orientation)
        triangle = plt.Polygon(vertices, color='red', ec='black', lw=1, alpha=0.7, zorder=4)
        ax.add_patch(triangle)

    ax.set_aspect('equal', adjustable='box')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Floor Plan")

def plot_robot_view(known_map, robots, vine_robot, cone_points_list, ax):
    """Plot the robots' known map of the environment including sensed points."""
    ax.clear()

    # Create a custom colormap for the known map
    cmap_known = colors.ListedColormap(['grey', 'white', 'black'])  # 0: grey (unknown), 1: white (free), 2: black (obstacle)
    display_map = np.full_like(known_map, fill_value=0)  # Initialize with unknown (grey)

    # Map known_map values to display indices
    display_map[known_map == -1] = 0  # Unknown areas to index 0 (grey)
    display_map[known_map == 1] = 1   # Free space to index 1 (white)
    display_map[known_map == 0] = 2   # Obstacles to index 2 (black)
    ax.imshow(display_map, cmap=cmap_known, origin='lower')

    # Plot the vine robot if it has positions
    if len(vine_robot['positions']) > 1:
        vine_positions = np.array(vine_robot['positions'])
        ax.plot(vine_positions[:, 1], vine_positions[:, 0], color='darkgreen', linewidth=5, zorder=2)

    # Plot all robots
    for robot in robots:
        x, y = robot['position']
        orientation = robot['orientation']

        # Plot the robot circle
        ax.scatter(y, x, s=200, c='blue', edgecolors='black', zorder=3)

        # Triangle to indicate the robot's orientation
        vertices = get_triangle_vertices(x, y, orientation)
        triangle = plt.Polygon(vertices, color='red', ec='black', lw=1, alpha=0.7, zorder=4)
        ax.add_patch(triangle)

    # Highlight sensed cone points
    for cone_points in cone_points_list:
        if cone_points:
            cone_x, cone_y = zip(*cone_points)
            ax.scatter(cone_y, cone_x, c='orange', s=20, alpha=0.5, zorder=1)

    ax.set_aspect('equal', adjustable='box')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Robots' Known Map")

def plot_known_heat_map(known_heat_map, ax):
    """Plot the heat map that robots have discovered."""
    ax.clear()

    # Create a custom colormap for the known heat map
    cmap_heat = plt.cm.Reds
    cmap_heat.set_bad(color='grey')  # Unknown areas will be grey

    # Mask unknown values (-1)
    masked_heat_map = np.ma.masked_where(known_heat_map == -1, known_heat_map)

    ax.imshow(masked_heat_map, cmap=cmap_heat, origin='lower')

    ax.set_aspect('equal', adjustable='box')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Robots' Known Heat Map")

def generate_heat_map(grid_shape, heat_source_position):
    """Generate a heat map centered at the heat source position."""
    x_center, y_center = heat_source_position
    x = np.arange(0, grid_shape[0])
    y = np.arange(0, grid_shape[1])
    X, Y = np.meshgrid(y, x)  # Note: x and y are swapped for meshgrid
    distance = np.sqrt((X - y_center) ** 2 + (Y - x_center) ** 2)

    # Gaussian distribution for heat intensity
    sigma = max(grid_shape) / 5  # Adjust the spread of the heat
    heat_intensity = np.exp(-distance ** 2 / (2 * sigma ** 2))

    # Normalize heat intensity to range [0, 1]
    heat_intensity = heat_intensity / np.max(heat_intensity)

    # Mask out obstacles
    heat_intensity = np.ma.array(heat_intensity)

    return heat_intensity
