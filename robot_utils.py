import numpy as np

def is_position_occupied(position, current_robot, robots):
    for robot in robots:
        if robot is not current_robot:
            robot_pos = robot['position']
            if int(round(robot_pos[0])) == int(round(position[0])) and int(round(robot_pos[1])) == int(round(position[1])): return True
    return False

def move_robot(robot, robots, floor_plan):
    # todo: make this not dumb and random

    x, y = robot['position']
    orientation = robot['orientation']

    # rotate by a small rand angle
    random_angle = np.random.uniform(-np.pi / 18, np.pi / 18)
    orientation = (orientation + random_angle) % (2 * np.pi)
    robot['orientation'] = orientation

    # move forward in new orientation
    dx, dy = np.cos(orientation), np.sin(orientation)
    new_x = x + dx
    new_y = y + dy
    int_new_x, int_new_y = int(round(new_x)), int(round(new_y))

    # check if possible
    if ( 0 <= int_new_x < floor_plan.shape[0] and 0 <= int_new_y < floor_plan.shape[1]
        and floor_plan[int_new_x, int_new_y] == 1 and not is_position_occupied((new_x, new_y), robot, robots) ):
        robot['position'] = (new_x, new_y)
        return

    # else bumped into something so rotate
    rotation_angles = [np.pi / 2, -np.pi / 2, np.pi]
    np.random.shuffle(rotation_angles)

    for angle in rotation_angles:
        new_orientation = (orientation + angle) % (2 * np.pi)
        dx, dy = np.cos(new_orientation), np.sin(new_orientation)
        new_x = x + dx
        new_y = y + dy
        int_new_x, int_new_y = int(round(new_x)), int(round(new_y))

        if ( 0 <= int_new_x < floor_plan.shape[0] and 0 <= int_new_y < floor_plan.shape[1]
            and floor_plan[int_new_x, int_new_y] == 1 and not is_position_occupied((new_x, new_y), robot, robots) ):
            robot['orientation'] = new_orientation
            robot['position'] = (new_x, new_y)
            return

    # stay in place (wall issue might be fixed now though?)
    print(f"Robot at ({int(round(x))}, {int(round(y))}) cannot move and stays in place.")

def sense_environment(robot, floor_plan, known_map, heat_map_enabled, heat_source_position, known_heat_map):
    cone_length = 8
    cone_angle = np.pi / 4  # 45-degree cone
    x, y = robot['position']
    orientation = robot['orientation']

    cone_points = []
    for angle_offset in np.linspace(-cone_angle / 2, cone_angle / 2, 100):
        
        angle = orientation + angle_offset
        
        for distance in np.linspace(0.5, cone_length, 50):
            new_x = x + distance * np.cos(angle)
            new_y = y + distance * np.sin(angle)
            int_new_x = int(round(new_x))
            int_new_y = int(round(new_y))

            if 0 <= int_new_x < floor_plan.shape[0] and 0 <= int_new_y < floor_plan.shape[1]:
                if floor_plan[int_new_x, int_new_y] == 0:
                    
                    known_map[int_new_x, int_new_y] = 0
                    
                    if heat_map_enabled and heat_source_position is not None: 
                        known_heat_map[int_new_x, int_new_y] = get_heat_at_position((int_new_x, int_new_y), heat_source_position, floor_plan.shape)
                    
                    cone_points.append((new_x, new_y))
                    break

                known_map[int_new_x, int_new_y] = 1  # marks as free space

                if heat_map_enabled and heat_source_position is not None: 
                    known_heat_map[int_new_x, int_new_y] = get_heat_at_position((int_new_x, int_new_y), heat_source_position, floor_plan.shape)

                cone_points.append((new_x, new_y))

    int_x, int_y = int(round(x)), int(round(y))
    if heat_map_enabled and heat_source_position is not None:
        known_heat_map[int_x, int_y] = get_heat_at_position((int_x, int_y), heat_source_position, floor_plan.shape)

    return known_map, cone_points, known_heat_map

def get_heat_at_position(position, heat_source_position, grid_shape):
    x_pos, y_pos = position
    x_source, y_source = heat_source_position

    distance = np.sqrt((x_pos - x_source) ** 2 + (y_pos - y_source) ** 2)
    sigma = max(grid_shape) / 5  # todo: this should be global cause in both maps
    heat_intensity = np.exp(-distance ** 2 / (2 * sigma ** 2))

    return heat_intensity
