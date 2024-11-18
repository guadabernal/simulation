import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors

def generate_floor_plan(grid_size, walls):
    floor_plan = np.ones(grid_size)

    # walls around the perimeter
    floor_plan[0, :] = 0
    floor_plan[-1, :] = 0
    floor_plan[:, 0] = 0
    floor_plan[:, -1] = 0

    # predefined internal walls
    for wall in walls:
        x_start, y_start, width, height = wall
        floor_plan[x_start:x_start + height, y_start:y_start + width] = 0

    return floor_plan

def get_triangle_vertices(x, y, orientation, size=0.7):
    tip_x = y + size * np.sin(orientation)
    tip_y = x + size * np.cos(orientation)

    base_angle = orientation + np.pi
    base_left_x = y + (size / 2) * np.sin(base_angle + np.pi / 6)
    base_left_y = x + (size / 2) * np.cos(base_angle + np.pi / 6)
    base_right_x = y + (size / 2) * np.sin(base_angle - np.pi / 6)
    base_right_y = x + (size / 2) * np.cos(base_angle - np.pi / 6)

    return [(tip_x, tip_y), (base_left_x, base_left_y), (base_right_x, base_right_y)]

def get_marker_size(ax, robot_diameter):
    # Get the transformation from data to display
    fig = ax.get_figure()
    dpi = fig.dpi
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width_inch = bbox.width
    height_inch = bbox.height

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_range = xlim[1] - xlim[0]
    y_range = ylim[1] - ylim[0]

    # Compute pixels per data unit
    x_pixels_per_unit = (width_inch * dpi) / x_range
    y_pixels_per_unit = (height_inch * dpi) / y_range

    # Since markers are circular, we'll take the average
    pixels_per_unit = (x_pixels_per_unit + y_pixels_per_unit) / 2

    # Diameter in pixels
    diameter_in_pixels = robot_diameter * pixels_per_unit

    # Matplotlib's scatter marker size 's' is in points squared
    # There are 72 points per inch
    diameter_in_points = diameter_in_pixels * 72 / dpi
    area_in_points_squared = (diameter_in_points / 2) ** 2 * np.pi  # Area of circle

    return area_in_points_squared

def plot_floor_plan(floor_plan, robots, vine_robot, ax, robot_diameter, heat_map_enabled=False, heat_source_position=None):
    ax.clear()
    cmap_floor = colors.ListedColormap(['black', 'white'])  # 0: black (obstacle), 1: white (free space)
    ax.imshow(floor_plan, cmap=cmap_floor, origin='lower')

    if heat_map_enabled and heat_source_position is not None:
        heat_map = generate_heat_map(floor_plan.shape, heat_source_position)
        ax.imshow(heat_map, cmap='Reds', origin='lower', alpha=0.5)

    if len(vine_robot['positions']) > 1:
        vine_positions = np.array(vine_robot['positions'])
        ax.plot(vine_positions[:, 1], vine_positions[:, 0], color='darkgreen', linewidth=5, zorder=2)

    # Calculate marker size based on robot diameter
    marker_size = get_marker_size(ax, robot_diameter)

    for robot in robots:
        x, y = robot['position']
        orientation = robot['orientation']

        # plot robot circle
        ax.scatter(y, x, s=marker_size, c='blue', edgecolors='black', zorder=3)

        # triangle indicates robot orientation
        vertices = get_triangle_vertices(x, y, orientation, size=robot_diameter/2)
        triangle = plt.Polygon(vertices, color='red', ec='black', lw=1, alpha=0.7, zorder=4)
        ax.add_patch(triangle)

    ax.set_aspect('equal', adjustable='box')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Floor Plan")

def plot_robot_view(known_map, robots, vine_robot, cone_points_list, ax, robot_diameter):
    ax.clear()
    cmap_known = colors.ListedColormap(['grey', 'white', 'black'])  # 0: grey (unknown), 1: white (free), 2: black (obstacle)
    display_map = np.full_like(known_map, fill_value=0)  # initialize with unknown (grey)

    # Map known_map values to display indices
    display_map[known_map == -1] = 0  # Unknown areas to index 0 (grey)
    display_map[known_map == 1] = 1   # Free space to index 1 (white)
    display_map[known_map == 0] = 2   # Obstacles to index 2 (black)
    ax.imshow(display_map, cmap=cmap_known, origin='lower')

    if len(vine_robot['positions']) > 1:
        vine_positions = np.array(vine_robot['positions'])
        ax.plot(vine_positions[:, 1], vine_positions[:, 0], color='darkgreen', linewidth=5, zorder=2)

    # Calculate marker size based on robot diameter
    marker_size = get_marker_size(ax, robot_diameter)

    for robot in robots:
        x, y = robot['position']
        orientation = robot['orientation']
        ax.scatter(y, x, s=marker_size, c='blue', edgecolors='black', zorder=3)
        vertices = get_triangle_vertices(x, y, orientation, size=robot_diameter/2)
        triangle = plt.Polygon(vertices, color='red', ec='black', lw=1, alpha=0.7, zorder=4)
        ax.add_patch(triangle)

    for cone_points in cone_points_list:
        if cone_points:
            cone_x, cone_y = zip(*cone_points)
            ax.scatter(cone_y, cone_x, c='orange', s=20, alpha=0.5, zorder=1)

    ax.set_aspect('equal', adjustable='box')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Robots' Known Map")

def plot_known_heat_map(known_heat_map, ax):
    ax.clear()
    cmap_heat = plt.cm.Reds
    cmap_heat.set_bad(color='grey')  # Unknown areas will be grey
    masked_heat_map = np.ma.masked_where(known_heat_map == -1, known_heat_map)

    ax.imshow(masked_heat_map, cmap=cmap_heat, origin='lower')
    ax.set_aspect('equal', adjustable='box')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Robots' Known Heat Map")

def generate_heat_map(grid_shape, heat_source_position):
    x_center, y_center = heat_source_position
    x = np.arange(0, grid_shape[0])
    y = np.arange(0, grid_shape[1])
    X, Y = np.meshgrid(y, x)  # x and y swapped for meshgrid
    distance = np.sqrt((X - y_center) ** 2 + (Y - x_center) ** 2)

    # --> Gaussian distribution for heat intensity <--
    sigma = max(grid_shape) / 5  # spread of the heat
    heat_intensity = np.exp(-distance ** 2 / (2 * sigma ** 2))

    # normalize heat intensity to range [0, 1]
    heat_intensity = heat_intensity / np.max(heat_intensity)
    heat_intensity = np.ma.array(heat_intensity)

    return heat_intensity
