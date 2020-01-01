import database
import os
import json


class FileWriter:
    def __init__(self):
        self.db = database.Database()
        self.cursor = self.db.get_cursor()

        # DICTIONARY OF DATA TYPES
        self.equipment_dictionary = {
            'FULL_EQUIPMENT': '10',
            'EQUIPMENT_FRAGMENT': '11',
            'EQUIPMENT_BLUEPRINT': '12',
            'PRINCESS_HEART': '14',

            'FRAGMENT_SUFFIX': ' （欠片） ',
            'BLUEPRINT_SUFFIX': 'の設計図',
            
            'rarity-1': 'common',
            'rarity-2': 'copper',
            'rarity-3': 'silver',
            'rarity-4': 'gold',
            'rarity-5': 'purple',
        }

        # QUEST_DATA GLOBAL VARIABLES
        self.quest_info = None
        self.wave_group_info = None
        self.enemy_reward_info = None

        # FILE PATHS
        self.equipment_data_path = 'out/equipment_data.json'
        self.character_data_path = 'out/character_data.json'
        self.quest_data_path = 'out/quest_data.json'
        self.translate_file_path = 'data/translate_me.json'

        # COMPLETED DICTIONARIES
        self.equipment_data = None
        self.character_data = None
        self.quest_data = None

    def __del__(self):
        self.db.close_connection()

    @staticmethod
    def save_file(dictionary, output_file_path):
        # CREATE 'out' DIRECTORY IF IT DOES NOT EXIST
        if not os.path.exists('out'):
            os.mkdir('out')

        # OVERWRITE EXISTING FILE IF EXISTS
        if os.path.exists(output_file_path):
            os.remove(output_file_path)

        # SAVE FILE
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(dictionary, f, ensure_ascii=False, indent=4)

        # PRINT MESSAGE
        print(output_file_path + ' created: `' + json.dumps(dictionary) + '`')

    def get_sql_answer(self, command):
        self.cursor.execute(command)
        return self.cursor.fetchall()

    def close_db_connection(self):
        self.db.close_connection()

    @staticmethod
    def equipment_get_type(full_id):
        return str(full_id)[:-4]

    @staticmethod
    def equipment_get_rarity_id(full_id):
        return str(full_id)[2:-3]

    @staticmethod
    def equipment_get_item_id(full_id):
        return str(full_id)[2:]

    def rarity_id_to_rarity_string(self, rarity_id):
        return self.equipment_dictionary['rarity-' + rarity_id]

    def write_equipment_data(self):
        # ADD EQUIPMENT DATA
        answer = self.get_sql_answer("SELECT equipment_id, equipment_name FROM equipment_data")
        dictionary = {}
        common_counter = 1
        copper_counter = 1
        silver_counter = 1
        gold_counter = 1
        purple_counter = 1
        for i in answer:
            full_id = i[0]
            item_id = self.equipment_get_item_id(full_id)
            item_type = self.equipment_get_type(full_id)
            if item_type == self.equipment_dictionary.get('FULL_EQUIPMENT'):
                # GET ID
                rarity_string = self.rarity_id_to_rarity_string(self.equipment_get_rarity_id(full_id))

                # GET COUNTER
                counter = -1
                if rarity_string == self.equipment_dictionary.get('rarity-1'):
                    counter = common_counter
                if rarity_string == self.equipment_dictionary.get('rarity-2'):
                    counter = copper_counter
                if rarity_string == self.equipment_dictionary.get('rarity-3'):
                    counter = silver_counter
                if rarity_string == self.equipment_dictionary.get('rarity-4'):
                    counter = gold_counter
                if rarity_string == self.equipment_dictionary.get('rarity-5'):
                    counter = purple_counter

                # WRITE DICTIONARY ENTRY AND STORE INTO MAIN DICTIONARY
                dictionary_entry = {
                    "name_jp": str(i[1]),
                    "name": "",
                    "id": rarity_string + '-' + str(counter),
                    "has_fragments": False,
                    "req_pieces": 1,
                    "req_items": []
                }
                dictionary[str(full_id)] = dictionary_entry

                # INCREMENT COUNTER
                if rarity_string == self.equipment_dictionary.get('rarity-1'):
                    common_counter += 1
                if rarity_string == self.equipment_dictionary.get('rarity-2'):
                    copper_counter += 1
                if rarity_string == self.equipment_dictionary.get('rarity-3'):
                    silver_counter += 1
                if rarity_string == self.equipment_dictionary.get('rarity-4'):
                    gold_counter += 1
                if rarity_string == self.equipment_dictionary.get('rarity-5'):
                    purple_counter += 1
            else:
                is_equipment_fragment = item_type == self.equipment_dictionary.get('EQUIPMENT_FRAGMENT')
                is_equipment_blueprint = item_type == self.equipment_dictionary.get('EQUIPMENT_BLUEPRINT')
                if is_equipment_fragment or is_equipment_blueprint:
                    # IF EQUIPMENT FRAGMENT/BLUEPRINT, SET FRAGMENTS TO TRUE
                    dictionary["10" + str(item_id)]["has_fragments"] = True

        # GET CHARACTER MEMORY PIECES AVAILABLE FROM HARD / VERY HARD QUESTS
        memory_piece_whitelist = []
        answer = self.get_sql_answer("SELECT quest_id, reward_image_1 FROM quest_data")
        for i in answer:
            quest_id = i[0]
            quest_type = str(quest_id)[:-6]
            if quest_type == '12' or quest_type == '13':
                if i[1] is not 0:
                    memory_piece_whitelist.append(i[1])

        # ADD CHARACTER MEMORY PIECES
        answer = self.get_sql_answer("SELECT item_id, item_name, item_type FROM item_data")
        misc_counter = 1
        for i in answer:
            if i[2] == 11 or i[2] == 18:
                if i[0] in memory_piece_whitelist:
                    dictionary_entry = {
                        "name": "",
                        "name_jp": str(i[1]),
                        "id": 'misc-' + str(misc_counter),
                        "has_fragments": False,
                        "req_pieces": 1,
                        "req_items": []
                    }
                    dictionary[str(i[0])] = dictionary_entry
                    misc_counter += 1

        # ADD ENGLISH TRANSLATION FROM OLD EQUIPMENT FILE
        with open('data/equipment_data.json', encoding='utf-8') as equip_json:
            old_equipment_data = json.load(equip_json)
            for key in old_equipment_data:
                dictionary[key]["name"] = old_equipment_data[key]["name"]

            # CHECK IF THE EQUIPMENT COUNT IS DIFFERENT
            if len(dictionary) > len(old_equipment_data):
                # NEW ITEMS EXIST, GENERATE WHAT NEEDS TO BE TRANSLATED
                translate_json = {}
                for key in dictionary:
                    if dictionary[key]["name"] is "":
                        translate_entry = {
                            "name_jp": dictionary[key]["name_jp"],
                            "en_translation": ""
                        }
                        translate_json[key] = translate_entry
                with open(self.translate_file_path, 'w', encoding='utf-8') as f:
                    json.dump(translate_json, f, ensure_ascii=False, indent=4)
                input('\"data/translate_me.json\" has been created. Translate the items and press ENTER to continue...')
                with open('data/translate_me.json', encoding='utf-8') as translated_json:
                    translated_items = json.load(translated_json)
                    for key in translated_items:
                        dictionary[key]["name"] = translated_items[key]["en_translation"]

        # ADD REQUIRED FRAGMENTS
        command = "SELECT equipment_id, condition_equipment_id_1, consume_num_1 FROM equipment_craft"
        answer = self.get_sql_answer(command)
        for i in answer:
            if str(i[0])[:-4] == "10":
                # CHECK IF CONDITION EQUIPMENT 1 IS THE SAME AS EQUIPMENT ID
                if str(i[1])[2:] == str(i[0])[2:]:
                    dictionary[str(i[0])]["req_pieces"] = i[2]
                else:
                    # IF CONDITIONAL EQUIPMENT 1 DOES NOT MATCH EQUIPMENT ID MEANS THERE ARE NO FRAGMENTS
                    # SET CONDITIONAL EQUIPMENT 1 AS A REQUIRED ITEM INSTEAD
                    dictionary[str(i[0])]["req_pieces"] = 0
                    req_items_array = dictionary[str(i[0])]["req_items"]
                    req_item_name = dictionary[str(i[1])]["name"]
                    req_items_array.append(req_item_name)
                    dictionary[str(i[0])]["req_items"] = req_items_array

        # ADD REQUIRED ITEMS
        command = "SELECT equipment_id, condition_equipment_id_2, condition_equipment_id_3, condition_equipment_id_4 "
        command += "FROM equipment_craft"
        answer = self.get_sql_answer(command)
        for i in answer:
            if str(i[0])[:-4] == "10":
                req_items_array = dictionary[str(i[0])]["req_items"]
                # CONDITION EQUIPMENT 2
                if i[1] is not 0:
                    req_item_name = dictionary[str(i[1])]["name"]
                    req_items_array.append(req_item_name)

                # CONDITION EQUIPMENT 3
                if i[2] is not 0:
                    req_item_name = dictionary[str(i[2])]["name"]
                    req_items_array.append(req_item_name)

                # CONDITION EQUIPMENT 4
                if i[3] is not 0:
                    req_item_name = dictionary[str(i[3])]["name"]
                    req_items_array.append(req_item_name)

                # ADD REQUIRED ITEMS BACK TO DICTIONARY
                dictionary[str(i[0])]["req_items"] = req_items_array

        # SAVE FILE
        self.save_file(dictionary, self.equipment_data_path)
        self.equipment_data = dictionary

    def write_character_data(self):
        dictionary = {}
        # READ data/ja.json TO GET DICTIONARY OF CHARACTER NAMES AND THEMATICS
        character_name_ja_to_eng_dictionary = {}
        thematic_ja_to_eng_dictionary = {}
        with open('data/ja.json', encoding='utf-8') as language_json:
            ja_data = json.load(language_json)
            # BUILD CHARACTER NAME (JP) -> ENG
            character_name_data = ja_data["character_names"]
            for key in character_name_data:
                character_name_ja_to_eng_dictionary[character_name_data[key]] = key
            # BUILD THEMATIC (JP) -> ENG
            thematic_data = ja_data["thematics"]
            for key in thematic_data:
                thematic_ja_to_eng_dictionary[thematic_data[key]] = key

        # CREATE UNIT DATA DICTIONARY
        unit_id_to_unit_name = {}
        answer = self.get_sql_answer("SELECT unit_id, unit_name FROM unit_data")
        for i in answer:
            # UNIT_ID ABOVE 190,000 ARE NPCS OR STORY UNITS
            if i[0] < 190000:
                unit_id_to_unit_name[i[0]] = i[1]

        # GET UNIT PROMOTION REQUIREMENTS
        command = "SELECT unit_id, promotion_level, "
        command += "equip_slot_1, equip_slot_2, equip_slot_3, "
        command += "equip_slot_4, equip_slot_5, equip_slot_6 "
        command += "FROM unit_promotion"
        answer = self.get_sql_answer(command)
        for i in answer:
            # UNIT_ID ABOVE 400,000 ARE NPCS OR STORY UNITS
            # CHECK EVERYTHING BELOW 190,000 REGARDLESS TO MATCH UNIT DATA DICTIONARY
            if i[0] < 190000:
                # VARIABLES IMPORTANT FOR JSON
                # unit_key = None
                # name_en = None
                thematic_en = ""
                # name_jp = None
                thematic_jp = ""

                # DATA FOUND IN DATABASE
                unit_id = i[0]
                full_unit_name = unit_id_to_unit_name[unit_id]  # name_jp（thematic_jp）
                promotion_level = i[1]
                equip_slot_1 = self.equipment_data[str(i[2])]["name"] if not i[2] == 999999 else ""
                equip_slot_2 = self.equipment_data[str(i[3])]["name"] if not i[3] == 999999 else ""
                equip_slot_3 = self.equipment_data[str(i[4])]["name"] if not i[4] == 999999 else ""
                equip_slot_4 = self.equipment_data[str(i[5])]["name"] if not i[5] == 999999 else ""
                equip_slot_5 = self.equipment_data[str(i[6])]["name"] if not i[6] == 999999 else ""
                equip_slot_6 = self.equipment_data[str(i[7])]["name"] if not i[7] == 999999 else ""

                # GET UNIT KEY / NAME_EN / THEMATIC_EN / NAME_JP / THEMATIC_JP
                if str(full_unit_name).find("（") > -1:
                    # PARENTHESIS EXISTS... MEANS THERE'S PROBABLY A THEMATIC
                    parenthesis_index = full_unit_name.find("（")
                    thematic_jp = full_unit_name[parenthesis_index + 1:-1]
                    thematic_en = thematic_ja_to_eng_dictionary[thematic_jp]
                    name_jp = full_unit_name[:parenthesis_index]
                    name_en = str(character_name_ja_to_eng_dictionary[name_jp])
                    unit_key = thematic_en + '_' + name_en
                    # CAPITALIZE name_en AND thematic_en
                    name_en = name_en.capitalize()
                    if str(thematic_en).find('_') == -1:
                        thematic_en = str(thematic_en).capitalize()
                    else:
                        # SPLIT THEMATIC BY '_' AND ERASE EXISTING THEMATIC
                        split_thematic = str(thematic_en).split('_')
                        thematic_en = ""
                        # GO THROUGH ALL PARTS AND CAPITALIZE
                        for thematic_part in split_thematic:
                            thematic_en += str(thematic_part).capitalize() + " "
                        # REMOVE THE LAST (UNNECESSARY) SPACE
                        thematic_en = thematic_en[:-1]
                else:
                    # NO PARENTHESIS. JUST BASIC UNIT NAME
                    unit_key = character_name_ja_to_eng_dictionary[full_unit_name]
                    name_en = str(unit_key).capitalize()
                    name_jp = full_unit_name

                # INSERT DATA TO DICTIONARY
                if unit_key not in dictionary:
                    # UNIT KEY DOES NOT EXIST IN DICTIONARY, SETUP UNIT
                    dictionary_entry = {
                        "unit_id": unit_id,
                        "name": name_en,
                        "thematic": thematic_en,
                        "name_jp": name_jp,
                        "thematic_jp": thematic_jp
                    }
                    dictionary[unit_key] = dictionary_entry
                equip_array = [equip_slot_1, equip_slot_2, equip_slot_3, equip_slot_4, equip_slot_5, equip_slot_6]
                dictionary[unit_key]["rank_" + str(promotion_level)] = equip_array

        # SORT DICTIONARY ALPHABETICALLY
        sorted_character_names = []
        characters_with_thematics = {}
        # COLLECT CHARACTER NAMES AND BUILD LIST OF ONES THAT HAVE THEMATICS
        for key in sorted(dictionary.keys()):
            if str(key).rfind('_') == -1:
                # NO '_' MEANS NO THEMATIC
                sorted_character_names.append(key)
            else:
                # THEMATIC FOUND, ADD TO LIST AND SORT
                character_name = key[str(key).rfind('_') + 1:]
                if character_name not in characters_with_thematics:
                    characters_with_thematics[character_name] = []
                characters_with_thematics[character_name].append(key)
        sorted_dictionary = {}
        # CREATE SORTED DICTIONARY
        for key in sorted(sorted_character_names):
            sorted_dictionary[key] = dictionary[key]
            if key in characters_with_thematics:
                # CHARACTER HAS AN ALTERNATE VERSION
                # ADD ALTERNATE VERSIONS AFTER BASE VERSION
                for value in sorted(characters_with_thematics[key]):
                    sorted_dictionary[value] = dictionary[value]
        dictionary = sorted_dictionary

        # SAVE FILE
        self.save_file(dictionary, self.character_data_path)
        self.character_data = dictionary

    @staticmethod
    def get_next_key(dictionary):
        if 'item_1' not in dictionary:
            return 'item_1'
        else:
            if 'item_2' not in dictionary:
                return 'item_2'
            else:
                if 'item_3' not in dictionary:
                    return 'item_3'
                else:
                    return 'item_4'

    def get_quest_drops(self, dictionary, wave_group):
        drop_reward_counter = 1
        while drop_reward_counter <= 5:
            # GET WAVE DROPS
            wave_drops = wave_group['drop_reward_' + str(drop_reward_counter)]
            if wave_drops is not 0:
                # GET ITEMS FROM WAVE DROPS
                enemy_reward = self.enemy_reward_info[wave_drops]

                # CHECK IF WAVE GIVES SUBDROPS
                if enemy_reward['reward_id_1'] is not 0 and \
                        enemy_reward['reward_id_2'] is not 0 and \
                        enemy_reward['reward_id_3'] is not 0 and \
                        enemy_reward['reward_id_4'] is not 0 and \
                        enemy_reward['reward_id_5'] is not 0:
                    dictionary['subdrops'] = [
                        {
                            'reward_id': enemy_reward['reward_id_1'],
                            'reward_odds': enemy_reward['reward_odds_1']
                        },
                        {
                            'reward_id': enemy_reward['reward_id_2'],
                            'reward_odds': enemy_reward['reward_odds_2']
                        },
                        {
                            'reward_id': enemy_reward['reward_id_3'],
                            'reward_odds': enemy_reward['reward_odds_3']
                        },
                        {
                            'reward_id': enemy_reward['reward_id_4'],
                            'reward_odds': enemy_reward['reward_odds_4']
                        },
                        {
                            'reward_id': enemy_reward['reward_id_5'],
                            'reward_odds': enemy_reward['reward_odds_5']
                        }
                    ]
                else:
                    enemy_reward_counter = 1
                    while enemy_reward_counter <= 5:
                        reward_type = enemy_reward['reward_type_' + str(enemy_reward_counter)]
                        reward_id = enemy_reward['reward_id_' + str(enemy_reward_counter)]
                        reward_odds = enemy_reward['reward_odds_' + str(enemy_reward_counter)]
                        item = {
                            'reward_id': reward_id,
                            'reward_odds': reward_odds
                        }

                        if reward_id is not 0:
                            # IF DROP IS EQUIPMENT...
                            if reward_type is 4:
                                key = self.get_next_key(dictionary)
                                dictionary[key] = item
                            else:
                                if reward_type is 2:
                                    # CHECK IF ITEM IS A MEMORY PIECE
                                    if str(reward_id)[:1] is '3':
                                        dictionary['char_shard'] = item
                        else:
                            break

                        enemy_reward_counter += 1
            else:
                drop_reward_counter += 1
                continue

            drop_reward_counter += 1

        return dictionary

    def add_quest_entry(self, dictionary, quest):
        quest_drops = self.get_quest_drops({}, self.wave_group_info[quest['wave_group_id_1']])
        quest_drops = self.get_quest_drops(quest_drops, self.wave_group_info[quest['wave_group_id_2']])
        quest_drops = self.get_quest_drops(quest_drops, self.wave_group_info[quest['wave_group_id_3']])
        quest_key = quest['key']
        dictionary[quest_key] = {
            "name": quest['name']
        }
        counter = 1

        # ADD ITEMS 1 - 4
        while counter <= 4:
            if 'item_' + str(counter) in quest_drops:
                if ('item_' + str(counter)) in quest_drops:
                    item_id = str(quest_drops["item_" + str(counter)]["reward_id"])[2:]
                    item_name = self.equipment_data['10' + item_id]['name']
                    drop_percent = quest_drops["item_" + str(counter)]["reward_odds"]

                    # ADD ' Fragment' IF ITEM HAS FRAGMENTS
                    if self.equipment_data['10' + item_id]['has_fragments']:
                        item_name += ' Fragment'

                    # ADD TO DICTIONARY
                    item = {
                        'item_name': item_name,
                        'drop_percent': drop_percent
                    }
                    dictionary[quest_key]['item_' + str(counter)] = item

            counter += 1

        # ADD CHARACTER SHARD
        if 'char_shard' in quest_drops:
            item_id = str(quest_drops["char_shard"]["reward_id"])
            item_name = self.equipment_data[item_id]['name']
            item = {
                'item_name': item_name,
                'drop_percent': quest_drops["char_shard"]["reward_odds"]
            }
            dictionary[quest_key]['char_shard'] = item

        # ADD SUB DROPS AND PERCENT
        subdrops = []
        subdrops_percent = []
        subdrops_not_equal = False
        for item_data in quest_drops['subdrops']:
            item_id = str(item_data['reward_id'])[2:]
            item_name = self.equipment_data['10' + item_id]['name']
            drop_percent = item_data['reward_odds']

            # ADD ' Fragment' IF ITEM HAS FRAGMENTS
            if self.equipment_data['10' + item_id]['has_fragments']:
                item_name += ' Fragment'

            subdrops.append(item_name)
            subdrops_percent.append(drop_percent)
            if subdrops_percent[0] is not drop_percent:
                subdrops_not_equal = True
        dictionary[quest_key]['subdrops'] = subdrops
        if subdrops_not_equal:
            dictionary[quest_key]['subdrops_percent'] = subdrops_percent

        return dictionary

    def write_quest_data(self):
        # COLLECT quest_data INFORMATION
        quest_data = {}
        command = "SELECT quest_id, quest_name, "
        command += "wave_group_id_1, wave_group_id_2, wave_group_id_3 "
        command += "FROM quest_data"
        answer = self.get_sql_answer(command)
        for i in answer:
            quest_id = i[0]
            quest_type = str(quest_id)[:2]
            if int(quest_type) is not 18 and int(quest_type) is not 19:
                quest_full_name = str(i[1])
                quest_chapter = quest_full_name[quest_full_name.rfind(' ') + 1:quest_full_name.rfind('-')]
                quest_number = quest_full_name[quest_full_name.rfind('-') + 1:]
                quest_difficulty = None
                if int(quest_type) is 11:               # NORMAL
                    quest_type = ""
                    quest_difficulty = 'NORMAL'
                else:
                    if int(quest_type) is 12:           # HARD
                        quest_type = "H"
                        quest_difficulty = 'HARD'
                    else:
                        if int(quest_type) is 13:       # VERY HARD
                            quest_type = "VH"
                            quest_difficulty = 'VERY HARD'

                quest_data[str(quest_id)] = {
                    "id": quest_id,
                    "name": quest_full_name,
                    "key": quest_chapter + '-' + quest_number + quest_type,
                    "difficulty": quest_difficulty,
                    "wave_group_id_1": i[2],
                    "wave_group_id_2": i[3],
                    "wave_group_id_3": i[4],
                }

        # COLLECT wave_group_data INFORMATION
        wave_group_data = {}
        command = "SELECT wave_group_id, drop_reward_id_1, drop_reward_id_2, "
        command += "drop_reward_id_3, drop_reward_id_4, drop_reward_id_5 "
        command += "FROM wave_group_data"
        answer = self.get_sql_answer(command)
        for i in answer:
            wave_group_data[i[0]] = {
                "wave_group_id": i[0],
                "drop_reward_1": i[1],
                "drop_reward_2": i[2],
                "drop_reward_3": i[3],
                "drop_reward_4": i[4],
                "drop_reward_5": i[5],
            }
        self.wave_group_info = wave_group_data

        # COLLECT enemy_reward_data INFORMATION
        enemy_reward_data = {}
        command = "SELECT drop_reward_id, "
        command += "reward_type_1, reward_id_1, odds_1, "
        command += "reward_type_2, reward_id_2, odds_2, "
        command += "reward_type_3, reward_id_3, odds_3, "
        command += "reward_type_4, reward_id_4, odds_4, "
        command += "reward_type_5, reward_id_5, odds_5 "
        command += "FROM enemy_reward_data"
        answer = self.get_sql_answer(command)
        for i in answer:
            enemy_reward_data[i[0]] = {
                "drop_reward_id": i[0],

                "reward_type_1": i[1],
                "reward_id_1": i[2],
                "reward_odds_1": i[3],

                "reward_type_2": i[4],
                "reward_id_2": i[5],
                "reward_odds_2": i[6],

                "reward_type_3": i[7],
                "reward_id_3": i[8],
                "reward_odds_3": i[9],

                "reward_type_4": i[10],
                "reward_id_4": i[11],
                "reward_odds_4": i[12],

                "reward_type_5": i[13],
                "reward_id_5": i[14],
                "reward_odds_5": i[15],
            }
        self.enemy_reward_info = enemy_reward_data

        # BUILD QUEST DATA JSON
        dictionary = {}
        for key in quest_data:
            quest = quest_data[key]

            # CHECK IF QUEST HAS ALL WAVE DATA
            if quest['wave_group_id_1'] is not 0 and \
                    quest['wave_group_id_2'] is not 0 and \
                    quest['wave_group_id_3'] is not 0:

                # GET QUEST DROPS
                if quest['difficulty'] is 'NORMAL':
                    dictionary = self.add_quest_entry(dictionary, quest)

                    # CHECK IF ANY MORE NORMAL QUESTS
                    quest_id = str(quest["id"])
                    quest_number = quest_id[-3:]
                    quest_chapter = quest_id[-6:-3]
                    next_quest_number = str(int(quest_number) + 1).zfill(3)
                    next_quest_id = '11' + quest_chapter + next_quest_number
                    if next_quest_id not in quest_data:
                        # ADD HARD QUESTS
                        hard_quest_counter = 1
                        hard_quest_id = '12' + quest_chapter + str(hard_quest_counter).zfill(3)
                        while hard_quest_id in quest_data:
                            quest = quest_data[hard_quest_id]
                            if quest['wave_group_id_1'] is not 0 and \
                                    quest['wave_group_id_2'] is not 0 and \
                                    quest['wave_group_id_3'] is not 0:
                                dictionary = self.add_quest_entry(dictionary, quest)

                            hard_quest_counter += 1
                            hard_quest_id = '12' + quest_chapter + str(hard_quest_counter).zfill(3)

                        # ADD VERY HARD QUESTS
                        hard_quest_counter = 1
                        hard_quest_id = '13' + quest_chapter + str(hard_quest_counter).zfill(3)
                        while hard_quest_id in quest_data:
                            quest = quest_data[hard_quest_id]
                            if quest['wave_group_id_1'] is not 0 or \
                                    quest['wave_group_id_2'] is not 0 or \
                                    quest['wave_group_id_3'] is not 0:
                                dictionary = self.add_quest_entry(dictionary, quest)

                            hard_quest_counter += 1
                            hard_quest_id = '13' + quest_chapter + str(hard_quest_counter).zfill(3)

        # SAVE FILE
        self.save_file(dictionary, self.quest_data_path)
        self.quest_data = dictionary
