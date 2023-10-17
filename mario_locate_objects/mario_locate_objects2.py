from nes_py.wrappers import JoypadSpace
from gym_super_mario_bros.actions import COMPLEX_MOVEMENT
import gym
import cv2 as cv
import numpy as np
import string
import time
import agent
# code for locating objects on the screen in super mario bros
# by Lauren Gee

# Template matching is based on this tutorial:
# https://docs.opencv.org/4.x/d4/dc6/tutorial_py_template_matching.html

################################################################################

# change these values if you want more/less printing
PRINT_GRID      = False
PRINT_LOCATIONS = False

# If printing the grid doesn't display in an understandable way, change the
# settings of your terminal (or anaconda prompt) to have a smaller font size,
# so that everything fits on the screen. Also, use a large terminal window /
# whole screen.

# other constants (don't change these)
SCREEN_HEIGHT   = 240
SCREEN_WIDTH    = 256
MATCH_THRESHOLD = 0.9

################################################################################
# TEMPLATES FOR LOCATING OBJECTS

# ignore sky blue colour when matching templates
MASK_COLOUR = np.array([252, 136, 104])
# (these numbers are [BLUE, GREEN, RED] because opencv uses BGR colour format by default)

# You can add more images to improve the object locator, so that it can locate
# more things. For best results, paint around the object with the exact shade of
# blue as the sky colour. (see the given images as examples)
#
# Put your image filenames in image_files below, following the same format, and
# it should work fine.

# filenames for object templates
image_files = {
    "mario": {
        "small": ["marioA.png", "marioB.png", "marioC.png", "marioD.png",
                  "marioE.png", "marioF.png", "marioG.png"],
        "tall": ["tall_marioA.png", "tall_marioB.png", "tall_marioC.png"],
        # Note: Many images are missing from tall mario, and I don't have any
        # images for fireball mario.
    },
    "enemy": {
        "goomba": ["goomba.png"],
        "koopa": ["koopaA.png", "koopaB.png"],
    },
    "block": {
        "block": ["block1.png", "block2.png", "block3.png", "block4.png"],
        "question_block": ["questionA.png", "questionB.png", "questionC.png"],
        "pipe": ["pipe_upper_section.png", "pipe_lower_section.png"],
    },
    "item": {
        # Note: The template matcher is colourblind (it's using greyscale),
        # so it can't tell the difference between red and green mushrooms.
        "mushroom": ["mushroom_red.png"],
        # There are also other items in the game that I haven't included,
        # such as star.

        # There's probably a way to change the matching to work with colour,
        # but that would slow things down considerably. Also, given that the
        # red and green mushroom sprites are so similar, it might think they're
        # the same even if there is colour.
    }
}

def _get_template(filename):
    image = cv.imread(filename)
    assert image is not None, f"File {filename} does not exist."
    template = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    mask = np.uint8(np.where(np.all(image == MASK_COLOUR, axis=2), 0, 1))
    num_pixels = image.shape[0]*image.shape[1]
    if num_pixels - np.sum(mask) < 10:
        mask = None # this is important for avoiding a problem where some things match everything
    dimensions = tuple(template.shape[::-1])
    return template, mask, dimensions

def get_template(filenames):
    results = []
    for filename in filenames:
        results.append(_get_template(filename))
    return results

def get_template_and_flipped(filenames):
    results = []
    for filename in filenames:
        template, mask, dimensions = _get_template(filename)
        results.append((template, mask, dimensions))
        results.append((cv.flip(template, 1), cv.flip(mask, 1), dimensions))
    return results

# Mario and enemies can face both right and left, so I'll also include
# horizontally flipped versions of those templates.
include_flipped = {"mario", "enemy"}

# generate all templatees
templates = {}
for category in image_files:
    category_items = image_files[category]
    category_templates = {}
    for object_name in category_items:
        filenames = category_items[object_name]
        if category in include_flipped or object_name in include_flipped:
            category_templates[object_name] = get_template_and_flipped(filenames)
        else:
            category_templates[object_name] = get_template(filenames)
    templates[category] = category_templates

################################################################################
# PRINTING THE GRID (for debug purposes)

colour_map = {
    (104, 136, 252): " ", # sky blue colour
    (0,     0,   0): " ", # black
    (252, 252, 252): "'", # white / cloud colour
    (248,  56,   0): "M", # red / mario colour
    (228,  92,  16): "%", # brown enemy / block colour
}
unused_letters = sorted(set(string.ascii_uppercase) - set(colour_map.values()),reverse=True)
DEFAULT_LETTER = "?"

