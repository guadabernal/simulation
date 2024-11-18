import numpy as np

def check_collision(position, current_robot, robots, floor_plan, robot_diameter):
    x, y = position
    robot_radius = robot_diameter / 2

    # Check collision with walls
    x_min = int(np.floor(x - robot_radius))
    x_max = int(np.ceil(x + robot_radius))
    y_min = int(np.floor(y - robot_radius))
    y_max = int(np.ceil(y + robot_radius))

    for xi in range(x_min, x_max + 1):
        for yi in range(y_min, y_max + 1):
            if 0 <= xi < floor_plan.shape[0] and 0 <= yi < floor_plan.shape[1]:
                if floor_plan[xi, yi] == 0:
                    # Check if this grid cell is within robot_radius of (x,y)
                    cell_center_x = xi + 0.5
                    cell_center_y = yi + 0.5
                    dx = cell_center_x - x
                    dy = cell_center_y - y
                    distance = np.sqrt(dx ** 2 + dy ** 2)
                    if distance < robot_radius:
                        return True  # Collision with wall
            else:
                # Out of bounds, consider as wall
                return True

    # Check collision with other robots
    for other_robot in robots:
        if other_robot is not current_robot:
            other_x, other_y = other_robot['position']
            dx = other_x - x
            dy = other_y - y
            distance = np.sqrt(dx ** 2 + dy ** 2)
            if distance < robot_diameter:
                return True  # Collision with another robot

    return False  # No collision

def move_robot(robot, robots, floor_plan, robot_diameter):
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
    new_position = (new_x, new_y)
    
    # check if possible
    if not check_collision(new_position, robot, robots, floor_plan, robot_diameter):
        robot['position'] = new_position
        # Update distance_traveled
        distance = np.sqrt(dx**2 + dy**2)
        robot['distance_traveled'] += distance
        return
    
    # else bumped into something so rotate
    rotation_angles = [np.pi / 2, -np.pi / 2, np.pi]
    np.random.shuffle(rotation_angles)

    for angle in rotation_angles:
        new_orientation = (orientation + angle) % (2 * np.pi)
        dx, dy = np.cos(new_orientation), np.sin(new_orientation)
        new_x = x + dx
        new_y = y + dy
        new_position = (new_x, new_y)

        if not check_collision(new_position, robot, robots, floor_plan, robot_diameter):
            robot['orientation'] = new_orientation
            robot['position'] = new_position
            # Update distance_traveled
            distance = np.sqrt(dx**2 + dy**2)
            robot['distance_traveled'] += distance
            return

    # stay in place
    print(f"Robot at ({int(round(x))}, {int(round(y))}) cannot move and stays in place.")

def sense_environment(robot, floor_plan, known_map, heat_map_enabled, heat_source_position, known_heat_map, robot_diameter):
    x, y = robot['position']
    cone_points = []
    robot_radius = robot_diameter / 2

    if robot['sensors'].get('Cone Vision', False):
        cone_length = 8
        cone_angle = np.pi / 4  # 45-degree cone
        orientation = robot['orientation']
    
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
                        if robot['sensors'].get('Heat Sensor', False) and heat_map_enabled and heat_source_position is not None: 
                            known_heat_map[int_new_x, int_new_y] = get_heat_at_position((int_new_x, int_new_y), heat_source_position, floor_plan.shape)
                        cone_points.append((new_x, new_y))
                        break
                    known_map[int_new_x, int_new_y] = 1  # marks as free space
                    if robot['sensors'].get('Heat Sensor', False) and heat_map_enabled and heat_source_position is not None: 
                        known_heat_map[int_new_x, int_new_y] = get_heat_at_position((int_new_x, int_new_y), heat_source_position, floor_plan.shape)
                    cone_points.append((new_x, new_y))
    else:
        # If no cone vision, sense the area occupied by the robot
        x_min = int(np.floor(x - robot_radius))
        x_max = int(np.ceil(x + robot_radius))
        y_min = int(np.floor(y - robot_radius))
        y_max = int(np.ceil(y + robot_radius))
        for xi in range(x_min, x_max + 1):
            for yi in range(y_min, y_max + 1):
                if 0 <= xi < floor_plan.shape[0] and 0 <= yi < floor_plan.shape[1]:
                    cell_center_x = xi + 0.5
                    cell_center_y = yi + 0.5
                    dx = cell_center_x - x
                    dy = cell_center_y - y
                    distance = np.sqrt(dx ** 2 + dy ** 2)
                    if distance <= robot_radius:
                        if floor_plan[xi, yi] == 0:
                            known_map[xi, yi] = 0  # Obstacle
                        else:
                            known_map[xi, yi] = 1  # Free space
                        if robot['sensors'].get('Heat Sensor', False) and heat_map_enabled and heat_source_position is not None:
                            known_heat_map[xi, yi] = get_heat_at_position((xi, yi), heat_source_position, floor_plan.shape)
    return known_map, cone_points, known_heat_map

def get_heat_at_position(position, heat_source_position, grid_shape):
    x_pos, y_pos = position
    x_source, y_source = heat_source_position

    distance = np.sqrt((x_pos - x_source) ** 2 + (y_pos - y_source) ** 2)
    sigma = max(grid_shape) / 5  # spread of the heat
    heat_intensity = np.exp(-distance ** 2 / (2 * sigma ** 2))

    return heat_intensity
