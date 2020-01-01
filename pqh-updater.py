import os, json, wget, brotli, sqlite3, hashlib, shutil, file_writer
from vendor.UnityPack import unitypack
from io import BytesIO
from PIL import Image


# EDIT BELOW AS NEEDED =================================================================================================
ACCOUNT_NAME = 'Administrator'
PRICONNE_QUEST_HELPER_DIRECTORY = 'C:/Users/Administrator/Desktop/priconne-quest-helper'
# ======================================================================================================================

# DO NOT EDIT UNLESS YOU KNOW WHAT YOU'RE DOING ========================================================================
MANIFEST_FILENAME = 'manifest.db'
OUTPUT_DIRECTORY_NAME = 'extract'
GAME_DIRECTORY_PATH = 'C:/Users/{0}/AppData/LocalLow/Cygames/PrincessConnectReDive'.format(ACCOUNT_NAME)
FILE_WHITELIST = []
# ======================================================================================================================


def create_directory(dir_path):
    if os.path.exists(dir_path):
        for file in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('DELETE FAILED', e)
    else:
        os.mkdir(dir_path)


def read_maifest_files(manifest_path):
    # COPY MANIFEST.DB (IN CASE DMM IS RUNNING)
    shutil.copy(manifest_path, OUTPUT_DIRECTORY_NAME)

    manifest = sqlite3.connect(os.path.join(OUTPUT_DIRECTORY_NAME, MANIFEST_FILENAME))
    cursor = manifest.cursor()
    cursor.execute('SELECT k FROM t')
    files = []

    for r in cursor.fetchall():
        for wl in FILE_WHITELIST:
            if str(r).find(wl) is not -1:
                files.append(r[0])
    manifest.close()

    return files


def read_manifest_files(manifest_path):
    # COPY MANIFEST.DB (IN CASE DMM IS RUNNING)
    shutil.copy(manifest_path, OUTPUT_DIRECTORY_NAME)

    manifest = sqlite3.connect(os.path.join(OUTPUT_DIRECTORY_NAME, MANIFEST_FILENAME))
    cursor = manifest.cursor()
    cursor.execute('SELECT k FROM t')
    files = []

    for r in cursor.fetchall():
        for wl in FILE_WHITELIST:
            if str(r).find(wl) is not -1:
                files.append(r[0])
    manifest.close()

    return files


def copy_manifest_files(files, game_directory, output_directory):
    file_amt = len(files)
    file_counter = 1

    hashes = [hashlib.sha1(f[f.find('/') + 1:].encode('utf-8')).hexdigest() for f in files]
    for hash, file in zip(hashes, files):
        file_folder = file[:file.find('/') + 1]
        source = game_directory + '/' + file_folder + hash
        destination = output_directory + '/' + file

        print('\t', str(file_counter).zfill(len(str(file_amt))) + '/' + str(file_amt), '\t', source, '->', destination)

        # MAKE DIRECTORY IF IT DOESN'T EXIST
        if not os.path.exists(output_directory + '/' + file_folder):
            os.mkdir(output_directory + '/' + file_folder)

        # ATTEMPT TO COPY
        try:
            shutil.copy(source, destination)
        except FileNotFoundError:
            print(source, destination, 'MISSING')

        file_counter += 1