def _get_colour(colour): # colour must be 3 ints
    colour = tuple(colour)
    if colour in colour_map:
        return colour_map[colour]
    
    # if we haven't seen this colour before, pick a letter to represent it
    if unused_letters:
        letter = unused_letters.pop()
        colour_map[colour] = letter
        return letter
    else:
        return DEFAULT_LETTER

def print_grid(obs, object_locations):
    pixels = {}
    # build the outlines of located objects
    for category in object_locations:
        for location, dimensions, object_name in object_locations[category]:
            x, y = location
            width, height = dimensions
            name_str = object_name.replace("_", "-") + "-"
            for i in range(width):
                pixels[(x+i, y)] = name_str[i%len(name_str)]
                pixels[(x+i, y+height-1)] = name_str[(i+height-1)%len(name_str)]
            for i in range(1, height-1):
                pixels[(x, y+i)] = name_str[i%len(name_str)]
                pixels[(x+width-1, y+i)] = name_str[(i+width-1)%len(name_str)]

    # print the screen to terminal
    print("-"*SCREEN_WIDTH)
    for y in range(SCREEN_HEIGHT):
        line = []
        for x in range(SCREEN_WIDTH):
            coords = (x, y)
            if coords in pixels:
                # this pixel is part of an outline of an object,
                # so use that instead of the normal colour symbol
                colour = pixels[coords]
            else:
                # get the colour symbol for this colour
                colour = _get_colour(obs[y][x])
            line.append(colour)
        print("".join(line))

################################################################################
# LOCATING OBJECTS

def _locate_object(screen, templates, stop_early=False, threshold=MATCH_THRESHOLD):
    locations = {}
    for template, mask, dimensions in templates:
        results = cv.matchTemplate(screen, template, cv.TM_CCOEFF_NORMED, mask=mask)
        locs = np.where(results >= threshold)
        for y, x in zip(*locs):
            locations[(x, y)] = dimensions

        # stop early if you found mario (don't need to look for other animation frames of mario)
        if stop_early and locations:
            break
    
    #      [((x,y), (width,height))]
    return [( loc,  locations[loc]) for loc in locations]

def _locate_pipe(screen, threshold=MATCH_THRESHOLD):
    upper_template, upper_mask, upper_dimensions = templates["block"]["pipe"][0]
    lower_template, lower_mask, lower_dimensions = templates["block"]["pipe"][1]

    # find the upper part of the pipe
    upper_results = cv.matchTemplate(screen, upper_template, cv.TM_CCOEFF_NORMED, mask=upper_mask)
    upper_locs = list(zip(*np.where(upper_results >= threshold)))
    
    # stop early if there are no pipes
    if not upper_locs:
        return []
    
    # find the lower part of the pipe
    lower_results = cv.matchTemplate(screen, lower_template, cv.TM_CCOEFF_NORMED, mask=lower_mask)
    lower_locs = set(zip(*np.where(lower_results >= threshold)))

    # put the pieces together
    upper_width, upper_height = upper_dimensions
    lower_width, lower_height = lower_dimensions
    locations = []
    for y, x in upper_locs:
        for h in range(upper_height, SCREEN_HEIGHT, lower_height):
            if (y+h, x+2) not in lower_locs:
                locations.append(((x, y), (upper_width, h), "pipe"))
                break
    return locations

def locate_objects(screen, mario_status):
    # convert to greyscale
    screen = cv.cvtColor(screen, cv.COLOR_BGR2GRAY)

    # iterate through our templates data structure
    object_locations = {}
    for category in templates:
        category_templates = templates[category]
        category_items = []
        stop_early = False
        for object_name in category_templates:
            # use mario_status to determine which type of mario to look for
            if category == "mario":
                if object_name != mario_status:
                    continue
                else:
                    stop_early = True
            # pipe has special logic, so skip it for now
            if object_name == "pipe":
                continue
            
            # find locations of objects
            results = _locate_object(screen, category_templates[object_name], stop_early)
            for location, dimensions in results:
                category_items.append((location, dimensions, object_name))

        object_locations[category] = category_items

    # locate pipes
    object_locations["block"] += _locate_pipe(screen)
    #print(object_locations)
    return object_locations

################################################################################
# GETTING INFORMATION AND CHOOSING AN ACTION

