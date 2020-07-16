"""
HOW TO USE:
`python fix-equipment-data.py <equipment_data.json_path>`
"""


import sys, json


def fix_equipment_data(equipment_data_path):
    with open(equipment_data_path, encoding='utf-8') as equipment_json:
        equipment_data = json.load(equipment_json)
        fixed = {}

        # FIND ALL misc RARITY ITEMS
        for equip_key in equipment_data:
            equip_rarity = equipment_data[equip_key]["id"]
            if "misc" in equip_rarity:
                fixed[equip_key] = equipment_data[equip_key]

        # DELETE AND RE-ADD ALL misc RARITY ITEMS
        for fixed_key in fixed:
            del equipment_data[fixed_key]
            equipment_data[fixed_key] = fixed[fixed_key]

        # DONE
        print('FIXED', equipment_data_path)

    # OVERWRITE EQUIPMENT DATA FILE WITH FIXED DATA
    with open(equipment_data_path, 'w', encoding='utf-8') as f:
        json.dump(equipment_data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Not enough arguments.')
        sys.exit()
    fix_equipment_data(sys.argv[1])
