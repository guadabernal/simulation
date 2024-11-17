# main.py

import sys  # Import sys to allow exiting the program
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.gridspec import GridSpec  # Import GridSpec for dynamic subplot management

# Import functions from the modules
from map_utils import (
    generate_floor_plan,
    plot_floor_plan,
    plot_robot_view,
    plot_known_heat_map  # Function to plot the known heat map
)
from robot_utils import move_robot, sense_environment, is_position_occupied
from vine_robot_utils import move_vine_robot

def main():
    grid_size = (50, 50)  # Define the size of the grid

    # Define the walls/rooms you want to add
    walls = [
        (5, 5, 10, 2),    # Wall starting at (5,5) with width 10 and height 2
        (10, 15, 2, 10),  # Wall starting at (10,15) with width 2 and height 10
        (20, 5, 2, 30),   # Wall starting at (20,5) with width 2 and height 30
        (30, 25, 15, 2),  # Wall starting at (30,25) with width 15 and height 2
        (40, 10, 2, 15),  # Wall starting at (40,10) with width 2 and height 15
        # Add more walls as needed
    ]

    floor_plan = generate_floor_plan(grid_size, walls)

    # Initialize known map (unknown: -1)
    known_map = -1 * np.ones(grid_size)

    # Initialize known heat map (unknown: -1)
    known_heat_map = -1 * np.ones(grid_size)

    # Initialize list of robots and vine robot
    robots = []
    vine_robot = {'positions': [], 'active': False, 'orientation': None}

    # Initialize heat map variables
    heat_map_enabled = [False]       # Flag to indicate if heat map is enabled
    adding_heat_source = [False]     # Flag to indicate when adding heat source
    heat_source_position = [None]    # To store the heat source position

    plt.ion()  # Turn on interactive mode

    # Create a figure with GridSpec for dynamic subplot management
    fig = plt.figure(figsize=(12, 6))
    gs = GridSpec(1, 2, figure=fig)

    # Initial axes (two subplots)
    ax_floor_plan = fig.add_subplot(gs[0, 0])
    ax_robot_view = fig.add_subplot(gs[0, 1])

    axes = [ax_floor_plan, ax_robot_view]  # List to hold the axes

    # Initialize pause duration
    pause_duration = [0.1]  # Use a mutable object to allow modification within nested functions

    simulation_running = [False]  # Flag to control the simulation loop
    adding_robot = [False]       # Flag to indicate when adding a robot
    adding_vine_robot_stage = [0]  # 0: not adding, 1: waiting for start point, 2: waiting for orientation point
    step = 0  # Initialize simulation step

    # Define callback functions for the buttons
    def speed_up(event):
        if pause_duration[0] > 0.01:
            pause_duration[0] /= 2  # Speed up by halving the pause duration
            print(f"Speed increased. Current pause duration: {pause_duration[0]:.4f} seconds")

    def slow_down(event):
        pause_duration[0] *= 2  # Slow down by doubling the pause duration
        print(f"Speed decreased. Current pause duration: {pause_duration[0]:.4f} seconds")

    def start_simulation(event):
        if robots or vine_robot['positions']:
            simulation_running[0] = True
            print("Simulation started")
            start_button.ax.set_visible(False)
            plt.draw()
        else:
            print("Please add at least one robot or the vine robot before starting the simulation.")

    def add_robot(event):
        adding_robot[0] = True
        adding_vine_robot_stage[0] = 0
        adding_heat_source[0] = False
        print("Click on the map to place a robot.")

    def add_vine_robot(event):
        adding_vine_robot_stage[0] = 1
        adding_robot[0] = False
        adding_heat_source[0] = False
        print("Click on the map to place the vine robot's starting point.")

    def add_heat_map(event):
        adding_heat_source[0] = True
        adding_robot[0] = False
        adding_vine_robot_stage[0] = 0
        print("Click on the map to place the heat source.")

    def drop_rescue_roller(event):
        if len(vine_robot['positions']) > 0:
            # Get the tip of the vine robot
            tip_x, tip_y = vine_robot['positions'][-1]
            # Place the rescue robot a small distance away in the direction of the vine robot's orientation
            offset_distance = 2
            orientation = vine_robot['orientation']
            new_x = tip_x + offset_distance * np.cos(orientation)
            new_y = tip_y + offset_distance * np.sin(orientation)
            new_position = (new_x, new_y)
            int_x, int_y = int(round(new_position[0])), int(round(new_position[1]))
            if (
                0 <= int_x < floor_plan.shape[0]
                and 0 <= int_y < floor_plan.shape[1]
                and floor_plan[int_x, int_y] == 1
                and not is_position_occupied(new_position, None, robots)
            ):
                # Assign a random initial orientation
                orientation = np.random.uniform(0, 2 * np.pi)
                robot = {
                    'position': new_position,
                    'orientation': orientation
                }
                robots.append(robot)
                print(f"RESCUE Roller deployed at ({int_x}, {int_y}) with orientation {orientation:.2f} radians")
            else:
                print("Cannot deploy RESCUE Roller at this position. It may be blocked or occupied.")
        else:
            print("Vine robot has not been placed or has not moved yet.")

    # Event handler to set robot positions, vine robot, or heat source
    def on_click(event):
        if event.inaxes == axes[0]:
            ix, iy = event.xdata, event.ydata
            int_x, int_y = int(round(iy)), int(round(ix))

            # Check if the position is within the floor and not a wall
            if 0 <= int_x < floor_plan.shape[0] and 0 <= int_y < floor_plan.shape[1]:
                if floor_plan[int_x, int_y] == 1 and not is_position_occupied((iy, ix), None, robots):
                    if adding_robot[0]:
                        orientation = np.random.uniform(0, 2 * np.pi)  # Random initial orientation
                        robot = {
                            'position': (iy, ix),
                            'orientation': orientation
                        }
                        robots.append(robot)
                        plot_floor_plan(floor_plan, robots, vine_robot, axes[0],
                                        heat_map_enabled[0], heat_source_position[0])
                        plot_robot_view(known_map, robots, vine_robot, [], axes[1])
                        if heat_map_enabled[0] and len(axes) == 3:
                            plot_known_heat_map(known_heat_map, axes[2])
                        plt.draw()
                        print(f"Robot added at ({int_x}, {int_y}) with orientation {orientation:.2f} radians")
                        adding_robot[0] = False  # Reset the flag
                    elif adding_vine_robot_stage[0] == 1:
                        # First click: Set starting position
                        vine_robot['positions'] = [(iy, ix)]
                        vine_robot['active'] = False  # Not active until orientation is set
                        adding_vine_robot_stage[0] = 2  # Move to next stage
                        print("Click on the map to set the vine robot's orientation.")
                    elif adding_vine_robot_stage[0] == 2:
                        # Second click: Set orientation
                        start_x, start_y = vine_robot['positions'][0]
                        end_x, end_y = iy, ix
                        dx = end_x - start_x
                        dy = end_y - start_y
                        orientation = np.arctan2(dy, dx)
                        vine_robot['orientation'] = orientation
                        vine_robot['active'] = True  # Now the vine robot can start moving
                        adding_vine_robot_stage[0] = 0  # Reset the flag
                        plot_floor_plan(floor_plan, robots, vine_robot, axes[0],
                                        heat_map_enabled[0], heat_source_position[0])
                        plot_robot_view(known_map, robots, vine_robot, [], axes[1])
                        if heat_map_enabled[0] and len(axes) == 3:
                            plot_known_heat_map(known_heat_map, axes[2])
                        plt.draw()
                        print(f"Vine robot orientation set. It will move at angle {orientation:.2f} radians.")
                    elif adding_heat_source[0]:
                        # Set heat source position
                        heat_source_position[0] = (iy, ix)
                        heat_map_enabled[0] = True
                        adding_heat_source[0] = False
                        # Adjust the figure to add the third plot
                        add_third_plot()
                        plot_floor_plan(floor_plan, robots, vine_robot, axes[0],
                                        heat_map_enabled[0], heat_source_position[0])
                        plot_known_heat_map(known_heat_map, axes[2])  # Plot the known heat map
                        plt.draw()
                        print(f"Heat source added at ({int_x}, {int_y}).")
                    else:
                        # Do nothing if not adding anything
                        pass
                else:
                    print("Cannot place on a wall or occupied space. Please select a free space.")
            else:
                print("Click within the map area to set the position.")

    # Function to add the third plot dynamically
    def add_third_plot():
        nonlocal axes, gs
        if len(axes) < 3:
            # Remove existing axes
            for ax in axes:
                ax.remove()
            # Update GridSpec to have 1 row, 3 columns
            gs = GridSpec(1, 3, figure=fig)
            # Create new subplots
            ax_floor_plan = fig.add_subplot(gs[0, 0])
            ax_robot_view = fig.add_subplot(gs[0, 1])
            ax_heat_map = fig.add_subplot(gs[0, 2])
            # Update the axes list
            axes.clear()
            axes.extend([ax_floor_plan, ax_robot_view, ax_heat_map])
            # Re-plot the existing data
            plot_floor_plan(floor_plan, robots, vine_robot, axes[0],
                            heat_map_enabled[0], heat_source_position[0])
            plot_robot_view(known_map, robots, vine_robot, [], axes[1])
            plot_known_heat_map(known_heat_map, axes[2])
            plt.draw()

    # Function to reset the simulation
    def reset_simulation(event):
        nonlocal known_map, known_heat_map, robots, vine_robot, heat_map_enabled, \
            adding_heat_source, heat_source_position, simulation_running, \
            adding_robot, adding_vine_robot_stage, step, axes, gs
        # Reset variables
        known_map = -1 * np.ones(grid_size)
        known_heat_map = -1 * np.ones(grid_size)
        robots.clear()
        vine_robot = {'positions': [], 'active': False, 'orientation': None}
        heat_map_enabled[0] = False
        adding_heat_source[0] = False
        heat_source_position[0] = None
        simulation_running[0] = False
        adding_robot[0] = False
        adding_vine_robot_stage[0] = 0
        step = 0

        # Clear and reinitialize the axes
        for ax in axes:
            ax.clear()

        # Remove the third plot if heat map was enabled
        if len(axes) == 3:
            axes[2].remove()
            axes.pop(2)
            # Update GridSpec to have 1 row, 2 columns
            gs = GridSpec(1, 2, figure=fig)
            # Reassign the first two axes
            axes[0] = fig.add_subplot(gs[0, 0])
            axes[1] = fig.add_subplot(gs[0, 1])

        # Re-plot the initial floor plan and robot view
        plot_floor_plan(floor_plan, robots, vine_robot, axes[0],
                        heat_map_enabled[0], heat_source_position[0])
        plot_robot_view(known_map, robots, vine_robot, [], axes[1])

        # Make the Start button visible again
        start_button.ax.set_visible(True)
        plt.draw()
        print("Simulation reset.")

    # Function to kill the simulation and exit the program
    def kill_simulation(event):
        plt.close(fig)
        sys.exit()

    # Add buttons to the figure
    button_width = 0.08
    button_height = 0.04
    button_spacing = 0.01
    x_start = 0.05

    ax_speed_up = plt.axes([x_start + 0 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_slow_down = plt.axes([x_start + 1 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_add_bot = plt.axes([x_start + 2 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_add_vine = plt.axes([x_start + 3 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_drop_rescue = plt.axes([x_start + 4 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_heat_map = plt.axes([x_start + 5 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_start = plt.axes([x_start + 6 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_reset = plt.axes([x_start + 7 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_kill = plt.axes([x_start + 8 * (button_width + button_spacing), 0.02, button_width, button_height])

    btn_speed_up = Button(ax_speed_up, 'Speed Up')
    btn_slow_down = Button(ax_slow_down, 'Slow Down')
    add_bot_button = Button(ax_add_bot, 'Add Bot')
    add_vine_button = Button(ax_add_vine, 'Vine Robot')
    drop_rescue_button = Button(ax_drop_rescue, 'Drop RR')
    heat_map_button = Button(ax_heat_map, 'Heat Map')
    start_button = Button(ax_start, 'Start')
    reset_button = Button(ax_reset, 'Reset')
    kill_button = Button(ax_kill, 'Kill')

    btn_speed_up.on_clicked(speed_up)
    btn_slow_down.on_clicked(slow_down)
    add_bot_button.on_clicked(add_robot)
    add_vine_button.on_clicked(add_vine_robot)
    drop_rescue_button.on_clicked(drop_rescue_roller)
    heat_map_button.on_clicked(add_heat_map)
    start_button.on_clicked(start_simulation)
    reset_button.on_clicked(reset_simulation)
    kill_button.on_clicked(kill_simulation)

    # Connect the click event handler
    cid = fig.canvas.mpl_connect('button_press_event', on_click)

    # Initial plot to display the floor plan
    plot_floor_plan(floor_plan, robots, vine_robot, axes[0],
                    heat_map_enabled[0], heat_source_position[0])
    plot_robot_view(known_map, robots, vine_robot, [], axes[1])
    plt.draw()

    # Main simulation loop
    max_steps = 1000  # Set a maximum number of steps
    while step < max_steps:
        if simulation_running[0]:
            cone_points_list = []
            for robot in robots:
                known_map, cone_points, known_heat_map = sense_environment(
                    robot, floor_plan, known_map, heat_map_enabled[0], heat_source_position[0], known_heat_map)
                cone_points_list.append(cone_points)
            plot_floor_plan(floor_plan, robots, vine_robot, axes[0],
                            heat_map_enabled[0], heat_source_position[0])
            plot_robot_view(known_map, robots, vine_robot, cone_points_list, axes[1])
            if heat_map_enabled[0] and len(axes) == 3:
                plot_known_heat_map(known_heat_map, axes[2])
            for robot in robots:
                move_robot(robot, robots, floor_plan)
            if vine_robot['active']:
                move_vine_robot(vine_robot, floor_plan)
            plt.pause(pause_duration[0])
            step += 1
        else:
            plt.pause(0.1)  # Wait before checking again to reduce CPU usage

    plt.ioff()
    plt.show()

if __name__ == "__main__":
    main()