def open_texture2d():
    try:
        from PIL import ImageOps
    except ImportError:
        print('WARNING: Pillow not available.\nInstall via \"pip install Pillow\"')
        return

    a_folder_path = OUTPUT_DIRECTORY_NAME + '/a'
    if not os.path.exists(a_folder_path):
        return

    for file in os.listdir(a_folder_path):
        with open(a_folder_path + '/' + file, 'rb') as f:
            bundle = unitypack.load(f)
            for asset in bundle.assets:
                for id, object in asset.objects.items():
                    if object.type == "Texture2D":
                        data = object.read()
                        try:
                            from PIL import ImageOps
                        except ImportError:
                            print('\tIMPORT ERROR FOR PILLOW ; IGNORING FILE')
                            continue
                        try:
                            image = data.image
                        except NotImplementedError:
                            print('\tNOT IMPLEMENTED ERROR ; IGNORING FILE')
                            continue
                        if image is None:
                            print('\tEMPTY IMAGE ; IGNORING FILE')
                            continue

                        img = ImageOps.flip(image)
                        output = BytesIO()
                        img.save(output, format='png')

                        if not os.path.exists('extract/a_decode'):
                            os.makedirs('extract/a_decode')

                        with open('extract/a_decode/' + str(file).replace('.unity3d', '') + '.png', 'wb') as fi:
                            fi.write(output.getvalue())
                            print('\t' + file, '->', 'extract/a_decode/' + str(file).replace('.unity3d', '') + '.png')


def extract_images():
    create_directory(OUTPUT_DIRECTORY_NAME)

    print('\nReading', MANIFEST_FILENAME)
    manifest_path = os.path.join(GAME_DIRECTORY_PATH, MANIFEST_FILENAME)
    files = read_maifest_files(manifest_path)

    print('\nCopying', len(files), 'files')
    copy_manifest_files(files, GAME_DIRECTORY_PATH, OUTPUT_DIRECTORY_NAME)

    print('\nDeleting', OUTPUT_DIRECTORY_NAME + '/' + MANIFEST_FILENAME)
    os.remove(os.path.join(OUTPUT_DIRECTORY_NAME, MANIFEST_FILENAME))

    print('\nDecrypting .unity3d files (Texture2D -> .png)')
    open_texture2d()


