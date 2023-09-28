def get_info(mario_locations, item_locations, enemy_locations, block_locations):
    ene_locs = []
    question_loc = []
    pipe_loc = []
    item_loc = []

    if mario_locations:
        location, dimensions, object_name = mario_locations[0]
        mario_x, mario_y = location
    else:
        return None, None, None, None, None, None
    if item_locations:
        item_loc, dimensions, object_name = item_locations[0]
        #item_x, item_y = item_loc

    if enemy_locations:
        for enemy in enemy_locations:
            enemy_location, enemy_dimensions, enemy_name = enemy
            ene_locs.append(enemy_location)
        ene_locs.sort()

    if block_locations:
        for block in block_locations:
            if block[2] == "question_block":
                question_loc.append(block[0])
            elif block[2] == "pipe":
                pipe_loc.append(block[0])
        question_loc.sort()
        pipe_loc.sort()
    return  mario_x, mario_y, item_loc, ene_locs, question_loc, pipe_loc

def move(mario_locations, enemy_locations, item_locations, block_locations, step):

    mario_x, mario_y, item_loc, enemy_loc, ques_loc, pipe_loc = get_info(mario_locations, item_locations, enemy_locations, block_locations)
    if mario_x == None:
        return None
    elif mario_x == prev_x:
        return 2
    if enemy_loc:
        return react_enemies(enemy_loc, mario_x, mario_y, step)
    if item_loc:
        return react_items(mario_x, mario_y, item_loc, step)
    elif ques_loc:
        return react_blocks(mario_x, mario_y, ques_loc, step)
    elif pipe_loc:
        return react_pipes(mario_x, mario_y, pipe_loc, step)


def react_enemies(enemy_locations, mario_x, mario_y, step):
    enemy_x, enemy_y = enemy_locations[0]
    try:
        if mario_x < enemy_x:
            if mario_y == enemy_y and enemy_x - mario_x < 50:
                return 2
            else:
                return 1
        elif mario_x > enemy_x:
            if mario_y == enemy_y and mario_x - enemy_x < 50:
                return 5
            else:
                return 6
    except UnboundLocalError:
        pass

def react_items(mario_x, mario_y, item_loc, step):
    item_x, item_y = item_loc
    try:
        if mario_x - item_x > 10:
            return 6
        elif item_x - mario_x < 10:
            return 1
        if item_y > mario_y:
            return 5
        else:
            return 1
    except UnboundLocalError:
        pass

def react_blocks(mario_x, mario_y, ques_loc, step):
    ques_x, ques_y = ques_loc[0]

    try:
        if mario_y < ques_y:
            return 1
        if mario_x - ques_x > 10:
            return 6
        elif ques_x - mario_x < 10:
            return 2
        if ques_y > mario_y:
            return 5
        elif step % 10 == 0:
            return 1
        else: 
            return 2
    except UnboundLocalError:
        pass

def react_pipes(mario_x, mario_y, pipe_loc, step):
    pipe_x, pipe_y = pipe_loc[0]
    try:
        if pipe_x - mario_x < 40:
            return 2
        else: #pipe_x - mario_x < 10:
            return 1
        #if pipe_y > mario_y:
            return 5
        #else:
            return 1
    except UnboundLocalError:
        pass