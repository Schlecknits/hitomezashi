from PIL import Image, ImageDraw
import random
import argparse
import dataclasses


@dataclasses.dataclass()
class Vec2:
    x: int
    y: int

    def __add__(self, other):
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return Vec2(self.x * other.x, self.y * other.y)

    def __gt__(self, other):
        if self.x > other.x or self.y > other.y:
            return True
        return False

    def toTuple(self):
        return (self.x, self.y)


RIGHTWARDS = Vec2(1, 0)
DOWNWARDS = Vec2(0, 1)
draw_vectors = [RIGHTWARDS, DOWNWARDS]

# Default values
width = 600
height = 400
stitch_length = 25
stitch_width = 3  # TODO: make configurable
offset = int(
    stitch_width / 2)  # the offset from 0/0 coordinate, this is necessary because of the way ImageMagick draws lines
offset_vector = Vec2(offset, offset)
rainbow = False
bg_color = (0, 0, 0)
line_color = (0, 128, 0)
seed = random.randrange(-2147483648, 2147483647)
color_seed = seed
color_randomer = random.Random(seed)

parser = argparse.ArgumentParser("python3 generator.py")
parser.add_argument("-seed", "-s", help="set a generation seed (default: random Int32)")  # OK
parser.add_argument("-width", help="set the width in px of generated pattern (default: 400px)")  # OK
parser.add_argument("-height", help="set the height in px of generated pattern (default: 300px)")  # OK
parser.add_argument("-stitch", help="set the length in px of stitches (default: 25px)")  # OK
parser.add_argument("-fill", "-f", nargs="*", help="set an arbitrary amount of hex color codes to infill the pattern ("
                                                   "default: DISABLED)")
parser.add_argument("-color", "-c", help="set a hex color code for the line color (default: #FFFFFF)")
parser.add_argument("--rainbow", "--r", action="store_true",
                    help="enable random line colors for each drawn line (default: DISABLED). Overwrites color argument")
# TODO: Separate seeds for color generation
parser.add_argument("--rainbowfill", action="store_true",
                    help="enable random fill colors for each area (default: DISABLED). Overwrites fill argument.")
parser.add_argument("-output", "-o",
                    help="set a save location and name (default: [current_directory]/hitomezashi.png).")
parser.add_argument("--noshow", action="store_true", help="doesn't show the image after generation")
args = parser.parse_args()


def find_starts(image_length, size_of_stitch):
    """Find all starting positions for generation along the width of the image
    and return them.
    """
    starts = []
    pos = 0
    while pos <= image_length:
        starts.append(pos)
        pos += size_of_stitch
    return starts


def generate_color():
    """Generate and return random color if necessary.

    If the picture is set to generate with random line colors, generate three component colors using the
    color_randomer, which is dependent on the color_seed (currently not implemented separately) or the general seed
    depending on given arguments. Unite the component colors into a tuple and return it. Otherwise, if the lines are
    colored using a static line color, return it."""

    component_colors = [0] * 3
    for i, component_color in enumerate(component_colors):
        component_colors[i] = color_randomer.randrange(0, 255)
    return tuple(component_colors)


def draw_pattern(im, seed, start_coordinates):
    """Draw the hitomezashi pattern onto the canvas one line at a time.
    """

    draw = ImageDraw.Draw(im)
    randomer = random.Random(seed)
    current_color = line_color
    im_size = Vec2(im.size[0], im.size[1])
    for i, vector in enumerate(draw_vectors):
        addition_vector = Vec2(stitch_length, stitch_length) * vector
        for first_coordinate in start_coordinates[i - 1]:
            current_pos = Vec2(first_coordinate, first_coordinate) * draw_vectors[i - 1]
            draw_this_time = randomer.random() > 0.5
            while not current_pos > im_size:
                next_pos = current_pos + addition_vector
                if draw_this_time:
                    if args.rainbow:
                        current_color = generate_color()
                    draw.line((current_pos + Vec2(offset, offset)).toTuple() + (next_pos + offset_vector).toTuple(),
                              fill=current_color, width=stitch_width)
                if next_pos > im_size and not draw_this_time:
                    current_pos = Vec2(first_coordinate, first_coordinate) * draw_vectors[i - 1]
                    next_pos = Vec2(stitch_length * -1, stitch_length * -1) * vector + current_pos
                    draw.line((current_pos + Vec2(offset, offset)).toTuple() + (next_pos + offset_vector).toTuple(),
                              fill=current_color, width=stitch_width)
                    break
                current_pos = next_pos
                draw_this_time = not draw_this_time


def fill_pattern(im, fill_colors=None):
    px = im.load()
    fill_offset = int(stitch_length / 2)
    fill_point = Vec2(fill_offset, fill_offset)
    if fill_colors is None:
        while fill_point.x < im.size[0]:
            while fill_point.y < im.size[1]:
                if px[fill_point.x, fill_point.y] == bg_color:
                    ImageDraw.floodfill(im, (fill_point.x, fill_point.y), generate_color())
                fill_point.y += stitch_length
            fill_point.x += stitch_length
            fill_point.y = fill_offset
    else:
        prev_color = fill_colors[0]
        i = 1
        while fill_point.x < im.size[0]:
            while fill_point.y < im.size[1]:
                if px[fill_point.x, fill_point.y] not in fill_colors:
                    i = fill_colors.index(prev_color) + 1
                    if i >= len(fill_colors):
                        i = 0
                    ImageDraw.floodfill(im, (fill_point.x, fill_point.y), fill_colors[i])
                prev_color = px[fill_point.x, fill_point.y]
                fill_point.y += stitch_length

            fill_point.x += stitch_length
            fill_point.y = fill_offset
            prev_color = px[fill_point.x - stitch_length, fill_point.y]


def hexadecimal_to_color_tuple(hexadecimal_str):
    if hexadecimal_str.startswith("#"):
        hexadecimal_str = hexadecimal_str[1:]  # removes the hash symbol if it was used to indicate a hexadecimal value
    return tuple(bytes.fromhex(hexadecimal_str))


fill_tuples = []

if args.seed:
    seed = args.seed
if args.width:
    width = int(args.width)
if args.height:
    height = int(args.height)
if args.stitch:
    stitch_length = int(args.stitch)
if args.fill and not args.rainbowfill:
    if len(args.fill) > 2:
        print("Hint: Providing more than 2 fill colors is likely to break tileability")
        # TODO: Work out a way which doesn't break tileability
    for hexadecimal_input in args.fill:
        fill_tuples.append(hexadecimal_to_color_tuple(hexadecimal_input))
        # The following has to be done, so that setting the same infill color as the background color doesn't break
        # the infill functionality
        while True:
            if bg_color in fill_tuples:
                bg_color = tuple([random.randrange(0, 255)] * 3)
            else:
                break
if args.color:
    line_color = hexadecimal_to_color_tuple(args.color)

im = Image.new("RGB", (width, height), color=bg_color)
start_coordinates = [find_starts(width, stitch_length), find_starts(height, stitch_length)]

draw_pattern(im, seed, start_coordinates)

if args.rainbowfill:
    print("Hint: rainbow-filled patterns aren't tileable.")
    fill_pattern(im)
elif fill_tuples:
    fill_pattern(im, fill_tuples)
if not args.noshow:
    im.show()
if args.output:
    print(args.output)
    im.save(args.output)

# TODO: change some code documentation to make the workings of some functionalities clearer