def get_new_images():
    print('\nSearching for new items...')
    new_items_exists = False
    if os.path.exists('data/translate_me.json'):
        new_items_exists = True
        with open('data/translate_me.json', encoding='utf-8') as translated_json:
            translated_items = json.load(translated_json)
            for key in translated_items:

                # CHECK IF ITEM IS EQUIPMENT
                if key[:2] == '10':
                    FILE_WHITELIST.append('icon_icon_equipment_' + key)  # EQUIPMENT
                    FILE_WHITELIST.append('icon_icon_equipment_11' + key[2:])  # EQUIPMENT FRAGMENT
                    FILE_WHITELIST.append('icon_icon_equipment_12' + key[2:])  # EQUIPMENT BLUEPRINT
                elif key[:2] == '31' or key[:2] == '32':
                    FILE_WHITELIST.append('icon_icon_item_' + key)  # MEMORY PIECE OR PURE MEMORY PIECE

    print('\nSearching for new characters...')
    new_characters = []
    with open('out/character_data.json', encoding='utf-8') as new_character_data_json:
        new_character_data = json.load(new_character_data_json)
        with open('data/character_data.json', encoding='utf-8') as old_character_data_json:
            old_character_data = json.load(old_character_data_json)
            for char_key in new_character_data:
                if char_key not in old_character_data:
                    unit_id = str(new_character_data[char_key]['unit_id'])
                    FILE_WHITELIST.append('unit_icon_unit_' + unit_id[:4] + '3' + unit_id[5:])
                    new_characters.append(char_key)

    # EXTRACT IMAGES
    if new_items_exists is True or len(new_characters) > 0:
        extract_images()

    # RENAME ITEM FILES IF THEY EXIST
    if new_items_exists is True:
        print('\nRenaming decrypted ITEM .png files...')
        with open('data/translate_me.json', encoding='utf-8') as translated_json:
            translated_items = json.load(translated_json)
            for key in translated_items:
                output_dir = 'out/images/items'
                en_translation = translated_items[key]["en_translation"]
                if en_translation != "":
                    image_name = en_translation.replace(' ', '_') + '.png'
                else:
                    image_name = key + '.png'

                if not os.path.exists('out/images'):
                    os.mkdir('out/images')
                if not os.path.exists(output_dir):
                    os.mkdir(output_dir)

                if key[:2] == '10':
                    # COPY/RENAME FULL EQUIPMENT IMAGE
                    source = 'extract/a_decode/icon_icon_equipment_' + key

                    try:
                        shutil.copy(source + '.png', output_dir + '/' + image_name)
                        print('\t', source + '.png', '->', output_dir + '/' + image_name)
                    except FileNotFoundError:
                        print('\t', source, 'MISSING')

                    # COPY/RENAME FRAGMENT IMAGE
                    if en_translation != "":
                        image_name = en_translation.replace(' ', '_') + '_Fragment' + '.png'
                    else:
                        image_name = key + '_Fragment.png'

                    source = 'extract/a_decode/icon_icon_equipment_'
                    if os.path.exists(source + '11' + key[2:] + '.png'):
                        try:
                            shutil.copy(source + '11' + key[2:] + '.png', output_dir + '/' + image_name)
                            print('\t', source + '11' + key[2:] + '.png', '->', output_dir + '/' + image_name)
                        except FileNotFoundError:
                            print('\t', source, 'MISSING')
                    elif os.path.exists(source + '12' + key[2:] + '.png'):
                        try:
                            shutil.copy(source + '12' + key[2:] + '.png', output_dir + '/' + image_name)
                            print('\t', source + '12' + key[2:] + '.png', '->', output_dir + '/' + image_name)
                        except FileNotFoundError:
                            print('\t', source, 'MISSING')
                elif key[:2] == '31' or key[:2] == '32':
                    # COPY/RENAME MEMORY PIECE OR PURE MEMORY PIECE IMAGE
                    source = 'extract/a_decode/icon_icon_item_' + key
                    try:
                        shutil.copy(source + '.png', output_dir + '/' + image_name)
                        print('\t', source + '.png', '->', output_dir + '/' + image_name)
                    except FileNotFoundError:
                        print('\t', source, 'MISSING')

    if len(new_characters) > 0:
        print('\nRenaming decrypted UNIT .png files...')
        with open('out/character_data.json', encoding='utf-8') as new_character_data_json:
            new_character_data = json.load(new_character_data_json)
            output_dir = 'out/images/unit_icon'

            if not os.path.exists('out/images'):
                os.mkdir('out/images')
            if not os.path.exists(output_dir):
                os.mkdir(output_dir)

            for char_key in new_characters:
                unit_id = str(new_character_data[char_key]['unit_id'])
                unit_name = str(new_character_data[char_key]['name']).replace(' ', '_')
                unit_thematic = str(new_character_data[char_key]['thematic']).replace(' ', '_')
                unit_image = 'unit_icon_unit_' + unit_id[:4] + '3' + unit_id[5:]
                source = 'extract/a_decode/' + unit_image + '.png'
                if unit_thematic is not '':
                    destination = output_dir + '/' + unit_thematic + '_' + unit_name + '.png'
                else:
                    destination = output_dir + '/' + unit_name + '.png'
                try:
                    shutil.copy(source, destination)
                    print('\t', source, '->', destination)
                except FileNotFoundError:
                    print('\t', source, 'MISSING')


