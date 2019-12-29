import os, json, wget, brotli, sqlite3, hashlib, shutil, file_writer
from vendor.UnityPack import unitypack
from io import BytesIO


# EDIT BELOW AS NEEDED =================================================================================================
ACCOUNT_NAME = 'Administrator'
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

        print(str(file_counter).zfill(len(str(file_amt))) + '/' + str(file_amt), '\t', source, '->', destination)

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
                        print('Decoding', file)

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
                            print('\tSaved file as', 'extract/a_decode/' + str(file).replace('.unity3d', '') + '.png')


def run():
    # CREATE 'data' DIRECTORY IF IT DOES NOT EXIST
    if not os.path.exists('data'):
        os.mkdir('data')

    # CHECK IF REQUIRED SETUP FILES ARE AVAILABLE
    can_run = True

    if not os.path.exists('data/equipment_data.json'):
        print('\"data/equipment_data.json\" NOT FOUND')
        print('\t- Place the current \"equipment_data.json\" from priconne-quest-helper in this location.')
        print('\t- The inclusion of this file is necessary to add existing English Translations for the new JSON.')
        can_run = False

    if not os.path.exists('data/ja.json'):
        print('\"data/ja.json\" NOT FOUND')
        print('\t- Place the current \"ja.json\" from priconne-quest-helper in this location.')
        print('\t- The inclusion of this file is necessary in the compilation of character_data.json.')
        print('\t- ja.json MUST BE UPDATED to include all new characters names and thematics.')
        can_run = False

    if can_run is False:
        print('\nFix the listed errors and restart the program to continue.')
        return

    # CREATE JSON FILES
    print('Creating data files...')
    fw = file_writer.FileWriter()

    print('\nWorking on \"equipment_data.json\"...')
    fw.write_equipment_data()

    print('\nWorking on \"character_data.json\"...')
    fw.write_character_data()

    print('\nWorking on \"quest_data.json\"...')
    fw.write_quest_data()

    # GRAB NEW ITEM IMAGES
    with open('data/translate_me.json', encoding='utf-8') as translated_json:
        translated_items = json.load(translated_json)
        for key in translated_items:

            # CHECK IF ITEM IS EQUIPMENT
            if key[:2] == '10':
                FILE_WHITELIST.append('icon_icon_equipment_' + key)         # EQUIPMENT
                FILE_WHITELIST.append('icon_icon_equipment_11' + key[2:])   # EQUIPMENT FRAGMENT
                FILE_WHITELIST.append('icon_icon_equipment_12' + key[2:])   # EQUIPMENT BLUEPRINT
            elif key[:2] == '31' or key[:2] == '32':
                FILE_WHITELIST.append('icon_icon_item_' + key)              # MEMORY PIECE OR PURE MEMORY PIECE

    if os.path.exists('data/translate_me.json'):
        create_directory(OUTPUT_DIRECTORY_NAME)

        print('\nReading', MANIFEST_FILENAME)
        manifest_path = os.path.join(GAME_DIRECTORY_PATH, MANIFEST_FILENAME)
        files = read_maifest_files(manifest_path)

        print('\nCopying', len(files), 'files')
        asset_path = GAME_DIRECTORY_PATH
        copy_manifest_files(files, GAME_DIRECTORY_PATH, OUTPUT_DIRECTORY_NAME)

        print('\nDeleting', OUTPUT_DIRECTORY_NAME + '/' + MANIFEST_FILENAME)
        os.remove(os.path.join(OUTPUT_DIRECTORY_NAME, MANIFEST_FILENAME))

        print('\nDecrypting .unity3d files (Texture2D -> .png)')
        open_texture2d()

        # RENAME FILES
        with open('data/translate_me.json', encoding='utf-8') as translated_json:
            translated_items = json.load(translated_json)
            for key in translated_items:
                output_dir = 'out/images'
                en_translation = translated_items[key]["en_translation"]
                if en_translation != "":
                    image_name = en_translation.replace(' ', '_') + '.png'
                else:
                    image_name = key + '.png'

                if not os.path.exists(output_dir):
                    os.mkdir(output_dir)

                if key[:2] == '10':
                    # COPY/RENAME FULL EQUIPMENT IMAGE
                    source = 'extract/a_decode/icon_icon_equipment_' + key

                    try:
                        shutil.copy(source + '.png', output_dir + '/' + image_name)
                        print(source + '.png', '->', output_dir + '/' + image_name)
                    except FileNotFoundError:
                        print(source, 'MISSING')

                    # COPY/RENAME FRAGMENT IMAGE
                    if en_translation != "":
                        image_name = en_translation.replace(' ', '_') + '_Fragment' + '.png'
                    else:
                        image_name = key + '_Fragment.png'

                    source = 'extract/a_decode/icon_icon_equipment_'
                    if os.path.exists(source + '11' + key[2:] + '.png'):
                        try:
                            shutil.copy(source + '11' + key[2:] + '.png', output_dir + '/' + image_name)
                            print(source + '11' + key[2:] + '.png', '->', output_dir + '/' + image_name)
                        except FileNotFoundError:
                            print(source, 'MISSING')
                    elif os.path.exists(source + '12' + key[2:] + '.png'):
                        try:
                            shutil.copy(source + '12' + key[2:] + '.png', output_dir + '/' + image_name)
                            print(source + '12' + key[2:] + '.png', '->', output_dir + '/' + image_name)
                        except FileNotFoundError:
                            print(source, 'MISSING')

                elif key[:2] == '31' or key[:2] == '32':
                    # COPY/RENAME MEMORY PIECE OR PURE MEMORY PIECE IMAGE
                    source = 'extract/a_decode/icon_icon_item_' + key
                    try:
                        shutil.copy(source + '.png', output_dir + '/' + image_name)
                        print(source + '.png', '->', output_dir + '/' + image_name)
                    except FileNotFoundError:
                        print(source, 'MISSING')

    # CLEAN FILES
    print('\nCleaning unnecessary files...')
    if os.path.exists('data/equipment_data.json'):
        os.remove('data/equipment_data.json')
    if os.path.exists('data/ja.json'):
        os.remove('data/ja.json')
    if os.path.exists('data/translate_me.json'):
        os.remove('data/translate_me.json')
    if os.path.exists('extract'):
        shutil.rmtree('extract')

    # PROGRAM COMPLETE
    input("\nFiles Successfully Generated! (Press Enter to Exit...)")


run()