def make_action(screen, info, step, env, prev_action):
    mario_status = info["status"]
    object_locations = locate_objects(screen, mario_status)

    # You probably don't want to print everything I am printing when you run
    # your code, because printing slows things down, and it puts a LOT of
    # information in your terminal.

    # Printing the whole grid is slow, so I am only printing it occasionally,
    # and I'm only printing it for debug purposes, to see if I'm locating objects
    # correctly.
    if PRINT_GRID and step % 100 == 0:
        print_grid(screen, object_locations)
        # If printing the grid doesn't display in an understandable way, change
        # the settings of your terminal (or anaconda prompt) to have a smaller
        # font size, so that everything fits on the screen. Also, use a large
        # terminal window / whole screen.

        # object_locations contains the locations of all the objects we found
        print(object_locations)

    # List of locations of Mario:
    mario_locations = object_locations["mario"]
    # (There's usually 1 item in mario_locations, but there could be 0 if we
    # couldn't find Mario. There might even be more than one item in the list,
    # but if that happens they are probably approximately the same location.)

    # List of locations of enemies, such as goombas and koopas:
    enemy_locations = object_locations["enemy"]

    # List of locations of blocks, pipes, etc:
    block_locations = object_locations["block"]
    # List of locations of items: (so far, it only finds mushrooms)
    item_locations = object_locations["item"]
    # This is the format of the lists of locations:
    # ((x_coordinate, y_coordinate), (object_width, object_height), object_name)
    #
    # x_coordinate and y_coordinate are the top left corner of the object
    #
    # For example, the enemy_locations list might look like this:
    # [((161, 193), (16, 16), 'goomba'), ((175, 193), (16, 16), 'goomba')]
    
    if PRINT_LOCATIONS:
        # To get the information out of a list:
        for enemy in enemy_locations:
            enemy_location, enemy_dimensions, enemy_name = enemy
            x, y = enemy_location
            width, height = enemy_dimensions
            print("enemy:", x, y, width, height, enemy_name)

        # Or you could do it this way:
        for block in block_locations:
            block_x = block[0][0]
            block_y = block[0][1]
            block_width = block[1][0]
            block_height = block[1][1]
            block_name = block[2]
            print(f"{block_name}: {(block_x, block_y)}), {(block_width, block_height)}")

        # Or you could do it this way:
        for item_location, item_dimensions, item_name in item_locations:
            x, y = item_location
            print(item_name, x, y)

        # gym-super-mario-bros also gives us some info that might be useful
        print(info)
        # see https://pypi.org/project/gym-super-mario-bros/ for explanations

        # The x and y coordinates in object_locations are screen coordinates.
        # Top left corner of screen is (0, 0), top right corner is (255, 0).
        # Here's how you can get Mario's screen coordinates:
        if mario_locations:
            location, dimensions, object_name = mario_locations[0]
            mario_x, mario_y = location
            print("Mario's location on screen:",
                    mario_x, mario_y, f"({object_name} mario)")
        
        # The x and y coordinates in info are world coordinates.
        # They tell you where Mario is in the game, not his screen position.
        mario_world_x = info["x_pos"]
        mario_world_y = info["y_pos"]
        # Also, you can get Mario's status (small, tall, fireball) from info too.
        mario_status = info["status"]
        print("Mario's location in world:",
              mario_world_x, mario_world_y, f"({mario_status} mario)")
    # move = agent.move(mario_locations, enemy_locations, item_locations, block_locations, step, prev)
    # if move == None:
    #     return 0
    # if step % 15 == 0:
    #     return 0
    # else:
    #     return 5