def convert_to_webp():
    image_quality = 70
    compression_method = 6  # SLOWEST/BEST

    # CONVERT ITEM IMAGES
    output_item_dir = 'out/images/items'
    if os.path.exists(output_item_dir):
        if not os.path.exists(output_item_dir + '_webp'):
            os.mkdir(output_item_dir + '_webp')
        print('\nConverting ITEM images to .webp with image quality ' + str(image_quality) + ' and compression method '
              + str(compression_method))
        for item_image in os.listdir(output_item_dir):
            im_path = output_item_dir + '/' + item_image
            im_out_path = output_item_dir + '_webp/' + item_image.replace('.png', '.webp')
            im = Image.open(im_path)
            im.save(im_out_path, 'webp', quality=image_quality, method=compression_method)
            print('\t', im_path, '->', im_out_path)

    # CONVERT UNIT IMAGES
    output_unit_dir = 'out/images/unit_icon'
    if os.path.exists(output_unit_dir):
        if not os.path.exists(output_unit_dir + '_webp'):
            os.mkdir(output_unit_dir + '_webp')
        print('\nConverting UNIT images to .webp with image quality ' + str(image_quality) + ' and compression method '
              + str(compression_method))
        for unit_image in os.listdir(output_unit_dir):
            im_path = output_unit_dir + '/' + unit_image
            im_out_path = output_unit_dir + '_webp/' + unit_image.replace('.png', '.webp')
            im = Image.open(im_path)
            im.save(im_out_path, 'webp', quality=image_quality, method=compression_method)
            print('\t', im_path, '->', im_out_path)


def run():
    # DELETE 'out' DIRECTORY IF IT DOES EXIST
    if os.path.exists('out'):
        print('\nDeleting existing \"out\" directory...')
        shutil.rmtree('out')

    # CREATE 'data' DIRECTORY IF IT DOES NOT EXIST
    if not os.path.exists('data'):
        print('\nCreating \"data\" directory...')
        os.mkdir('data')

    # CHECK FOR REQUIRED SETUP FILES FROM priconne-quest-helper DIRECTORY
    print('\nSearching for required setup files...')
    can_run = True
    if not os.path.exists(PRICONNE_QUEST_HELPER_DIRECTORY + '/data/character_data.json'):
        print('\t- \"priconne-quest-helper/data/character_data.json\" NOT FOUND')
        can_run = False
    if not os.path.exists(PRICONNE_QUEST_HELPER_DIRECTORY + '/data/equipment_data.json'):
        print('\t- \"priconne-quest-helper/data/equipment_data.json\" NOT FOUND')
        can_run = False
    if not os.path.exists(PRICONNE_QUEST_HELPER_DIRECTORY + '/language/ja.json'):
        print('\t- \"priconne-quest-helper/language/ja.json\" NOT FOUND')
        can_run = False
    if can_run is False:
        print('\n PROGRAM ENDING : Cannot locate all required setup files.')
        print('\t- Check the PRICONNE_QUEST_HELPER_DIRECTORY variable to make sure it\'s correct.')
        return
    print('')

    # COPY REQUIRED SETUP FILES FROM priconne-quest-helper DIRECTORY
    print('Copying setup files to \"data\" directory...')
    try:
        shutil.copy(PRICONNE_QUEST_HELPER_DIRECTORY + '/data/character_data.json', 'data/character_data.json')
        shutil.copy(PRICONNE_QUEST_HELPER_DIRECTORY + '/data/equipment_data.json', 'data/equipment_data.json')
        shutil.copy(PRICONNE_QUEST_HELPER_DIRECTORY + '/language/ja.json', 'data/ja.json')
    except FileNotFoundError:
        print('\nPROGRAM ENDING : Cannot locate all required setup files.')
        return
    print('')

    # CREATE JSON FILES
    print('Creating data files...')
    fw = file_writer.FileWriter()

    print('\nWorking on \"equipment_data.json\"...')
    fw.write_equipment_data()

    print('\nWorking on \"character_data.json\"...')
    fw.write_character_data()

    print('\nWorking on \"quest_data.json\"...')
    fw.write_quest_data()

    fw.close_db_connection()

    # GRAB NEW IMAGES
    get_new_images()

    # CONVERT TO WEBP
    convert_to_webp()

    # CLEAN FILES
    print('\nCleaning unnecessary files...')
    if os.path.exists('data'):
        shutil.rmtree('data')
    if os.path.exists('extract'):
        shutil.rmtree('extract')


run()
# PROGRAM COMPLETE
input("\nFiles Successfully Generated! (Press Enter to Exit...)")
