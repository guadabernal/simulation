# gui_utils.py
import sys
import matplotlib.pyplot as plt  # Import plt if not already done

def speed_up(event, pause_duration):
    if pause_duration[0] > 0.01:
        pause_duration[0] /= 2
        print(f"Speed increased. Current pause duration: {pause_duration[0]:.4f} seconds")

def slow_down(event, pause_duration):
    pause_duration[0] *= 2
    print(f"Speed decreased. Current pause duration: {pause_duration[0]:.4f} seconds")

def start_simulation(event, robots, vine_robot, simulation_running, start_button):
    if robots or vine_robot['positions']:
        simulation_running[0] = True
        print("Simulation started")
        start_button.ax.set_visible(False)
        plt.draw()
    else:
        print("Add at least one robot or vine robot before starting simulation.")

def add_robot(event, adding_robot, adding_vine_robot_stage, adding_heat_source):
    adding_robot[0] = True
    adding_vine_robot_stage[0] = 0
    adding_heat_source[0] = False
    print("Click on map to place a robot.")

def add_vine_robot(event, adding_vine_robot_stage, adding_robot, adding_heat_source):
    adding_vine_robot_stage[0] = 1
    adding_robot[0] = False
    adding_heat_source[0] = False
    print("Click on map to place vine robot's starting point.")

def kill_simulation(event, fig):
    plt.close(fig)
    sys.exit()

def add_heat_map(event, adding_heat_source, adding_robot, adding_vine_robot_stage):
    adding_heat_source[0] = True
    adding_robot[0] = False
    adding_vine_robot_stage[0] = 0
    print("Click on the map to place the heat source.")
    