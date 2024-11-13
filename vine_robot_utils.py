import numpy as np

def move_vine_robot(vine_robot, floor_plan):
    """Move the vine robot in its specified orientation until it hits a wall."""
    if not vine_robot['active']:
        return  # Do nothing if the vine robot is not active

    x, y = vine_robot['positions'][-1]  # Get the current end position
    orientation = vine_robot['orientation']
    # Move one unit in the direction of orientation
    new_x = x + np.cos(orientation)
    new_y = y + np.sin(orientation)
    int_new_x, int_new_y = int(round(new_x)), int(round(new_y))

    # Check if within bounds and not blocked
    if (
        0 <= int_new_x < floor_plan.shape[0]
        and 0 <= int_new_y < floor_plan.shape[1]
        and floor_plan[int_new_x, int_new_y] == 1
    ):
        # Add the new position to the vine robot's path
        vine_robot['positions'].append((new_x, new_y))
    else:
        # Stop moving if a wall is encountered but keep it visualized
        vine_robot['active'] = False
        print("Vine robot has reached a wall and stopped moving.")