# Ashley Ford (22981961)
# Cameron Nguyen (22968675)
from nes_py.wrappers import JoypadSpace
from gym_super_mario_bros.actions import COMPLEX_MOVEMENT
import gym
import cv2 as cv
import numpy as np
import string

SCREEN_HEIGHT   = 240
SCREEN_WIDTH    = 256
MATCH_THRESHOLD = 0.9

MASK_COLOUR = np.array([252, 136, 104])
image_files = {
    "mario": {
        "small": ["marioA.png", "marioB.png", "marioC.png", "marioD.png",
                  "marioE.png", "marioF.png", "marioG.png"],
        "tall": ["tall_marioA.png", "tall_marioB.png", "tall_marioC.png", "tall_marioD.png", "tall_marioE.png", "tall_marioF.png"],
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
        "mushroom": ["mushroom_red.png"],
    }
}

def _get_template(filename):
    image = cv.imread(filename)
    assert image is not None, f"File {filename} does not exist."
    template = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    mask = np.uint8(np.where(np.all(image == MASK_COLOUR, axis=2), 0, 1))
    num_pixels = image.shape[0]*image.shape[1]
    if num_pixels - np.sum(mask) < 10:
        mask = None
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

include_flipped = {"mario", "enemy"}

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

colour_map = {
    (104, 136, 252): " ", # sky blue colour
    (0,     0,   0): " ", # black
    (252, 252, 252): "'", # white / cloud colour
    (248,  56,   0): "M", # red / mario colour
    (228,  92,  16): "%", # brown enemy / block colour
}
unused_letters = sorted(set(string.ascii_uppercase) - set(colour_map.values()),reverse=True)
DEFAULT_LETTER = "?"

def _get_colour(colour):
    colour = tuple(colour)
    if colour in colour_map:
        return colour_map[colour]
    
    if unused_letters:
        letter = unused_letters.pop()
        colour_map[colour] = letter
        return letter
    else:
        return DEFAULT_LETTER

def _locate_object(screen, templates, stop_early=False, threshold=MATCH_THRESHOLD):
    locations = {}
    for template, mask, dimensions in templates:
        results = cv.matchTemplate(screen, template, cv.TM_CCOEFF_NORMED, mask=mask)
        locs = np.where(results >= threshold)
        for y, x in zip(*locs):
            locations[(x, y)] = dimensions

        if stop_early and locations:
            break
    
    return [( loc,  locations[loc]) for loc in locations]

def _locate_pipe(screen, threshold=MATCH_THRESHOLD):
    upper_template, upper_mask, upper_dimensions = templates["block"]["pipe"][0]
    lower_template, lower_mask, lower_dimensions = templates["block"]["pipe"][1]

    upper_results = cv.matchTemplate(screen, upper_template, cv.TM_CCOEFF_NORMED, mask=upper_mask)
    upper_locs = list(zip(*np.where(upper_results >= threshold)))
    
    if not upper_locs:
        return []
    
    lower_results = cv.matchTemplate(screen, lower_template, cv.TM_CCOEFF_NORMED, mask=lower_mask)
    lower_locs = set(zip(*np.where(lower_results >= threshold)))

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
    screen = cv.cvtColor(screen, cv.COLOR_BGR2GRAY)

    object_locations = {}
    for category in templates:
        category_templates = templates[category]
        category_items = []
        stop_early = False
        for object_name in category_templates:
            if category == "mario":
                if object_name != mario_status:
                    continue
                else:
                    stop_early = True
            if object_name == "pipe":
                continue

            results = _locate_object(screen, category_templates[object_name], stop_early)
            for location, dimensions in results:
                category_items.append((location, dimensions, object_name))

        object_locations[category] = category_items

    object_locations["block"] += _locate_pipe(screen)
    return object_locations


def make_action(screen, info, step, env, prev_action):
    mario_status = info["status"]
    object_locations = locate_objects(screen, mario_status)

    mario_locations = object_locations["mario"]

    enemy_locations = object_locations["enemy"]

    block_locations = object_locations["block"]
    
    item_locations = object_locations["item"]

