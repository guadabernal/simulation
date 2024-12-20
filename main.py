import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons
from matplotlib.gridspec import GridSpec
import functools

from map_utils import generate_floor_plan, plot_floor_plan, plot_robot_view, plot_known_heat_map
from robot_utils import move_robot, sense_environment, check_collision
from vine_robot_utils import move_vine_robot

from gui_utils import speed_up, slow_down, start_simulation, add_vine_robot, kill_simulation, add_heat_map


def main():
    grid_size = (210, 300)
    robot_diameter = 1.6  # Define robot diameter

    # x,y,width,height
    # walls = [ (5, 5, 10, 2),  
    #           (10, 15, 2, 10),
    #           (20, 5, 2, 30), 
    #           (30, 25, 15, 2),
    #           (40, 10, 2, 15),
    #         ]

    # gaps between walls = 10 = 36 inches => RR 2.something ish inches so 0.8 diameter

    walls = [       # BORDERS
                (0,     0,     4,    210),
                (296,   0,     4,    210),

                (0,     0,     300,  4),  
                (0,     206,   300,  4),  
                
                    # TOP
                (68,    164,   4,    44),
                (152,   164,   4,    44),

                
                (2,     160,   38,   4),
                (60,    160,   66,   4),
                (152,   160,   16,   4),
                (190,   160,   56,   4),

                    # BOTTOM
                (72,    4,     4,    42),
                (118,   2,     4,    42),
                (188,   4,     4,    10),
                (188,   26,    4,    18),

                (118,   42,    74,   4),
                (2,     42,    38,   4), 
                (60,    42,    14,   4),

                    # MIDDLE
                (148,   70,    4,    60),
                (74,    70,    4,    12),
                (74,    98,    4,    16),
                (74,    122,   4,    12),
                (204,   72,    4,    10),
                (204,   94,    4,    18),
                (204,   124,   4,    8),
                
                (2,     104,   74,   4),
                (2,     130,   108,  4),
                (2,     68,    108,  4),
                (130,   68,    82,   4),
                (130,   130,   78,   4),
                (150,   102,   54,   4),
                    
                    # RIGHT
                (244,   34,    4,    104),
                (244,   150,   4,    58),

                (244,   118,   56,   4),
                (244,   32,    26,   4),
                (290,   32,    14,   4),
        ]



    floor_plan = generate_floor_plan(grid_size, walls)
    
    known_map = -1 * np.ones(grid_size)
    known_heat_map = -1 * np.ones(grid_size)

    robots = []
    vine_robot = {'positions': [], 'active': False, 'orientation': None}

    heat_map_enabled = [False]
    adding_heat_source = [False]
    heat_source_position = [None]
    simulation_running = [False]
    adding_robot = [False]

    sensor_options = ['Cone Vision', 'Heat Sensor']
    selecting_sensors = [False]
    sensor_selections = {}
    sensor_widgets = {}
    adding_rr = [False]

    plt.ion()

    # GridSpec dynamic subplot
    fig = plt.figure(figsize=(12, 6))
    gs = GridSpec(1, 2, figure=fig)

    ax_floor_plan = fig.add_subplot(gs[0, 0])
    ax_robot_view = fig.add_subplot(gs[0, 1])
    axes = [ax_floor_plan, ax_robot_view]

    pause_duration = [0.1]
    adding_vine_robot_stage = [0]  # 0: not adding 1: need start point 2: need orientation point
    step = 0

    def drop_rescue_roller(event):
        if len(vine_robot['positions']) > 0:
            if selecting_sensors[0]:
                print("Please complete the current sensor selection first.")
                return
            adding_rr[0] = True
            start_sensor_selection()
        else:
            print("Vine robot has not been placed or has not moved yet.")

    def create_robot_after_sensor_selection():
        tip_x, tip_y = vine_robot['positions'][-1]
        offset_distance = 2
        orientation = vine_robot['orientation']
        new_x = tip_x + offset_distance * np.cos(orientation)
        new_y = tip_y + offset_distance * np.sin(orientation)
        new_position = (new_x, new_y)
        int_x, int_y = int(round(new_position[0])), int(round(new_position[1]))
        
        if ( 0 <= int_x < floor_plan.shape[0]
            and 0 <= int_y < floor_plan.shape[1]
            and floor_plan[int_x, int_y] == 1
            and not check_collision(new_position, None, robots, floor_plan, robot_diameter)):
            
            orientation = np.random.uniform(0, 2 * np.pi)
            robot = {
                'position': new_position,
                'orientation': orientation,
                'sensors': sensor_selections.copy(),
                'distance_traveled': 0.0
            }
            robots.append(robot)
            print(f"RESCUE Roller deployed at ({int_x}, {int_y}) with orientation {orientation:.2f} radians")
            adding_rr[0] = False
        else:
            print("Cannot deploy RESCUE Roller at this position. It may be blocked or occupied.")
            adding_rr[0] = False

    def start_sensor_selection():
        selecting_sensors[0] = True
        sensor_selections.clear()
        
        # Create axes for the checkbuttons
        check_ax = plt.axes([0.85, 0.5, 0.1, 0.15])  # Adjust position as needed
        sensor_check = CheckButtons(check_ax, sensor_options, [True]*len(sensor_options))
        
        sensor_widgets['check'] = sensor_check
        sensor_widgets['check_ax'] = check_ax
        
        # Create OK button
        ok_ax = plt.axes([0.85, 0.45, 0.1, 0.04])
        ok_button = Button(ok_ax, 'OK')
        sensor_widgets['ok_button'] = ok_button
        sensor_widgets['ok_ax'] = ok_ax
        
        # Store connection IDs
        sensor_widgets['ok_button_cid'] = None
        sensor_widgets['sensor_check_cid'] = None

        # Define callback for OK button
        def on_ok_clicked(event):
            # Read the selections
            selections = sensor_check.get_status()
            for option, selected in zip(sensor_options, selections):
                sensor_selections[option] = selected
            # Clean up the buttons
            # Disconnect event handlers
            ok_button.disconnect(sensor_widgets['ok_button_cid'])
            sensor_check.disconnect(sensor_widgets['sensor_check_cid'])
            # Remove the widgets
            sensor_check.ax.remove()
            ok_button.ax.remove()
            fig.canvas.draw_idle()
            
            selecting_sensors[0] = False
            print("Sensor selection completed.")
            print(f"Selected sensors: {sensor_selections}")
            # Now proceed to place the robot (if adding_robot[0] is True)
            if adding_robot[0]:
                print("Click on map to place the robot.")
            elif adding_rr[0]:
                # For Drop RR, proceed to create the robot
                create_robot_after_sensor_selection()
            # Delete widget references
            del sensor_widgets['check']
            del sensor_widgets['ok_button']
        
        # Connect the event handlers and store the connection IDs
        sensor_widgets['ok_button_cid'] = ok_button.on_clicked(on_ok_clicked)
        sensor_widgets['sensor_check_cid'] = sensor_check.on_clicked(lambda label: None)
        
        plt.draw()

    def on_click(event):
        if event.inaxes == axes[0]:
            if selecting_sensors[0]:
                print("Please complete sensor selection first.")
                return
            ix, iy = event.xdata, event.ydata
            int_x, int_y = int(round(iy)), int(round(ix))

            # check not in wall
            if 0 <= int_x < floor_plan.shape[0] and 0 <= int_y < floor_plan.shape[1]:
                if floor_plan[int_x, int_y] == 1 and not check_collision((iy, ix), None, robots, floor_plan, robot_diameter):
                    
                    if adding_robot[0]:
                        orientation = np.random.uniform(0, 2 * np.pi)
                        robot = {
                            'position': (iy, ix),
                            'orientation': orientation,
                            'sensors': sensor_selections.copy(),
                            'distance_traveled': 0.0
                        }
                        robots.append(robot)
                        
                        plot_floor_plan(floor_plan, robots, vine_robot, axes[0], robot_diameter, heat_map_enabled[0], heat_source_position[0])
                        plot_robot_view(known_map, robots, vine_robot, [], axes[1], robot_diameter)

                        if heat_map_enabled[0] and len(axes) == 3:
                            plot_known_heat_map(known_heat_map, axes[2])
                        plt.draw()
                        print(f"Robot added at ({int_x}, {int_y}) with orientation {orientation:.2f} radians")
                        adding_robot[0] = False
                    elif adding_vine_robot_stage[0] == 1:       # 1. set starting position
                        vine_robot['positions'] = [(iy, ix)]
                        vine_robot['active'] = False
                        adding_vine_robot_stage[0] = 2
                        print("Click on the map to set the vine robot's orientation.")
                    
                    elif adding_vine_robot_stage[0] == 2:       # 2. set orientation
                        start_x, start_y = vine_robot['positions'][0]
                        end_x, end_y = iy, ix
                        dx = end_x - start_x
                        dy = end_y - start_y
                        orientation = np.arctan2(dy, dx)
                        vine_robot['orientation'] = orientation
                        vine_robot['active'] = True
                        adding_vine_robot_stage[0] = 0
                        
                        plot_floor_plan(floor_plan, robots, vine_robot, axes[0], robot_diameter, heat_map_enabled[0], heat_source_position[0])
                        plot_robot_view(known_map, robots, vine_robot, [], axes[1], robot_diameter)
                        
                        if heat_map_enabled[0] and len(axes) == 3:
                            plot_known_heat_map(known_heat_map, axes[2])
                        plt.draw()
                        print(f"Vine robot orientation set. It will move at angle {orientation:.2f} radians.")
                    
                    elif adding_heat_source[0]:
                        heat_source_position[0] = (iy, ix)
                        heat_map_enabled[0] = True
                        adding_heat_source[0] = False
                        
                        add_third_plot()
                        plot_floor_plan(floor_plan, robots, vine_robot, axes[0], robot_diameter, heat_map_enabled[0], heat_source_position[0])
                        plot_known_heat_map(known_heat_map, axes[2])
                        plt.draw()
                        print(f"Heat source added at ({int_x}, {int_y}).")
                    else:
                        pass
                else:
                    print("Cannot place on a wall or occupied space. Please select a free space.")
            else:
                print("Click within the map area to set the position.")

    def add_third_plot():   # just for heat map
        nonlocal axes, gs
        if len(axes) < 3:
            for ax in axes:
                ax.remove()

            gs = GridSpec(1, 3, figure=fig)

            ax_floor_plan = fig.add_subplot(gs[0, 0])
            ax_robot_view = fig.add_subplot(gs[0, 1])
            ax_heat_map = fig.add_subplot(gs[0, 2])

            axes.clear()
            axes.extend([ax_floor_plan, ax_robot_view, ax_heat_map])

            plot_floor_plan(floor_plan, robots, vine_robot, axes[0], robot_diameter, heat_map_enabled[0], heat_source_position[0])
            plot_robot_view(known_map, robots, vine_robot, [], axes[1], robot_diameter)
            plot_known_heat_map(known_heat_map, axes[2])

            plt.draw()

    def reset_simulation(event):
        nonlocal known_map, known_heat_map, robots, vine_robot, heat_map_enabled, adding_heat_source, heat_source_position, simulation_running, adding_robot, adding_vine_robot_stage, step, axes, gs
        
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

        for ax in axes:
            ax.clear()

        if len(axes) == 3:
            axes[2].remove()
            axes.pop(2)
            gs = GridSpec(1, 2, figure=fig)
            axes[0] = fig.add_subplot(gs[0, 0])
            axes[1] = fig.add_subplot(gs[0, 1])

        plot_floor_plan(floor_plan, robots, vine_robot, axes[0], robot_diameter, heat_map_enabled[0], heat_source_position[0])
        plot_robot_view(known_map, robots, vine_robot, [], axes[1], robot_diameter)

        start_button.ax.set_visible(True)
        plt.draw()
        print("Simulation reset.")

    def add_robot(event, adding_robot, adding_vine_robot_stage, adding_heat_source):
        if selecting_sensors[0]:
            print("Please complete the current sensor selection first.")
            return
        adding_robot[0] = True
        adding_vine_robot_stage[0] = 0
        adding_heat_source[0] = False
        start_sensor_selection()

    button_width = 0.08
    button_height = 0.04
    button_spacing = 0.01
    x_start = 0.05

    ax_speed_up    = plt.axes([x_start + 0 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_slow_down   = plt.axes([x_start + 1 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_add_bot     = plt.axes([x_start + 2 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_add_vine    = plt.axes([x_start + 3 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_drop_rescue = plt.axes([x_start + 4 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_heat_map    = plt.axes([x_start + 5 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_start       = plt.axes([x_start + 6 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_reset       = plt.axes([x_start + 7 * (button_width + button_spacing), 0.02, button_width, button_height])
    ax_kill        = plt.axes([x_start + 8 * (button_width + button_spacing), 0.02, button_width, button_height])

    btn_speed_up        = Button(ax_speed_up,    'Speed Up')
    btn_slow_down       = Button(ax_slow_down,   'Slow Down')
    add_bot_button      = Button(ax_add_bot,     'Add Bot')
    add_vine_button     = Button(ax_add_vine,    'Vine Robot')
    drop_rescue_button  = Button(ax_drop_rescue, 'Drop RR')
    heat_map_button     = Button(ax_heat_map,    'Heat Map')
    start_button        = Button(ax_start,       'Start')
    reset_button        = Button(ax_reset,       'Reset')
    kill_button         = Button(ax_kill,        'Kill')

    # funcs I managed to pull out
    btn_speed_up.on_clicked(functools.partial(speed_up, pause_duration=pause_duration))
    btn_slow_down.on_clicked(functools.partial(slow_down, pause_duration=pause_duration))
    add_bot_button.on_clicked(functools.partial(add_robot, adding_robot=adding_robot, adding_vine_robot_stage=adding_vine_robot_stage, adding_heat_source=adding_heat_source))
    add_vine_button.on_clicked(functools.partial(add_vine_robot, adding_vine_robot_stage=adding_vine_robot_stage, adding_robot=adding_robot, adding_heat_source=adding_heat_source))
    start_button.on_clicked(functools.partial(start_simulation, robots=robots, vine_robot=vine_robot, simulation_running=simulation_running, start_button=start_button))
    kill_button.on_clicked(functools.partial(kill_simulation, fig=fig))
    heat_map_button.on_clicked(functools.partial(add_heat_map, adding_heat_source=adding_heat_source, adding_robot=adding_robot, adding_vine_robot_stage=adding_vine_robot_stage))

    # funcs that crash everything if i pull out
    drop_rescue_button.on_clicked(drop_rescue_roller)
    reset_button.on_clicked(reset_simulation)
    

    cid = fig.canvas.mpl_connect('button_press_event', on_click)

    plot_floor_plan(floor_plan, robots, vine_robot, axes[0], robot_diameter, heat_map_enabled[0], heat_source_position[0])
    plot_robot_view(known_map, robots, vine_robot, [], axes[1], robot_diameter)
    plt.draw()

    # ================================================================================================================================
    # Main Loop
    # ================================================================================================================================
    max_steps = 1000
    while step < max_steps:
        if simulation_running[0]:
            cone_points_list = []
            
            for robot in robots:
                known_map, cone_points, known_heat_map = sense_environment(robot, floor_plan, known_map, heat_map_enabled[0], heat_source_position[0], known_heat_map, robot_diameter)
                cone_points_list.append(cone_points)

            plot_floor_plan(floor_plan, robots, vine_robot, axes[0], robot_diameter, heat_map_enabled[0], heat_source_position[0])
            plot_robot_view(known_map, robots, vine_robot, cone_points_list, axes[1], robot_diameter)

            if heat_map_enabled[0] and len(axes) == 3:
                plot_known_heat_map(known_heat_map, axes[2])

            for robot in robots:
                move_robot(robot, robots, floor_plan, robot_diameter)

            if vine_robot['active']:
                move_vine_robot(vine_robot, floor_plan)
                
            plt.pause(pause_duration[0])
            step += 1
        else:
            plt.pause(0.1)

    plt.ioff()
    plt.show()

if __name__ == "__main__":
    main()