# --------------------------------------------------------------------------
        # TODO: Write code for a strategy, such as a rule based agent.
    if mario_locations:
        location, dimensions, object_name = mario_locations[0]
        mario_x, mario_y = location
        mario_world_x = info["x_pos"]
        speed = mario_world_x - prev.prev_mario_world_x
        prev.prev_mario_world_x = mario_world_x

        # print(block_locations)
        question_loc = []
        pipe_loc = []
        block_loc = []
        for block in block_locations:
            if block[2] == "question_block":
                question_loc.append(block[0])
            elif block[2] == "pipe":
                pipe_loc.append(block[0])
            elif block[2] == "block":
                block_loc.append(block[0])
        pipe_loc.sort()
        question_loc.sort()
        block_loc.sort()

        ene_locs = []
        if enemy_locations:
            for enemy in enemy_locations:
                enemy_location, enemy_dimensions, enemy_name = enemy
                if enemy_location[0] > mario_x:
                    ene_locs.append(enemy)
                # ene_locs.append(enemy_location)
        # if ene_locs:
        #     ene_locs.sort()
        #     enemy_x, enemy_y = ene_locs[0]
        #     away = False
        #     if enemy_x + speed >= prev.prev_ene_x and mario_x < enemy_x:
        #         away = True
        #     elif enemy_x + speed <= prev.prev_ene_x and mario_x > enemy_x:
        #         away = True
        #     else:
        #         away = False
        #     print(away)
        #     prev.prev_ene_x = enemy_x
        # if question_loc:
        #     ques_x, ques_y = question_loc[0]
        #     if mario_x < ques_x:
        #             if ques_x - mario_x < 15:
        #                 if ene_locs and not enemy_danger(mario_x, mario_y, enemy_x, enemy_y):
        #                     return 2
        # ene_locs = []
        # if enemy_locations:
        #     for enemy in enemy_locations:
        #         enemy_location, enemy_dimensions, enemy_name = enemy
        #         ene_locs.append(enemy_location)
        gap = []
        gap_x = 0
        if block_loc:
            block_x, block_y = block_loc[0]
            for block in block_loc:
                if block[1] != 224:
                    continue
                if block[1] == block_y:
                    if block[0] - block_x > 16:
                        gap.append(block_x)
                        gap_x = block_x
                block_x, block_y = block
        if gap:
            if mario_x > gap_x + 16: 
                if len(gap) > 1:
                    gap_x = gap[1]
                else:
                    gap_x = 500
            if gap_x - mario_x < 10:
                return 2
        # if gap:
        #     gap_x = gap[0][0]
        #     if mario_x > gap_x: 
        #         if len(gap) > 1:
        #             print("passed")
        #             gap_x = gap[1][0]
        #     if gap_x - mario_x < 10:
        #         return 2
            
        if ene_locs:
            ene_locs.sort()
            enemy_x, enemy_y = ene_locs[0][0]
            enemy_name = ene_locs[0][2]
            away = False
            if mario_x < enemy_x:
                if enemy_x >= prev.prev_ene_x:
                    away = True
                else:
                    away = False
            elif mario_x > enemy_x:
                if enemy_x <= prev.prev_ene_x:
                    away = True
                else:
                    away = False
            prev.prev_ene_x = enemy_x
            if enemy_ahead(mario_x, mario_y, enemy_x, enemy_y) and can_stomp_on_enemy(mario_x, mario_y, enemy_x, enemy_y, away, enemy_name):
                action = jump_on_enemy()
                return action
        if speed == 0:
            if step % 20 == 0:
                return 0
            else:
                return 2    
        
        if pipe_loc:
            if mario_x > pipe_loc[0][0]:
                if len(pipe_loc) > 1:
                    pipe_x, pipe_y = pipe_loc[1]
                else:
                    pipe_x, pipe_y = pipe_loc[0]
            pipe_x, pipe_y = pipe_loc[0]
            if pipe_ahead(mario_x, mario_y, pipe_x, pipe_y) and can_jump_over_pipe(mario_x, mario_y, pipe_x, pipe_y):
                action = jump_over_pipe()
                return action

