import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

# Import functions from the modules
from map_utils import (
    generate_floor_plan,
    plot_floor_plan,
    plot_robot_view,
)
from robot_utils import move_robot, sense_environment, is_position_occupied
from vine_robot_utils import move_vine_robot

def main():
    grid_size = (100, 100)  # Define the size of the grid

    # Define the walls/rooms you want to add
    walls = [
        (90, 0, 30, 2),
        (70, 40, 2, 30),
        (70, 40, 20, 2),

        (50, 50, 10, 10),   # square

        (10, 70, 25, 2),
        (10, 70, 2, 20),


        (20, 20, 15, 3),
        (40, 10, 2, 25),
        (5, 5, 10, 2),
        (80, 80, 8, 4),
        (25, 90, 20, 3),
        (60, 20, 3, 20),
    ]

    floor_plan = generate_floor_plan(grid_size, walls)

    # Initialize known map (unknown: -1)
    known_map = -1 * np.ones(grid_size)

    # Initialize list of robots and vine robot
    robots = []
    vine_robot = {'positions': [], 'active': False, 'orientation': None}

    plt.ion()  # Turn on interactive mode
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))

    # Initialize pause duration
    pause_duration = [0.1]  # Use a mutable object to allow modification within nested functions

    simulation_running = [False]  # Flag to control the simulation loop
    adding_robot = [False]       # Flag to indicate when adding a robot
    adding_vine_robot_stage = [0]  # 0: not adding, 1: waiting for start point, 2: waiting for orientation point

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
        print("Click on the map to place a robot.")

    def add_vine_robot(event):
        adding_vine_robot_stage[0] = 1
        adding_robot[0] = False
        print("Click on the map to place the vine robot's starting point.")

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

    # Event handler to set robot positions or vine robot
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
                        plot_floor_plan(floor_plan, robots, vine_robot, axes[0])
                        plot_robot_view(known_map, robots, vine_robot, [], axes[1])
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
                        plot_floor_plan(floor_plan, robots, vine_robot, axes[0])
                        plot_robot_view(known_map, robots, vine_robot, [], axes[1])
                        plt.draw()
                        print(f"Vine robot orientation set. It will move at angle {orientation:.2f} radians.")
                    else:
                        # Do nothing if not adding robots
                        pass
                else:
                    print("Cannot place on a wall or occupied space. Please select a free space.")
            else:
                print("Click within the map area to set the position.")

    # Add buttons to the figure
    ax_speed_up = plt.axes([0.4, 0.02, 0.1, 0.04])  # x-position, y-position, width, height
    ax_slow_down = plt.axes([0.51, 0.02, 0.1, 0.04])
    ax_add_bot = plt.axes([0.62, 0.02, 0.1, 0.04])
    ax_add_vine = plt.axes([0.73, 0.02, 0.1, 0.04])
    ax_drop_rescue = plt.axes([0.84, 0.02, 0.1, 0.04])
    ax_start = plt.axes([0.95, 0.02, 0.05, 0.04])

    btn_speed_up = Button(ax_speed_up, 'Speed Up')
    btn_slow_down = Button(ax_slow_down, 'Slow Down')
    add_bot_button = Button(ax_add_bot, 'Add Bot')
    add_vine_button = Button(ax_add_vine, 'Vine Robot')
    drop_rescue_button = Button(ax_drop_rescue, 'Drop RESCUE Roller')
    start_button = Button(ax_start, 'Start')

    btn_speed_up.on_clicked(speed_up)
    btn_slow_down.on_clicked(slow_down)
    add_bot_button.on_clicked(add_robot)
    add_vine_button.on_clicked(add_vine_robot)
    drop_rescue_button.on_clicked(drop_rescue_roller)
    start_button.on_clicked(start_simulation)

    # Connect the click event handler
    cid = fig.canvas.mpl_connect('button_press_event', on_click)

    # Initial plot to display the floor plan
    plot_floor_plan(floor_plan, robots, vine_robot, axes[0])
    plot_robot_view(known_map, robots, vine_robot, [], axes[1])
    plt.draw()

    # Main simulation loop
    step = 0
    max_steps = 1000  # Set a maximum number of steps
    while step < max_steps:
        if simulation_running[0]:
            cone_points_list = []
            for robot in robots:
                known_map, cone_points = sense_environment(robot, floor_plan, known_map)
                cone_points_list.append(cone_points)
            plot_floor_plan(floor_plan, robots, vine_robot, axes[0])
            plot_robot_view(known_map, robots, vine_robot, cone_points_list, axes[1])
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