# --------------------------------------------------------------------------
# Rule Based Heuristics Begin
# --------------------------------------------------------------------------
    if mario_locations:
        location, dimensions, object_name = mario_locations[0]
        mario_x, mario_y = location
        mario_world_x = info["x_pos"]
        speed = mario_world_x - prev.prev_mario_world_x
        prev.prev_mario_world_x = mario_world_x

        # Obtains locations of different objects
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

        # Obtains locations of enemies ahead of mario 
        ene_locs = []
        if enemy_locations:
            for enemy in enemy_locations:
                enemy_location, enemy_dimensions, enemy_name = enemy
                if enemy_location[0] > mario_x:
                    if mario_y + dimensions[1] == enemy_location[1] + enemy_dimensions[1]:
                        ene_locs.append(enemy)
                        enemy_x, enemy_y = enemy_location

        # Detects gaps in the ground
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
        
        # Jumps over gaps, tall mario needs to hold jump for longer
        if gap:
            if mario_status == "small":
                if mario_x > gap_x + 16: 
                    if len(gap) > 1:
                        gap_x = gap[1]
                    else:
                        gap_x = 500
                if gap_x - mario_x < 10:
                    return 2
            elif mario_status == "tall":
                if mario_x > gap_x + 48: 
                    if len(gap) > 1:
                        gap_x = gap[1]
                    else:
                        gap_x = 500
                if gap_x - mario_x < 5:
                    return 2
            
        # Collects items and hits question blocks if safe (no enemies on screen)
        if not enemy_locations:
            if item_locations:
                item_loc = item_locations[0][0]
                item_x, item_y = item_loc
                return get_item(mario_x, mario_y, item_x, item_y)
            if question_loc:
                ques_x = question_loc[0][0]
                action = break_block(mario_x, ques_x)
                if action:
                    return action
        
    
        # Jumps on enemies
        if ene_locs:
            ene_locs.sort()
            enemy_x, enemy_y = ene_locs[0][0]
            enemy_name = ene_locs[0][2]
            if can_stomp_on_enemy(mario_x, mario_y, enemy_x, enemy_y, enemy_name):
                return 2
            
        # Prevents mario from getting stuck due to holding down jump button
        if speed == 0 and step > 20:
            # Tall mario needs to hold jump for longer
            if mario_status == "tall":
                if step % 45 == 0:
                    return 0
                else:
                    return 2
            elif mario_status == "small":
                if step % 20 == 0:
                    return 0
                else:
                    return 2  
        
        # Jumps over pipes
        if pipe_loc:
            pipe_x = pipe_loc[0][0]

            # Moves to next pipe if mario is past the current pipe
            if mario_x > pipe_x:
                if len(pipe_loc) > 1:
                    pipe_x = pipe_loc[1][0]
                else:
                    pipe_x = pipe_loc[0][0]

            if pipe_ahead(mario_x, pipe_x) and can_jump_over_pipe(mario_x, pipe_x):
                return 2
    return 1

def can_stomp_on_enemy(mario_x, mario_y, ene_x, ene_y, ene_name):
    if ene_name == "koopa":
            return mario_y - ene_y < 15 and ene_x - mario_x < 52
    else:
        return ene_x - mario_x < 47

def pipe_ahead(mario_x, pipe_x):
    return mario_x < pipe_x

def break_block(mario_x, ques_x):
    if mario_x > ques_x:
        if mario_x - ques_x < 15:
            return 7
        else:
            return 6
    elif mario_x < ques_x:
        if ques_x - mario_x < 15:
            return 2
        else:
            return 1
    return 0

def get_item(mario_x, mario_y, item_x, item_y):
    if mario_x - item_x > 10:
        return 6
    elif item_x - mario_x < 10:
        return 1
    if item_y > mario_y:
        return 5
    else:
        return 1
    
def can_jump_over_pipe(mario_x, pipe_x):
    return pipe_x - mario_x < 40

class prev:
    prev_mario_world_x = 0


env = gym.make("SuperMarioBros-v0", apply_api_compatibility=True, render_mode="human")
env = JoypadSpace(env, COMPLEX_MOVEMENT)

obs = None
done = True
env.reset()
step_count = 0
total_reward = 0
for step in range(10000):
    if obs is not None:
        action = make_action(obs, info, step, env, action)
    else:
        action = 1
    obs, reward, terminated, truncated, info = env.step(action)
    step_count += 1
    total_reward += reward
    if info["flag_get"]:
        world = info["world"]
        stage = info["stage"]
        print(f"Stage {world}-{stage} completed in:", step_count, "steps")
        print("Current Score:", info["score"])
        print("Total Reward:", total_reward)
        print("Coins collected:", info["coins"], "\n")
        step_count = 0
        total_reward = 0
    done = terminated or truncated
    if done:
        step_count = 0
        total_reward = 0
        env.reset()
env.close()