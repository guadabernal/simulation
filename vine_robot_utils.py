import numpy as np

def move_vine_robot(vine_robot, floor_plan):
    if not vine_robot['active']: return

    x, y = vine_robot['positions'][-1]
    orientation = vine_robot['orientation']
    
    new_x = x + np.cos(orientation)
    new_y = y + np.sin(orientation)
    int_new_x, int_new_y = int(round(new_x)), int(round(new_y))

    # check if not blocked
    if (0 <= int_new_x < floor_plan.shape[0]
        and 0 <= int_new_y < floor_plan.shape[1]
        and floor_plan[int_new_x, int_new_y] == 1):
        
        vine_robot['positions'].append((new_x, new_y))
    else:
        vine_robot['active'] = False
        print("Vine robot reached a wall and stopped moving.")