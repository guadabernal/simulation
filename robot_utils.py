import numpy as np

def is_position_occupied(position, current_robot, robots):
    """Check if the given position is occupied by any other robot."""
    for robot in robots:
        if robot is not current_robot:
            robot_pos = robot['position']
            if int(round(robot_pos[0])) == int(round(position[0])) and int(round(robot_pos[1])) == int(round(position[1])):
                return True
    return False

def move_robot(robot, robots, floor_plan):
    """Move the robot straight in its current orientation unless blocked by a wall or another robot."""
    x, y = robot['position']
    orientation = robot['orientation']

    # Add a small random angle to the orientation
    random_angle = np.random.uniform(-np.pi / 18, np.pi / 18)  # ±10 degrees
    orientation = (orientation + random_angle) % (2 * np.pi)
    robot['orientation'] = orientation

    # Try to move in the new orientation
    dx, dy = np.cos(orientation), np.sin(orientation)
    new_x = x + dx
    new_y = y + dy
    int_new_x, int_new_y = int(round(new_x)), int(round(new_y))

    # Check if the move is possible
    if (
        0 <= int_new_x < floor_plan.shape[0]
        and 0 <= int_new_y < floor_plan.shape[1]
        and floor_plan[int_new_x, int_new_y] == 1
        and not is_position_occupied((new_x, new_y), robot, robots)
    ):
        robot['position'] = (new_x, new_y)
        return  # Move forward if possible

    # If unable to move forward, proceed with the previous randomized rotation logic
    # (as shown in the previous modification)


    # If unable to move forward, choose a random rotation angle
    rotation_angles = [np.pi / 2, -np.pi / 2, np.pi]  # 90 degrees left/right or 180 degrees
    np.random.shuffle(rotation_angles)  # Shuffle the options
    for angle in rotation_angles:
        new_orientation = (orientation + angle) % (2 * np.pi)
        dx, dy = np.cos(new_orientation), np.sin(new_orientation)
        new_x = x + dx
        new_y = y + dy
        int_new_x, int_new_y = int(round(new_x)), int(round(new_y))

        if (
            0 <= int_new_x < floor_plan.shape[0]
            and 0 <= int_new_y < floor_plan.shape[1]
            and floor_plan[int_new_x, int_new_y] == 1
            and not is_position_occupied((new_x, new_y), robot, robots)
        ):
            robot['orientation'] = new_orientation  # Update orientation
            robot['position'] = (new_x, new_y)
            return  # Move if possible

    # If no move is possible, stay in place
    print(f"Robot at ({int(round(x))}, {int(round(y))}) cannot move and stays in place.")


def sense_environment(robot, floor_plan, known_map):
    """Sense the environment around the robot using a cone-shaped field of view."""
    cone_length = 8  # Extended length for more refined sensing
    cone_angle = np.pi / 4  # 45-degree cone
    x, y = robot['position']
    orientation = robot['orientation']

    cone_points = []
    for angle_offset in np.linspace(-cone_angle / 2, cone_angle / 2, 100):  # More fine angle sampling
        angle = orientation + angle_offset
        for distance in np.linspace(0.5, cone_length, 50):  # More fine distance sampling
            new_x = x + distance * np.cos(angle)
            new_y = y + distance * np.sin(angle)
            int_new_x = int(round(new_x))
            int_new_y = int(round(new_y))

            if 0 <= int_new_x < floor_plan.shape[0] and 0 <= int_new_y < floor_plan.shape[1]:
                if floor_plan[int_new_x, int_new_y] == 0:
                    known_map[int_new_x, int_new_y] = 0  # Mark as occupied
                    cone_points.append((new_x, new_y))
                    break  # Stop if it encounters a wall
                known_map[int_new_x, int_new_y] = 1  # Mark as free space
                cone_points.append((new_x, new_y))

    return known_map, cone_points
