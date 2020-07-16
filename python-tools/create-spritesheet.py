"""
HOW TO USE:
`python create-spritesheet.py [item | unit] <css_path> <setup_image_directory> <output_directory_path>`

REQUIRED DEPENDENCIES:
- Pillow    `pip install Pillow`
"""


import sys, json, re
from PIL import Image
from datetime import date


def write_css_header(css_path):
    css = open(css_path, 'w')
    css.write("/*\n * DATA CSS | FOR USE IN priconne-quest-helper | GENERATED " + str(date.today()) + "\n *\n" +
              " * NOTE: ALL IMAGE CLASS NAMES ARE LOWERCASE, HAVE NO APOSTROPHES, AND NON-ALPHANUMERIC CHARACTERS"
              + " ARE '-'\n */\n\n")
    css.close()


def create_item_spritesheet(css_path, setup_image_dir, output_dir):
    # SPRITE SHEET DETAILS
    spacing = 2         # PIXEL SPACING BETWEEN THE FULL EQUIPMENT / FRAGMENT
    group_spacing = 5   # PIXEL SPACING BETWEEN EACH GROUP OF (FULL EQUIPMENT / FRAGMENT)
    max_row = 10        # MAX AMOUNT OF GROUPS PER ROW
    image_size = 48     # IMAGE SIZE OF EACH ITEM ; i.e. 48 == 48x48 ITEMS

    # WRITE GENERAL CSS FILE HEADER
    write_css_header(css_path)

    # WRITE ITEM HEADER
    css = open(css_path, "a")
    css.write("/*\n * ITEMS\n *\n" +
              " * USAGE: <i class=\"item-sprite is__{item-name}\"></i>\n" +
              " * EXAMPLE: <i class=\"item-sprite is__iron-blade\"></i>        | Iron Blade\n" +
              " *          <i class=\"item-sprite is__t-r-na-n-g-dagger\"></i> | Tír na nÓg Dagger\n" +
              " *          <i class=\"item-sprite is__dawns-holy-sword\"></i>  | Dawn's Holy Sword\n" +
              " */\n")

    # WRITE .item-sprite DETAILS
    css.write(".item-sprite{width:" + str(image_size) + "px;height:" + str(image_size) + "px;display:inline-block;" +
              "background-repeat:no-repeat}" +
              ".no-webp .item-sprite{background-image:url(\"../images/webpage/spritesheets/items.png\")}" +
              ".webp .item-sprite{background-image:url(\"../images/webpage_webp/spritesheets/items.webp\")}")

    # BEGIN SPRITESHEET
    spritesheet = Image.new("RGBA", (0, image_size))
    max_width = None
    pointer_x = 0
    pointer_y = 0
    counter = 0

    with open(output_dir + '/data/equipment_data.json', encoding='utf-8') as equipment_json:
        equipment_data = json.load(equipment_json)

        # ADD PLACEHOLDER
        image = Image.open(setup_image_dir + "/Placeholder.png")
        frag_image = Image.new('RGBA', (image_size, image_size))
        image = image.resize((image_size, image_size), Image.ANTIALIAS)
        (ss_width, ss_height) = spritesheet.size
        width = ss_width + (image_size * 2) + spacing + group_spacing
        ss_new = Image.new("RGBA", (width, ss_height))
        ss_new.paste(spritesheet, (0, 0))
        ss_new.paste(image, (pointer_x, pointer_y))
        pointer_x += image_size + spacing
        ss_new.paste(frag_image, (pointer_x, pointer_y))
        pointer_x += image_size + group_spacing
        spritesheet = ss_new
        image.close()
        frag_image.close()
        counter += 1

        # GO THROUGH ALL ITEMS NOW
        for equip_key in equipment_data:
            fragment_name = None
            sprite_frag_class = None
            item_name = equipment_data[equip_key]["name"].replace(" ", "_")
            image = Image.open(setup_image_dir + "/" + item_name + ".png")
            sprite_class = get_item_sprite_class(item_name)
            if equipment_data[equip_key]["has_fragments"]:
                fragment_name = (equipment_data[equip_key]["name"] + "_Fragment").replace(" ", "_")
                frag_image = Image.open(setup_image_dir + "/" + fragment_name + ".png")
                sprite_frag_class = get_item_sprite_class(fragment_name)
            else:
                frag_image = Image.new('RGBA', (image_size, image_size))

            image = image.resize((image_size, image_size), Image.ANTIALIAS)
            frag_image = frag_image.resize((image_size, image_size), Image.ANTIALIAS)

            (ss_width, ss_height) = spritesheet.size
            if counter % max_row == 0 and counter != 0:
                pointer_x = 0
                pointer_y += image_size + group_spacing
                ss_height = ss_height + group_spacing + image_size
                if max_width is None:
                    max_width = ss_width - group_spacing

            # ADD FULL ITEM
            if max_width is None:
                width = ss_width + (image_size * 2) + spacing + group_spacing
            else:
                width = max_width

            ss_new = Image.new("RGBA", (width, ss_height))
            ss_new.paste(spritesheet, (0, 0))

            ss_new.paste(image, (pointer_x, pointer_y))
            if pointer_x == 0 and pointer_y == 0:
                css.write(sprite_class + "{background-position:" + str(pointer_x) + " " + str(pointer_y) + "}")
            elif pointer_x == 0 and pointer_y != 0:
                css.write(sprite_class + "{background-position:" + str(pointer_x) + " -" + str(pointer_y) + "px}")
            elif pointer_x != 0 and pointer_y == 0:
                css.write(sprite_class + "{background-position:-" + str(pointer_x) + "px " + str(pointer_y) + "}")
            else:
                css.write(sprite_class + "{background-position:-" + str(pointer_x) + "px -" + str(pointer_y) + "px}")

            pointer_x += image_size + spacing

            # ADD FRAGMENT
            ss_new.paste(frag_image, (pointer_x, pointer_y))
            if fragment_name is not None:
                if pointer_x == 0 and pointer_y == 0:
                    css.write(sprite_frag_class + "{background-position:" + str(pointer_x) + " " + str(pointer_y) + "}")
                elif pointer_x == 0 and pointer_y != 0:
                    css.write(sprite_frag_class + "{background-position:" + str(pointer_x) + " -" + str(pointer_y)
                              + "px}")
                elif pointer_x != 0 and pointer_y == 0:
                    css.write(sprite_frag_class + "{background-position:-" + str(pointer_x) + "px " + str(pointer_y)
                              + "}")
                else:
                    css.write(sprite_frag_class + "{background-position:-" + str(pointer_x) + "px -" + str(pointer_y)
                              + "px}")
            pointer_x += image_size + group_spacing
            spritesheet = ss_new

            # CLOSE IMAGE SINCE WE'RE DONE USING IT
            image.close()
            frag_image.close()
            counter += 1

        # SPRITESHEET GENERATION COMPLETE
        spritesheet.save(output_dir + "/images/webpage/spritesheets/items.png")
        spritesheet.save(output_dir + "/images/webpage_webp/spritesheets/items.webp", 'webp', quality=70, method=6)
        css.close()