# --------------------------------------------------------------------------
    # question_loc = []
    # pipe_loc = []
    # for block in block_locations:
    #     if block[2] == "question_block":
    #         question_loc.append(block[0])
    #     elif block[2] == "pipe":
    #         pipe_loc.append(block[0])
    # pipe_loc.sort()
    # question_loc.sort()
    # if pipe_loc:
    #     pipe_x, pipe_y = pipe_loc[0]
    #     if mario_locations:
    #         if mario_x > pipe_x:
    #             if len(pipe_loc) > 1:
    #                 pipe_x, pipe_y = pipe_loc[1]

    # ene_locs = []
    # if enemy_locations:
    #     for enemy in enemy_locations:
    #         enemy_location, enemy_dimensions, enemy_name = enemy
    #         ene_locs.append(enemy_location)
    # if ene_locs:
    #     ene_locs.sort()
    #     enemy_x, enemy_y = ene_locs[0]
    #     try:
    #         if enemy_x >= prev.prev_ene_x and mario_x < enemy_x:
    #             away = True
    #         elif enemy_x <= prev.prev_ene_x and mario_x > enemy_x:
    #             away = True
    #         else:
    #             away = False
    #         prev.prev_x = enemy_x

    #         if pipe_loc:
    #             if mario_x < pipe_x and pipe_x < enemy_x:
    #                 if pipe_x - mario_x < 40:
    #                     return 2
    #         if mario_x < enemy_x:
    #             if away:
    #                 if mario_y == enemy_y and enemy_x - mario_x < 30:
    #                     return 2
    #                 else:
    #                     return 1
    #             elif mario_y == enemy_y and enemy_x - mario_x < 50:
    #                 return 2
    #             else:
    #                 return 1
                
    #         elif mario_x > enemy_x:
    #             if away:
    #                 if mario_y == enemy_y and mario_x - enemy_x < 30:
    #                     return 7
    #                 else:
    #                     return 6
    #             elif mario_y == enemy_y and mario_x - enemy_x < 30:
    #                 return 7
    #             else:
    #                 return 6
    #         else:
    #             return 1
    #     except UnboundLocalError:
    #         pass
        
    # if item_locations:
    #     item_loc, dimensions, object_name = item_locations[0]
    #     item_x, item_y = item_loc
    #     try:
    #         if mario_x - item_x > 10:
    #             return 6
    #         elif item_x - mario_x < 10:
    #             return 1
    #         if item_y > mario_y:
    #             return 5
    #         else:
    #             return 1
    #     except UnboundLocalError:
    #         pass
        
    # if question_loc:
    #     ques_x, ques_y = question_loc[0]

    #     try:
    #         if mario_y < ques_y:
    #             return 1
    #         if mario_x > ques_x:
    #             if mario_x - ques_x < 15:
    #                 return 7
    #             else:
    #                 return 6
    #         elif mario_x < ques_x:
    #             if ques_x - mario_x < 15:
    #                 return 2
    #             else:
    #                 return 1
    #         # if mario_x - ques_x > 15:
    #         #     return 7
    #         # elif ques_x - mario_x < 15:
    #         #     return 2
    #     except UnboundLocalError:
    #         pass
    # if pipe_loc:
    #     try:
    #         if pipe_x - mario_x < 40:
    #             return 2
    #         else: #pipe_x - mario_x < 10:
    #             return 1
    #         #else:
    #             return 1
    #     except UnboundLocalError:
    #         pass

# ----------------------------------------------------------------------

    # Choose an action from the list of available actions.
    # For example, action = 0 means do nothing
    #              action = 1 means press 'right' button
    #              action = 2 means press 'right' and 'A' buttons at the same time
    return 1
    # if step % 10 == 0:
    #     # I have no strategy at the moment, so I'll choose a random action.
    #     action = 1
    #     return move
    # else:
    #     # With a random agent, I found that choosing the same random action
    #     # 10 times in a row leads to slightly better performance than choosing
    #     # a new random action every step.
    #     return move
def enemy_ahead(mario_x, mario_y, ene_x, ene_y):
    return mario_x < ene_x

def can_stomp_on_enemy(mario_x, mario_y, ene_x, ene_y, away, ene_name):
    if ene_name == "koopa":
        if mario_x < ene_x:
            return ene_y - mario_y < 20 and ene_x - mario_x < 47
        else:
            return mario_y - ene_y < 20 and ene_x - mario_x < 47
    return mario_y == ene_y and ene_x - mario_x < 47
    if away:
        return mario_y == ene_y and ene_x - mario_x < 35
    else:
        return mario_y == ene_y and ene_x - mario_x < 35
    
def jump_on_enemy():
    return 2

def pipe_ahead(mario_x, mario_y, pipe_x, pipe_y):
    return mario_x < pipe_x

def can_jump_over_pipe(mario_x, mario_y, pipe_x, pipe_y):
    return pipe_x - mario_x < 40

def enemy_danger(mario_x, mario_y, ene_x, ene_y):
    return mario_y == ene_y and ene_x - mario_x < 60

def jump_over_pipe():
    return 2
################################################################################
class prev:
    prev_ene_x = 400
    prev_mario_x = 0
    prev_mario_world_x = 0


env = gym.make("SuperMarioBros-v0", apply_api_compatibility=True, render_mode="human")
env = JoypadSpace(env, COMPLEX_MOVEMENT)

obs = None
done = True
env.reset()
for step in range(10000):
    if obs is not None:
        action = make_action(obs, info, step, env, action)
    else:
        action = 1
        # action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    done = terminated or truncated
    if done:
        env.reset()
env.close()