def get_item_sprite_class(item_name):
    return ".is__" + re.sub('[^0-9a-zA-Z]+', '-', item_name.replace("'", "")).lower()


def create_unit_spritesheet(css_path, setup_image_dir, output_dir):
    # SPRITESHEET DETAILS
    spacing = 2         # PIXEL SPACING BETWEEN EACH UNIT ICON
    max_row = 16        # MAX AMOUNT OF UNIT ICONS PER ROW
    image_size = 64     # IMAGE SIZE OF EACH UNIT ICON ; i.e. 64 = 64x64 UNIT ICONS

    # WRITE UNIT ICON HEADER
    css = open(css_path, "a")
    css.write("\n\n/*\n * UNITS\n *\n" +
              " * USAGE: <i class=\"unit-sprite us__{unit-name}\"></i>\n" +
              " * EXAMPLE: <i class=\"unit-sprite us__miyako\"></i>          | Miyako\n" +
              " *          <i class=\"unit-sprite us__summer-pecorine\"></i> | Pecorine (Summer)\n" +
              " *          <i class=\"unit-sprite us__new-year-rei\"></i>    | Rei (New Year)\n" +
              " */\n")

    # WRITE .unit-sprite DETAILS
    css.write(".unit-sprite{width:" + str(image_size) + "px;height:" + str(image_size) + "px;display:inline-block;" +
              "background-repeat:no-repeat}" +
              ".no-webp .unit-sprite{background-image:url(\"../images/webpage/spritesheets/units.png\")}" +
              ".webp .unit-sprite{background-image:url(\"../images/webpage_webp/spritesheets/units.webp\")}")

    # BEGIN SPRITESHEET
    spritesheet = Image.new("RGBA", (0, image_size))
    max_width = None
    pointer_x = 0
    pointer_y = 0
    counter = 0

    with open(output_dir + '/data/character_data.json', encoding='utf-8') as character_json:
        character_data = json.load(character_json)

        # ADD PLACEHOLDER
        image = Image.open(setup_image_dir + "/Placeholder.png")
        image = image.resize((image_size, image_size), Image.ANTIALIAS)
        (ss_width, ss_height) = spritesheet.size
        width = ss_width + image_size + spacing
        ss_new = Image.new("RGBA", (width, ss_height))
        ss_new.paste(spritesheet, (0, 0))
        ss_new.paste(image, (pointer_x, pointer_y))
        pointer_x += image_size + spacing
        spritesheet = ss_new
        image.close()
        counter += 1

        # GO THROUGH ALL UNITS NOW
        for unit_key in character_data:
            unit_name = character_data[unit_key]["name"].replace(" ", "_")
            thematic = character_data[unit_key]["thematic"].replace(" ", "_")
            if thematic == "":
                file_name = unit_name
            else:
                file_name = thematic + "_" + unit_name
            image = Image.open(setup_image_dir + "/" + file_name + ".png")
            sprite_class = get_unit_sprite_class(file_name)

            image = image.resize((image_size, image_size), Image.ANTIALIAS)

            (ss_width, ss_height) = spritesheet.size
            if counter % max_row == 0 and counter != 0:
                pointer_x = 0
                pointer_y += image_size + spacing
                ss_height = ss_height + spacing + image_size
                if max_width is None:
                    max_width = ss_width - spacing

            # ADD FULL ITEM
            if max_width is None:
                width = ss_width + image_size + spacing
            else:
                width = max_width

            ss_new = Image.new("RGBA", (width, ss_height))
            ss_new.paste(spritesheet, (0, 0))

            ss_new.paste(image, (pointer_x, pointer_y))
            if pointer_x == 0 and pointer_y == 0:
                css.write(sprite_class + "{background-position:" + str(pointer_x) + " " + str(pointer_y) + "}")
            elif pointer_x == 0 and pointer_y != 0:
                css.write(sprite_class + "{background-position:" + str(pointer_x) + " -" + str(pointer_y) + "px}")
            elif pointer_x != 0 and pointer_y == 0:
                css.write(sprite_class + "{background-position:-" + str(pointer_x) + "px " + str(pointer_y) + "}")
            else:
                css.write(sprite_class + "{background-position:-" + str(pointer_x) + "px -" + str(pointer_y) + "px}")

            pointer_x += image_size + spacing
            spritesheet = ss_new

            # CLOSE IMAGE SINCE WE'RE DONE USING IT
            image.close()
            counter += 1

        # SPRITESHEET GENERATION COMPLETE
        spritesheet.save(output_dir + "/images/webpage/spritesheets/units.png")
        spritesheet.save(output_dir + "/images/webpage_webp/spritesheets/units.webp", 'webp', quality=70, method=6)
        css.close()


def get_unit_sprite_class(unit_name):
    return ".us__" + re.sub('[^0-9a-zA-Z]+', '-', unit_name.replace("'", "")).lower()


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Not enough arguments.")
        sys.exit()

    if sys.argv[1] == "item":
        create_item_spritesheet(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "unit":
        create_unit_spritesheet(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print("Unknown spritesheet type.")
